# Root code tutorial that im using
# https://www.tensorflow.org/tutorials/images/classification

import matplotlib.pyplot as plt
import numpy as np
import os
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.models import Sequential

# Global controls
batch_size = 200
img_height = 56
img_width = 56
training_epochs = 20
# For now hardset seed, but in the future just set to some random number or current time
seed = 100


def createModel():
    num_classes = 2
    data_augmentation = keras.Sequential(
        [
            tf.keras.layers.experimental.preprocessing.RandomTranslation(
                0.1, 0.1),
            layers.experimental.preprocessing.RandomRotation(0.2),
            layers.experimental.preprocessing.RandomZoom(0.1)
        ]
    )

    model = Sequential([
        layers.experimental.preprocessing.Rescaling(
            1./255, input_shape=(img_height, img_width, 3)),

        layers.Conv2D(32, 5, padding='same', activation='relu'),
        layers.MaxPooling2D(),
        layers.Conv2D(64, 5, padding='same', activation='relu'),
        layers.MaxPooling2D(),
        layers.Flatten(),
        layers.Dense(1024, activation='relu'),
        layers.Dropout(0.4),
        layers.Dense(num_classes)
    ])

    model.compile(optimizer='adam',
                  loss=tf.keras.losses.SparseCategoricalCrossentropy(
                      from_logits=True),
                  metrics=['accuracy'])

    return model


def setTrainingData(data):
    return tf.keras.preprocessing.image_dataset_from_directory(
        data,
        validation_split=0.2,
        subset="training",
        seed=seed,
        image_size=(img_height, img_width),
        batch_size=batch_size)


def setValidationData(data):
    return tf.keras.preprocessing.image_dataset_from_directory(
        data,
        validation_split=0.2,
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
    plt.savefig(title + "-trainingResult" +
                str(training_epochs)+"-"+str(batch_size)+".png")
    plt.close()


def main(*argv):

    # Need for identifcation later on
    dataTitles = ["Top", "Side", "Front"]
    models = [createModel(), createModel(), createModel()]
    trainingData = getTrainingDataTuples()
    print(trainingData)
    index = 0

    for training, validation in trainingData:

        print("Starting to Train View " + dataTitles[index])
        history = models[index].fit(
            training,
            validation_data=validation,
            epochs=training_epochs
        )

        print("Done training View " + dataTitles[index])
        printGraphOfResults(history, dataTitles[index])
        index += 1


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
