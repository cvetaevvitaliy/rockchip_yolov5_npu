# RK3588 NPU SRAM Instructions

* The RK3588 SOC contains 1MB of SRAM, of which 956KB can be used by each IP on the SOC, which supports the designated allocation for RKNPU
* SRAM can help RKNPU applications reduce DDR bandwidth pressure. Currently, it supports the allocation of SRAM for Internal and Weight memory types.


---
Board environmental requirements
---
### 1. Kernel environment requirements
* RKNPU driver version >=0.8.0
* Kernel config needs to enable CONFIG_ROCKCHIP_RKNPU_SRAM=y
    * The Android system config path is as follows:
    ```shell
    <path-to-your-kernel>/arch/arm64/configs/rockchip_defconfig
    ```
    * The Linux system config path is as follows:
    ```
    <path-to-your-kernel>/arch/arm64/configs/rockchip_linux_defconfig
    ```
* The corresponding DTS of the kernel needs to be allocated to RKNPU from the system SRAM
    * Allocate the required size of SRAM from the system to RKNPU, the maximum can be allocated 956KB, and the size needs to be 4K aligned
    * Note: In the default system, SRAM may have been allocated for other IPs, such as the codec module. The SRAM areas allocated by each IP cannot overlap, otherwise there will be data confusion during simultaneous reading and writing.
    * The following is an example of allocating 956KB to RKNPU:
    ```dts
    syssram: sram@ff001000 {
        compatible = "mmio-sram";
        reg = <0x0 0xff001000 0x0 0xef000>;

        #address-cells = <1>;
        #size-cells = <1>;
        ranges = <0x0 0x0 0xff001000 0xef000>;
        /* 分配RKNPU SRAM */
        /* start address and size should be 4k algin */
        rknpu_sram: rknpu_sram@0 {
            reg = <0x0 0xef000>; // 956KB
        };
    };
    ```
    * Hang the allocated SRAM to the RKNPU node, and modify the dtsi file as shown below:
    ```shell
    <path-to-your-kernel>/arch/arm64/boot/dts/rockchip/rk3588s.dtsi
    ```
    ```dts
    rknpu: npu@fdab0000 {
        compatible = "rockchip,rk3588-rknpu";
        /* ... */
        /* RKNPU sram*/
        rockchip,sram = <&rknpu_sram>;
        status = "disabled";
    };
    ```

2. RKNN SDK version requirements
* RKNPU Runtime library (librknnrt.so) version >=1.3.4b14

---
### 2 How to use
---
1、指定Internal使用SRAM:
* 自动大小方式，将尝试从系统分配剩余足够的SRAM给Internal使用
    * **export RKNN_INTERNAL_MEM_TYPE=sram**
* 指定大小方式，将尝试从系统分配指定256KB大小的SRAM给Internal使用
    * **export RKNN_INTERNAL_MEM_TYPE=sram#256**

2、指定Weight使用SRAM：
* 自动大小方式，将尝试从系统分配剩余足够的SRAM给Weight使用
    * **export RKNN_SEPARATE_WEIGHT_MEM=1**
    * **export RKNN_WEIGHT_MEM_TYPE=sram**
* 指定大小方式，将尝试从系统分配指定128KB大小的SRAM给Weight使用
     * **export RKNN_SEPARATE_WEIGHT_MEM=1**
    * **export RKNN_WEIGHT_MEM_TYPE=sram#128**

3、混合指定
* RKNPU驱动支持对SRAM内存管理，支持同时指定SRAM给Internal和Weight同时使用，如下：
    * **export RKNN_INTERNAL_MEM_TYPE=sram#256**
    * **export RKNN_SEPARATE_WEIGHT_MEM=1**
    * **export RKNN_WEIGHT_MEM_TYPE=sram#128**

---
三、调试方法
---
1、SRAM是否启用查询
* 通过开机串口日志查看SRAM是否启用，包含为RKNPU指定SRAM的地址范围和大小信息，如下所示：
```shell
rk3588_s:/ # dmesg | grep rknpu -i
RKNPU fdab0000.npu: RKNPU: sram region: [0x00000000ff001000, 0x00000000ff0f0000), sram size: 0xef000
```

