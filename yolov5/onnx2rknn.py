import argparse
import cv2
import numpy as np

from rknn.api import RKNN
import os

def convert(srcFileName, dstFilename):

    # Define Rockchip CPU:
    # NPU Type 1: RK1808, RV1109, RV1126, RK3399PRO
    # NPU type 2: RK3566, RK3568, RK3588, RK3588S
    platform = "rk3588"
    
    print('--> Source file name: ' + srcFileName)
    print('--> RKNN file name: ' + dstFilename)

    # Create RKNN object
    rknn = RKNN()

    # Define dataset for quantization model 
    DATASET = 'data/images/dataset.txt'

    # Config: see documentation Rockchip_Quick_Start_RKNN_SDK 
    rknn.config(mean_values=[[0, 0, 0]], std_values=[[255, 255, 255]], target_platform=platform)

    # Load model
    print('--> Loading model')
    ret = rknn.load_onnx(srcFileName)
    if ret != 0:
        print('load model failed!')
        exit(ret)
    print('done')

    # Build model
    print('--> Building model')
    ret = rknn.build(do_quantization=True, dataset=DATASET)
    if ret != 0:
        print('build model failed.')
        exit(ret)
    print('done')

    # Export model to rknn format for Rockchip NPU
    print('--> Export rknn model')
    ret = rknn.export_rknn(dstFilename)
    if ret != 0:
        print('Export rknn model failed!')
        return ret

    print('export done')

    rknn.release()
 
def main():

    parser = argparse.ArgumentParser(description='transform to rknn model')
    parser.add_argument('source_file')
    parser.add_argument('description_file')
    args = parser.parse_args()

    convert(args.source_file, args.description_file)

if __name__ == '__main__':
    main()    

