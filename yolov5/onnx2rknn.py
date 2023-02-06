import argparse
import cv2
import numpy as np

from rknn.api import RKNN
import os

def convert(srcFileName, dstFilename):

    platform = 'rk3588'
    OUT_DIR = "rknn_models"
    MODEL_PATH = srcFileName
    RKNN_MODEL_PATH = OUT_DIR + "/{}".format(dstFilename)
    
    NEED_BUILD_MODEL = True
    # NEED_BUILD_MODEL = False
    im_file = './dog_bike_car_640x640.jpg'
    
    print('--> Source file name: ' + MODEL_PATH)
    print('--> RKNN file name: ' + RKNN_MODEL_PATH)

    # Create RKNN object
    rknn = RKNN()

    if NEED_BUILD_MODEL:
        DATASET = 'data/images/dataset.txt'
        rknn.config(mean_values=[[0, 0, 0]], std_values=[[255, 255, 255]], target_platform="rk3588")
        # Load model
        print('--> Loading model')
        ret = rknn.load_onnx(MODEL_PATH)
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

        # # Export rknn model
        # if not os.path.exists(OUT_DIR):
        #     os.mkdir(OUT_DIR)
        # print('--> Export RKNN model: {}'.format(RKNN_MODEL_PATH))
        # ret = rknn.export_rknn(RKNN_MODEL_PATH)
        # if ret != 0:
        #     print('Export rknn model failed.')
        #     exit(ret)
        # print('done')
        print('--> Export rknn model')
        ret = rknn.export_rknn(dstFilename)
        if ret != 0:
            print('Export rknn model failed!')
            return ret

        print('export done')
    else:
        ret = rknn.load_rknn(RKNN_MODEL_PATH)

    rknn.release()
 
def main():

    parser = argparse.ArgumentParser(description='transform to rknn model')
    parser.add_argument('source_file')
    parser.add_argument('description_file')
    args = parser.parse_args()

    convert(args.source_file, args.description_file)

if __name__ == '__main__':
    main()    