2、SRAM使用情况查询
* 可通过节点查询SRAM的使用情况
* 如下为未使用SRAM的位图表，每个点表示4K大小
```shell
rk3588_s:/ # cat /sys/kernel/debug/rknpu/mm
SRAM bitmap: "*" - used, "." - free (1bit = 4KB)
[000] [................................]
[001] [................................]
[002] [................................]
[003] [................................]
[004] [................................]
[005] [................................]
[006] [................................]
[007] [...............]
SRAM total size: 978944, used: 0, free: 978944
```
* 如下为分配使用512KB后的SRAM位图表
```shell
rk3588_s:/ # cat /sys/kernel/debug/rknpu/mm
SRAM bitmap: "*" - used, "." - free (1bit = 4KB)
[000] [********************************]
[001] [********************************]
[002] [********************************]
[003] [********************************]
[004] [................................]
[005] [................................]
[006] [................................]
[007] [...............]
SRAM total size: 978944, used: 524288, free: 454656
```

3、通过RKNN API查询SRAM大小
* 通过rknn_query的RKNN_QUERY_MEM_SIZE接口查询SRAM大小信息
```C++
typedef struct _rknn_mem_size {
    uint32_t total_weight_size;
    uint32_t total_internal_size;
    uint64_t total_dma_allocated_size;
    uint32_t total_sram_size;
    uint32_t free_sram_size;
    uint32_t reserved[10];
} rknn_mem_size;
```
* 其中，total_sram_size表示：系统给RKNPU分配的SRAM总大小
* free_sram_size表示：剩余RKNPU能使用的SRAM大小

