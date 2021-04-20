import random
import sys

import DatasetUtils as dt
import numpy as np
import pyrender
import ModelPartsViewer as mpv
from MLStatics import *
from PIL import Image
import ModelPartsScreenshot as mps


def parseDatasetChairTuples(modelIndex, partsTuples, collections):
    modelParts = []
    partsDictrionary = {}
    for partMesh, partSide, partLabel in partsTuples:
        part = mpv.Part(mesh=partMesh, side=partSide, label=partLabel)

        # first - construct the model to manipulate and display
        # remove 'grouped' piece if just found 'left' or 'right'
        for modelPart in modelParts:
            if modelPart.label == partLabel and modelPart.side == 'grouped':
                modelParts.remove(modelPart)
                break

        modelParts.append(part)

        # second - form the new collection
        # would like to access collections['leg'][0] for example, which would have .left, .right, .grouped
        partIdentifier = str(modelIndex)+'_'+partLabel
        collectionPart = None
        if partIdentifier in partsDictrionary:
            collectionPart = partsDictrionary[partIdentifier]
        else:
            collectionPart = mpv.CollectionPart()
            partsDictrionary[partIdentifier] = collectionPart

        collectionPart.label = partLabel
        if partSide == 'grouped':
            collectionPart.grouped = partMesh
        if partSide == 'left':
            collectionPart.left = partMesh
        if partSide == 'right':
            collectionPart.right = partMesh

    # Ensure the consistency of the parts collection
    for partIdentifier, part in partsDictrionary.items():
        # grouped must always be present
        assert part.grouped != None

        # if no left and right, then grouped becomes left and right
        if part.left == None:
            assert part.right == None
            part.left = part.grouped
            part.right = part.grouped

        # store in appropriate collection
        collections[part.label].append(part)

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
    collections = {'back': [], 'seat': [], 'leg': [], 'arm rest': []}
    for index in progressbar(datasetIndices, "Fetching Model Data"):
        partsTuples = dt.getDatasetObjParts(index)
        modelParts = parseDatasetChairTuples(index, partsTuples, collections)
        model = mpv.Model(modelParts)
        model.name = str(index)  # for screenshotting convenience
        models.append(model)

    mpv.setCollections(collections)
    mpv.setModels(models)
    mpv.start()
