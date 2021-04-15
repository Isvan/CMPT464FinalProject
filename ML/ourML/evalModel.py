
import numpy as np
import os
import cv2
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.models import Sequential

from config import *
import NNModels

# Taken directly from sample code


def getEvalData():

    dirname = os.path.dirname(__file__)
    dataTop = os.path.join(dirname, "..", "..", "dataset", "imageData", "chairs-data",
                           "ourChairData", "chairs-Top-Eval")
    dataSide = os.path.join(dirname, "..", "..", "dataset", "imageData", "chairs-data",
                            "ourChairData", "chairs-Side-Eval")
    dataFront = os.path.join(dirname, "..", "..", "dataset", "imageData", "chairs-data",
                             "ourChairData", "chairs-Front-Eval")

    print(dataTop)
    print(dataSide)
    print(dataFront)

    # TOP VIEWS
    train_ds_top = tf.keras.preprocessing.image_dataset_from_directory(
        dataTop,
        image_size=(img_height, img_width),
        batch_size=batch_size,
        shuffle=False,
        label_mode=None)

    # SIDE VIEWS
    train_ds_side = tf.keras.preprocessing.image_dataset_from_directory(
        dataSide,
        image_size=(img_height, img_width),
        batch_size=batch_size,
        shuffle=False,
        label_mode=None)
    # FRONT VIEWS

    train_ds_front = tf.keras.preprocessing.image_dataset_from_directory(
        dataFront,
        image_size=(img_height, img_width),
        batch_size=batch_size,
        shuffle=False,
        label_mode=None)

    return train_ds_top, train_ds_front, train_ds_side


def load(dimension):

    imagesTop = []
    imagesSide = []
    imagesFront = []
    ls = 0
    folder = "../../dataset/imageData/evaluate-chairs/"

    length = len(os.listdir(folder)) // 3
    ls += length

    for filename in os.listdir(folder):

        view = int(filename.split(".")[0])
        view = view % 3

        img = cv2.imread(folder+filename)
        if dimension < 224:
            img = cv2.resize(img, dsize=(dimension, dimension),
                             interpolation=cv2.INTER_CUBIC)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = np.nan_to_num(img)

        # This relies on the files being loaded in order. For that to happen, the 0 padding in the file name is crucial.
        # If you do not have that, then you need to change the logic of this loop.

        if img is not None:
            if view == 2:
                imagesSide.append(1. - img / 255.)
            elif view == 0:
                imagesTop.append(1. - img / 255.)
            else:
                imagesFront.append(1. - img / 255.)

    imagesTop = np.array(imagesTop)
    imagesFront = np.array(imagesFront)
    imagesSide = np.array(imagesSide)

    # flatten the images
    #imagesTop = np.reshape(imagesTop, (ls, dimension * dimension))
    #imagesFront = np.reshape(imagesFront, (ls, dimension * dimension))
    #imagesSide = np.reshape(imagesSide, (ls, dimension * dimension))

    return imagesTop, imagesFront, imagesSide


def evalTripleSingleView():
    # Create the models

    imagesTop, imagesFront, imagesSide = load(img_height)

    #imagesTop, imagesFront, imagesSide = getEvalData()

    testInputLayer = NNModels.getMultiViewModel()

    evalData = {}
    evalData["Top"] = imagesTop
    evalData["Front"] = imagesFront
    evalData["Side"] = imagesSide

    class_names = ["Positive", "Negative"]

    # Fill the models with the trained weights from the checkpoints
    # This is a temp thing as you would need to download weights and put them into a checkpoints folder/ run the trainer
    for view in dataTitlesTripleView:
        model = NNModels.getSingleViewModelSingleDim()
        model.load_weights(checkpointFilepath +
                           view+"/checkpoint")

        predictions = model.predict(evalData[view])
        print("View : " + view)
        index = 0
        for pred in predictions:
            score = tf.nn.softmax(pred)
            print(
                "{} : {} with a {:.2f} percent confidence."
                .format(index, class_names[np.argmax(score)], 100 * np.max(score))
            )
            index += 1


def evalTripleMultieView():
    # Create the models

    imagesTop, imagesFront, imagesSide = load(img_height)

    class_names = ["Positive", "Negative"]

    # Fill the models with the trained weights from the checkpoints
    # This is a temp thing as you would need to download weights and put them into a checkpoints folder/ run the trainer

    model = NNModels.getMultiViewModel()
    model.load_weights(checkpointFilepath +
                       "tripleView"+"/checkpoint")

    predictions = model.predict([imagesTop, imagesSide, imagesFront])
    index = 0
    for pred in predictions:
        print("{:.2f} : {:.2f} ".format(pred[0], pred[1]))
        score = tf.nn.softmax(pred)
        print(
            "{} : {} with a {:.2f} percent confidence."
            .format(index, class_names[np.argmax(score)], 100 * np.max(score))
        )
        index += 1


def main(*argv):
    evalTripleMultieView()


if __name__ == "__main__":
    # Fix for GPU memory issue with TensorFlow 2.0 +
    # https://stackoverflow.com/questions/41117740/tensorflow-crashes-with-cublas-status-alloc-failed
    gpus = tf.config.experimental.list_physical_devices('GPU')
    if gpus:
        try:
            # Currently, memory growth needs to be the same across GPUs
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
            logical_gpus = tf.config.experimental.list_logical_devices('GPU')
            print(len(gpus), "Physical GPUs,", len(
                logical_gpus), "Logical GPUs")
        except RuntimeError as e:
            # Memory growth must be set before GPUs have been initialized
            print(e)
    main()
