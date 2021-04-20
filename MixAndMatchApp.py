import numpy as np
import random
import sys

import DatasetUtils as dt
import DatasetViewerApp as dva
import ModelPartsScreenshot as mps
import ModelPartsViewer as mpv
import ProjectUtils as pUtils
from Scorer import Scorer

from MLStatics import *

if __name__ == "__main__":
    # take 10 random chairs and form collections
    sourceChairCount = 10
    datasetIndices = []
    for i in range(sourceChairCount):
        randomIndex = int(random.randrange(1, 6201))
        datasetIndices.append(str(randomIndex))

    models = []
    for index in datasetIndices:
        partsTuples = dt.getDatasetObjParts(index)
        modelParts = dva.parseDatasetChairTuples(index, partsTuples)
        model = mpv.Model(modelParts)
        model.name = str(index)
        models.append(model)

    # generate 10 new chairs
    generatedChairCount = 10
    newChairs = []
    for i in progressbar(range(generatedChairCount), "Generating Chairs"):
        newChair = mpv.generateChair(models)
        newChairs.append(newChair)

    # screenshot every new chair
    rotations = [
        (np.pi/2, 0, 0),  # top
        (0, np.pi/2, 0),  # right
        (0, 0, 0),  # front
        # (0, np.pi, 0),  # back
        # (0, -np.pi/2, 0),  # left
        # (-np.pi/2, 0, 0)  # bottom
    ]

    depthScreenshots = []
    for generatedChair in newChairs:
        perspectives = mps.captureDepth(
            generatedChair, rotations, imageWidth=224, imageHeight=224)
        depthScreenshots.append((generatedChair, perspectives))

    s = Scorer()

    # Assign a score
    scoredChairs = []
    for generatedChair, perspectives in progressbar(depthScreenshots, "Evaluating Chairs"):
        score = s.score(perspectives)
        scoredChairs.append((generatedChair, score))

    # sort models depending on the score, from bigger to smaller
    chairsToDisplay = []
    sortedChairs = sorted(scoredChairs, reverse=True, key=lambda tup: tup[1])
    for chair, value in sortedChairs:
        print(value)
        chairsToDisplay.append(chair)

    # set models in a viewer
    mpv.setInputModels(chairsToDisplay)
    mpv.start()