4、查看网络SRAM的占用情况
* 板端环境中，RKNN应用运行前设置如下环境变量，可打印SRAM使用预测情况：
```shell
export RKNN_LOG_LEVEL=3
```
* Internal分配SRAM的逐层占用情况，如下日志所示：
```shell
---------------------------------------------------------------------------
Total allocated Internal SRAM Size: 524288, Addr: [0xff3e0000, 0xff460000)
---------------------------------------------------------------------------
---------------------------------------------------------------------+----------------------------------+-----------
ID  User           Tensor   DataType OrigShape      NativeShape      |     [Start       End)       Size |    SramHit
---------------------------------------------------------------------+----------------------------------+-----------
1   ConvRelu       input0   INT8     (1,3,224,224)  (1,1,224,224,3)  | 0xff3b0000 0xff3d4c00 0x00024c00 | \
2   ConvRelu       output2  INT8     (1,32,112,112) (1,2,112,112,16) | 0xff404c00 0xff466c00 0x00062000 | 0x0005b400
3   ConvRelu       output4  INT8     (1,32,112,112) (1,4,112,112,16) | 0xff466c00 0xff52ac00 0x000c4000 | 0x00000000
4   ConvRelu       output6  INT8     (1,64,112,112) (1,4,112,112,16) | 0xff52ac00*0xff5eec00 0x000c4000 | 0x00000000
5   ConvRelu       output8  INT8     (1,64,56,56)   (1,4,56,56,16)   | 0xff3e0000 0xff411000 0x00031000 | 0x00031000
6   ConvRelu       output10 INT8     (1,128,56,56)  (1,8,56,56,16)   | 0xff411000 0xff473000 0x00062000 | 0x0004f000
7   ConvRelu       output12 INT8     (1,128,56,56)  (1,8,56,56,16)   | 0xff473000 0xff4d5000 0x00062000 | 0x00000000
8   ConvRelu       output14 INT8     (1,128,56,56)  (1,8,56,56,16)   | 0xff3e0000 0xff442000 0x00062000 | 0x00062000
9   ConvRelu       output16 INT8     (1,128,28,28)  (1,8,28,28,16)   | 0xff442000 0xff45a800 0x00018800 | 0x00018800
10  ConvRelu       output18 INT8     (1,256,28,28)  (1,16,28,28,16)  | 0xff3e0000 0xff411000 0x00031000 | 0x00031000
11  ConvRelu       output20 INT8     (1,256,28,28)  (1,16,28,28,16)  | 0xff411000 0xff442000 0x00031000 | 0x00031000
12  ConvRelu       output22 INT8     (1,256,28,28)  (1,16,28,28,16)  | 0xff3e0000 0xff411000 0x00031000 | 0x00031000
13  ConvRelu       output24 INT8     (1,256,14,14)  (1,16,14,14,16)  | 0xff411000 0xff41d400 0x0000c400 | 0x0000c400
14  ConvRelu       output26 INT8     (1,512,14,14)  (1,32,14,14,16)  | 0xff3e0000 0xff3f8800 0x00018800 | 0x00018800
15  ConvRelu       output28 INT8     (1,512,14,14)  (1,32,14,14,16)  | 0xff3f8800 0xff411000 0x00018800 | 0x00018800
16  ConvRelu       output30 INT8     (1,512,14,14)  (1,32,14,14,16)  | 0xff3e0000 0xff3f8800 0x00018800 | 0x00018800
17  ConvRelu       output32 INT8     (1,512,14,14)  (1,32,14,14,16)  | 0xff3f8800 0xff411000 0x00018800 | 0x00018800
18  ConvRelu       output34 INT8     (1,512,14,14)  (1,32,14,14,16)  | 0xff3e0000 0xff3f8800 0x00018800 | 0x00018800
19  ConvRelu       output36 INT8     (1,512,14,14)  (1,32,14,14,16)  | 0xff3f8800 0xff411000 0x00018800 | 0x00018800
20  ConvRelu       output38 INT8     (1,512,14,14)  (1,32,14,14,16)  | 0xff3e0000 0xff3f8800 0x00018800 | 0x00018800
21  ConvRelu       output40 INT8     (1,512,14,14)  (1,32,14,14,16)  | 0xff3f8800 0xff411000 0x00018800 | 0x00018800
22  ConvRelu       output42 INT8     (1,512,14,14)  (1,32,14,14,16)  | 0xff3e0000 0xff3f8800 0x00018800 | 0x00018800
23  ConvRelu       output44 INT8     (1,512,14,14)  (1,32,14,14,16)  | 0xff3f8800 0xff411000 0x00018800 | 0x00018800
24  ConvRelu       output46 INT8     (1,512,14,14)  (1,32,14,14,16)  | 0xff3e0000 0xff3f8800 0x00018800 | 0x00018800
25  ConvRelu       output48 INT8     (1,512,7,7)    (1,33,7,7,16)    | 0xff3f8800 0xff3ff000 0x00006800 | 0x00006800
26  ConvRelu       output50 INT8     (1,1024,7,7)   (1,67,7,7,16)    | 0xff3e0000 0xff3ed000 0x0000d000 | 0x0000d000
27  ConvRelu       output52 INT8     (1,1024,7,7)   (1,67,7,7,16)    | 0xff3ed000 0xff3fa000 0x0000d000 | 0x0000d000
28  AveragePool    output54 INT8     (1,1024,7,7)   (1,67,7,7,16)    | 0xff3e0000 0xff3ed000 0x0000d000 | 0x0000d000
29  Conv           output55 INT8     (1,1024,1,1)   (1,64,1,1,16)    | 0xff3ed000 0xff3ed400 0x00000400 | 0x00000400
30  Softmax        output56 INT8     (1,1000,1,1)   (1,64,1,1,16)    | 0xff3e0000 0xff3e0400 0x00000400 | 0x00000400
31  OutputOperator output57 FLOAT    (1,1000,1,1)   (1,1000,1,1)     | 0xff3ae000 0xff3aefa0 0x00000fa0 | \
---------------------------------------------------------------------+----------------------------------+-----------
----------------------------------------
Total Weight Memory Size: 4260864
Total Internal Memory Size: 2157568
Predict Internal Memory RW Amount: 11068320
Predict Weight Memory RW Amount: 4260832
Predict SRAM Hit RW Amount: 6688768
----------------------------------------
```
* 其中上面文本图表中的SramHit为当前层Tensor所占用的SRAM大小，一般情况下将会节省当前大小的读+写的带宽
* Predict SRAM Hit RW Amount表示整个网络SRAM的读写预测情况，可近似估计每帧节省的带宽
* 注意：Linux环境日志重定向到终端，Android环境日志重定向到logcat