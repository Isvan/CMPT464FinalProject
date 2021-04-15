# Root code tutorial that im using
# https://www.tensorflow.org/tutorials/images/classification

import matplotlib.pyplot as plt
import numpy as np
import os
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.models import Sequential
import NNModels
import chairs_dataset

from config import *


def setTrainingData(data):
    return tf.keras.preprocessing.image_dataset_from_directory(
        data,
        validation_split=0.2,
        subset="training",
        # color_mode="grayscale",
        seed=seed,
        image_size=(img_height, img_width),
        batch_size=batch_size)


def setValidationData(data):
    return tf.keras.preprocessing.image_dataset_from_directory(
        data,
        validation_split=0.2,
        # color_mode="grayscale",
        subset="validation",
        seed=seed,
        image_size=(img_height, img_width),
        batch_size=batch_size)


def getTrainingDataTuples():

    dirname = os.path.dirname(__file__)
    dataTop = os.path.join(dirname, "..", "..", "dataset", "imageData", "chairs-data",
                           "ourChairData", "chairs-Top")
    dataSide = os.path.join(dirname, "..", "..", "dataset", "imageData", "chairs-data",
                            "ourChairData", "chairs-Side")
    dataFront = os.path.join(dirname, "..", "..", "dataset", "imageData", "chairs-data",
                             "ourChairData", "chairs-Front")

    seed = 1337

    # TOP VIEWS
    train_ds_top = setTrainingData(dataTop)
    val_ds_top = setValidationData(dataTop)

    # SIDE VIEWS
    train_ds_side = setTrainingData(dataSide)
    val_ds_side = setValidationData(dataSide)

    # FRONT VIEWS
    train_ds_front = setTrainingData(dataFront)
    val_ds_front = setValidationData(dataFront)

    return [(train_ds_top, val_ds_top), (train_ds_side, val_ds_side), (train_ds_front, val_ds_front)]


def printGraphOfResults(history, title):
    acc = history.history['accuracy']
    val_acc = history.history['val_accuracy']

    loss = history.history['loss']
    val_loss = history.history['val_loss']

    epochs_range = range(training_epochs)

    plt.figure(figsize=(8, 8))
    plt.subplot(1, 2, 1)
    plt.plot(epochs_range, acc, label='Training Accuracy')
    plt.plot(epochs_range, val_acc, label='Validation Accuracy')
    plt.legend(loc='lower right')
    plt.title('Training and Validation Accuracy')

    plt.subplot(1, 2, 2)
    plt.plot(epochs_range, loss, label='Training Loss')
    plt.plot(epochs_range, val_loss, label='Validation Loss')
    plt.legend(loc='upper right')
    plt.title('Training and Validation Loss For ' + title)
    plt.savefig(graphResultsFolder+title + "-trainingResult" +
                str(training_epochs)+"-"+str(batch_size)+".png")
    plt.close()


def runTripleSingleNN():
    # Need for identifcation later on
    models = [NNModels.getSingleViewModelSingleDim(), NNModels.getSingleViewModelSingleDim(),
              NNModels.getSingleViewModelSingleDim()]
    # trainingData = getTrainingDataTuples()
    # print(trainingData)
    index = 0

    if not os.path.exists(graphResultsFolder):
        os.makedirs(graphResultsFolder)

    imagesTop, imagesFront, imagesSide, topLabel, frontLabel, sideLabel = chairs_dataset.load(
        img_height)

    # ["Top", "Side", "Front"]

    trainingData = [(imagesTop, topLabel), (imagesSide,
                                            sideLabel), (imagesFront, frontLabel)]

    for data, label in trainingData:

        model_checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
            filepath=checkpointFilepath +
            dataTitlesTripleView[index]+"/checkpoint",
            save_weights_only=True,
            # monitor='val_accuracy',
            # mode='auto',
            save_best_only=False)

        print("Starting to Train View " + dataTitlesTripleView[index])
        history = models[index].fit(
            x=data,
            y=label,
            validation_split=0.2,
            epochs=training_epochs,
            batch_size=batch_size,
            callbacks=[model_checkpoint_callback]
        )

        print("Done training View " + dataTitlesTripleView[index])
        printGraphOfResults(history, dataTitlesTripleView[index])

        index += 1


def runSingleTripleBranchNN():
    # Need for identifcation later on
    model = NNModels.getMultiViewModel()

    checkPoint = tf.train.latest_checkpoint(
        checkpointFilepath + "tripleView"+"")
    if(checkPoint):
        model.load_weights(checkPoint)

    print("CheckPoints")
    print(checkPoint)

    if not os.path.exists(graphResultsFolder):
        os.makedirs(graphResultsFolder)

    imagesTop, imagesFront, imagesSide, topLabel, frontLabel, sideLabel = chairs_dataset.load(
        img_height)

    model_checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
        filepath=checkpointFilepath +
        "tripleView"+"/checkpoint",
        save_weights_only=True,
        # monitor='val_accuracy',
        # mode='auto',
        save_best_only=True)

    print("Starting to Train Triple View")
    history = model.fit(
        x=[imagesTop, imagesSide, imagesFront],
        y=topLabel,
        validation_split=0.2,
        epochs=training_epochs,
        batch_size=batch_size,
        callbacks=[model_checkpoint_callback]
    )

    print("Done training Triple View ")
    printGraphOfResults(history, "Triple View")


def main(*argv):
    runSingleTripleBranchNN()


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
