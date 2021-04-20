import ML.ourML.NNModels as nnModels
import numpy as np
import tensorflow as tf
import cv2
from MLStatics import *
import random


class Scorer:
    def __init__(self):

        # Fix for GPU memory issue with TensorFlow 2.0 +
        # https://stackoverflow.com/questions/41117740/tensorflow-crashes-with-cublas-status-alloc-failed
        gpus = tf.config.experimental.list_physical_devices('GPU')
        if gpus:
            try:
                # Currently, memory growth needs to be the same across GPUs
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
                logical_gpus = tf.config.experimental.list_logical_devices(
                    'GPU')
                print(len(gpus), "Physical GPUs,", len(
                    logical_gpus), "Logical GPUs")
            except RuntimeError as e:
                # Memory growth must be set before GPUs have been initialized
                print(e)

        self.model = nnModels.getMultiViewModel()

        self.model.load_weights(checkpointFilepath +
                                "tripleView"+"/checkpoint")

    def score(self, depthPerspectives):
        # Technically we should batch compute but that makes it a much bigger pain to debug and the speed loss is minumal

        front = cv2.resize(depthPerspectives[0], dsize=(img_width, img_height),
                           interpolation=cv2.INTER_CUBIC)

        side = cv2.resize(depthPerspectives[1], dsize=(img_width, img_height),
                          interpolation=cv2.INTER_CUBIC)

        top = cv2.resize(depthPerspectives[2], dsize=(img_width, img_height),
                         interpolation=cv2.INTER_CUBIC)

        front = np.resize(front, (1, 80, 80, 1))
        front = front.astype(np.float32)
        front = 1. - front / 255.

        side = np.resize(side, (1, 80, 80, 1))
        side = side.astype(np.float32)
        side = 1. - side / 255.

        top = np.resize(top, (1, 80, 80, 1))
        top = top.astype(np.float32)
        top = 1. - top / 255.

        predictions = self.model.predict(
            [front, side, top])
        return predictions[0][1] - predictions[0][0]
