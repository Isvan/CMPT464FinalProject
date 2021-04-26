import sys
import os
import random

# Global Static Settings that need to be synced for training/evaluating
batch_size = 64
img_height = 100
img_width = 100
training_epochs = 256

# For now hardset seed, but in the future just set to some random number or current time
seed = random.randint(0, 1000000000)

checkpointFilepath = os.path.join("ML", "ourML", "checkpoint", "")
graphResultsFolder = os.path.join("ML", "ourML", "trainingResults", "")

dataTitlesTripleView = ["Top", "Side", "Front"]
trainingDataLocation = os.path.join("dataset", "imageData", "chairs-data")
evalDataLocation = os.path.join("dataset", "imageData", "evaluate-chairs", "")

# https://stackoverflow.com/questions/3160699/python-progress-bar
# Code for progress bar as it can take a while and I want some sort of visual that its working


def progressbar(it, prefix="", size=60, file=sys.stdout):
    count = len(it)

    def show(j):
        x = int(size*j/count)
        file.write("%s[%s%s] %i/%i\r" %
                   (prefix, "#"*x, "."*(size-x), j, count))
        file.flush()
    show(0)
    for i, item in enumerate(it):
        yield item
        show(i+1)
    file.write("\n")
    file.flush()
