
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.models import Sequential
from tensorflow.keras.callbacks import LearningRateScheduler
import numpy as np

from MLStatics import *


def getSingleViewModelSingleDim():
    num_classes = 2

    model = Sequential([
        layers.experimental.preprocessing.Rescaling(
            1./255, input_shape=(img_height, img_width, 1)),

        layers.experimental.preprocessing.RandomTranslation(
            0.1, 0.1),
        layers.experimental.preprocessing.RandomRotation(0.2),
        layers.experimental.preprocessing.RandomZoom(0.1),

        layers.Conv2D(32, 5, padding='same', activation='relu'),
        layers.MaxPooling2D(),
        layers.Dropout(0.2),
        layers.Conv2D(64, 5, padding='same', activation='relu'),
        layers.MaxPooling2D(),
        layers.Dropout(0.2),
        layers.Conv2D(128, 5, padding='same', activation='relu'),
        layers.MaxPooling2D(),
        layers.Dropout(0.2),
        layers.Flatten(),
        layers.Dense(1024, activation='relu'),
        layers.Dropout(0.2),
        layers.Dense(512, activation='relu'),
        layers.Dense(num_classes)
    ])

    model.compile(optimizer='adam',
                  loss=tf.keras.losses.SparseCategoricalCrossentropy(
                      from_logits=True),
                  metrics=['accuracy'],
                  steps_per_execution=10)

    return model


def createConvolutionLayer(inputLayer):

    inputs = layers.Input(shape=(img_height, img_width, 1))

    # inputs = layers.experimental.preprocessing.Rescaling(
    #    1./255)(inputLayer)

    layer = layers.experimental.preprocessing.RandomTranslation(
        0.1, 0.1)(inputLayer)

    layer = layers.experimental.preprocessing.RandomRotation(0.1)(layer)
    layer = layers.experimental.preprocessing.RandomZoom(0.1)(layer)

    layer = layers.Conv2D(16, 5, padding='same')(layer)
    layer = layers.LeakyReLU(alpha=0.1)(layer)

    layer = layers.MaxPooling2D(pool_size=(2, 2), padding='same')(layer)
    layer = layers.Dropout(0.3)(layer)

    layer = layers.Conv2D(16, 1, padding='same')(layer)
    layer = layers.LeakyReLU(alpha=0.1)(layer)

    layer = layers.Conv2D(32, 5, padding='same')(layer)
    layer = layers.LeakyReLU(alpha=0.1)(layer)

    layer = layers.Conv2D(16, 1, padding='same')(layer)
    layer = layers.LeakyReLU(alpha=0.1)(layer)

    layer = layers.MaxPooling2D(pool_size=(2, 2), padding='same')(layer)
    layer = layers.Dropout(0.3)(layer)

    layer = layers.Conv2D(64, 3, padding='same')(layer)
    layer = layers.LeakyReLU(alpha=0.1)(layer)

    layer = layers.MaxPooling2D(pool_size=(2, 2), padding='same')(layer)
    layer = layers.Dropout(0.3)(layer)

    return layer


# Guide I followed for the Multi Branch stuff
# https://medium.datadriveninvestor.com/dual-input-cnn-with-keras-1e6d458cd979

def getMultiViewModel():

    topViewInput = layers.Input(shape=(img_height, img_width, 1))
    topViewModel = createConvolutionLayer(topViewInput)

    sideViewInput = layers.Input(shape=(img_height, img_width, 1))
    sideViewModel = createConvolutionLayer(sideViewInput)

    frontViewInput = layers.Input(shape=(img_height, img_width, 1))
    frontViewModel = createConvolutionLayer(frontViewInput)

    concatted = tf.keras.layers.Concatenate()(
        [topViewModel, sideViewModel, frontViewModel])

    concatted = layers.Flatten()(concatted)

    dense = layers.Dense(512)(concatted)
    dense = layers.LeakyReLU(alpha=0.1)(dense)
    dense = layers.Dropout(0.25)(dense)

    dense = layers.Dense(256)(concatted)
    dense = layers.LeakyReLU(alpha=0.1)(dense)
    dense = layers.Dropout(0.25)(dense)

    dense = layers.Dense(128)(dense)
    dense = layers.LeakyReLU(alpha=0.1)(dense)
    dense = layers.Dropout(0.4)(dense)

    output = layers.Dense(2, activation='softmax')(dense)

    model = tf.keras.Model(inputs=[topViewInput, sideViewInput,
                                   frontViewInput], outputs=[output])

    optimizer = tf.keras.optimizers.Adam()

    model.compile(optimizer=optimizer,
                  loss=tf.keras.losses.SparseCategoricalCrossentropy(
                      from_logits=True),
                  metrics=['accuracy'],
                  steps_per_execution=10)

    return model

# Guide on learning schedules
# https://www.jeremyjordan.me/nn-learning-rate/


def getLearningRateSchedule(initial_lr=1e-3, decay_factor=0.75, step_size=20):
    def schedule(epoch):
        return initial_lr * (decay_factor ** np.floor(epoch/step_size))

    return LearningRateScheduler(schedule)
