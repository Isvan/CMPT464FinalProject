import random
import sys

import DatasetUtils as dt
import numpy as np
import pyrender
import ModelPartsViewer as mpv
from MLStatics import *
from PIL import Image
import ModelPartsScreenshot as mps



def parseDatasetChairTuples(modelIndex, partsTuples):
    modelParts = []

    # first make a pass on grouped
    for partMesh, partSide, partLabel in partsTuples:
        if partSide != 'grouped':
            continue

        # Add model part
        part = mpv.Part(mesh=partMesh, label=partLabel)
        modelParts.append(part)

    # now make a pass on non grouped
    for partMesh, partSide, partLabel in partsTuples:
        if partSide == 'grouped':
            continue

        # Add model part
        # Add it to .groupedParts array if the grouped version exists
        for modelPart in modelParts:
            if modelPart.label == partLabel:
                sidePart = mpv.Part(mesh=partMesh, side=partSide)
                modelPart.groupedParts.append(sidePart)
                break

    # return model parts
    return modelParts


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please run with dataset indices (1-6201) (example: \"DatasetViewerApp.py 1 2 3\") or to test \"DatasetViewerApp.py -r 10\"")
        quit()

    datasetIndices = []
    if sys.argv[1] == '-r':
        if len(sys.argv) < 3:
            print("Random mode: enter the number of random chairs to get from dataset e.g. \"DatasetViewerApp.py -r 10\"")
            quit()

        randomAmount = int(sys.argv[2])
        for i in range(randomAmount):
            randomIndex = int(random.randrange(1, 6201))
            datasetIndices.append(str(randomIndex))

    elif sys.argv[1] == '-t':
        print("Starting to load all models and then convert each to training data, if you dont want this exit now!")
        # This can run out of memory (it did on my 64gb) so keep track of where it exits out and manually do it in parts
        datasetIndices = range(0, 6201)

        models = []
        collections = {'back': [], 'seat': [], 'leg': [], 'arm rest': []}

        outputDir = "dataset/imageData/chairs-data/positive/"

        currentIndex = len(os.listdir(outputDir))
        currentIndex += 1

        # initialize perspectives
        rotations = [
            (0, 0, 0),  # front
            (0, np.pi/2, 0),  # right
            (np.pi/2, 0, 0),  # top
        ]

        for index in progressbar(datasetIndices):
            partsTuples = dt.getDatasetObjParts(index)
            modelParts = parseDatasetChairTuples(
                index, partsTuples, collections)
            currentModel = mpv.Model(modelParts)

            # each screenshot will have w,h,3 shape in returned array in the same order as the given rotations
            perspectives = mps.captureDepth(
                currentModel, rotations, imageWidth=224, imageHeight=224, depthBegin=1, depthEnd=5)

            im = Image.fromarray(perspectives[0])
            im.save(os.path.join(outputDir, str(currentIndex) + '.png'))

            currentIndex += 1

            im = Image.fromarray(perspectives[1])
            im.save(os.path.join(outputDir, str(currentIndex) + '.png'))

            currentIndex += 1

            im = Image.fromarray(perspectives[2])
            im.save(os.path.join(outputDir, str(currentIndex) + '.png'))

            currentIndex += 1

        quit()
        pass
    else:
        datasetIndices = sys.argv[1:]

    models = []
    for index in progressbar(datasetIndices, "Fetching Model Data"):
        partsTuples = dt.getDatasetObjParts(index)
        modelParts = parseDatasetChairTuples(index, partsTuples)
        model = mpv.Model(modelParts)
        model.name = str(index)  # for screenshotting convenience
        models.append(model)

    mpv.setInputModels(models)
    mpv.start()
