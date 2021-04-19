# Root code tutorial that im using
# https://www.tensorflow.org/tutorials/images/classification

import matplotlib.pyplot as plt
import numpy as np
import os
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.models import Sequential

import ML.ourML.NNModels as nnModels
import ML.ourML.chairs_dataset as chairsDataset
from MLStatics import *


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
    models = [nnModels.getSingleViewModelSingleDim(), nnModels.getSingleViewModelSingleDim(),
              nnModels.getSingleViewModelSingleDim()]
    # trainingData = getTrainingDataTuples()
    # print(trainingData)
    index = 0

    if not os.path.exists(graphResultsFolder):
        os.makedirs(graphResultsFolder)

    imagesTop, imagesFront, imagesSide, topLabel, frontLabel, sideLabel = chairsDataset.load(
        img_height)

    # ["Top", "Side", "Front"]

    trainingData = [(imagesTop, topLabel), (imagesSide,
                                            sideLabel), (imagesFront, frontLabel)]

    for data, label in trainingData:

        model_checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
            filepath=os.path.join(checkpointFilepath +
                                  dataTitlesTripleView[index], "checkpoint", ""),
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
    model = nnModels.getMultiViewModel()

    checkPoint = tf.train.latest_checkpoint(os.path.join(
        checkpointFilepath, "tripleView"))
    if(checkPoint):
        model.load_weights(checkPoint)

    if not os.path.exists(graphResultsFolder):
        os.makedirs(graphResultsFolder)

    imagesTop, imagesFront, imagesSide, topLabel, frontLabel, sideLabel = chairsDataset.load(
        img_height)

    model_checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
        filepath=os.path.join(
            checkpointFilepath, "tripleView", "checkpoint"),
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
