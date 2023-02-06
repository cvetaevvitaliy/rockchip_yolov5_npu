# rockchip_yolov5_npu repository


Based on the code modification of https://github.com/ultralytics/yolov5 , the deployment optimization of rknpu equipment is configured

Modify the activation function silu to relu

For training related content, please refer to [README.md](https://github.com/cvetaevvitaliy/rockchip_yolov5_npu/blob/master/yolov5/README.md) instructions

Example notebook for traning model and convert to `rknn` format for Rockchip NPU, please refer to [train-rockchip.ipynb](https://github.com/cvetaevvitaliy/rockchip_yolov5_npu/blob/master/yolov5/train-rockchip.ipynb)

When exporting the model, `python export.py --rknpu {rk_platform}` can export the optimized model

(rk_platform supports rk1808, rv1109, rv1126, rk3399pro, rk3566, rk3568, rk3588, rv1103, rv1106)

example train and convert:

```bash
cd yolov5
# Train weights
python train.py --data coco128.yaml --weights yolov5s.pt --batch -1 --epochs 3

# Export to ONNX and modify the activation function silu to relu
python export.py --rknpu rk3588 --weights runs/train/exp/weights/best.pt

# Export to RKNN format
python onnx2rknn.py runs/train/exp/weights/best.onnx runs/train/exp/weights/best.rknn
```
