import numpy as np
import os
import random
import sys
import trimesh

import DatasetUtils as dt
import DatasetViewerApp as dva
import ModelPartsScreenshot as mps
import ModelPartsViewer as mpv
import ProjectUtils as pUtils
from Scorer import Scorer

from MLStatics import *

if __name__ == "__main__":
    tokens = sys.argv[1:]
    if len(tokens) <= 0:
        print('- Run with random dataset indices e.g. \"MixAndMatchApp.py -r 5\"')
        print('- Run with defense sets e.g. \"MixAndMatchApp.py -setA (or setB, setC)\"')
        print('- Specify how many chairs to generate and the pool size e.g. \"MixAndMatchApp.py -r 5 -g 10 -p 100\"')
        quit()

    chairsToGenerateCount = 10
    if '-g' in tokens:
        index = tokens.index('-g')
        chairsToGenerateCount = int(tokens[index+1])

    chairPoolCount = 200
    if '-p' in tokens:
        index = tokens.index('-p')
        chairPoolCount = int(tokens[index+1])

    datasetIndices = []
    if '-r' in tokens:
        index = tokens.index('-r')
        randomAmount = int(tokens[index+1])
        randomShuffledIndices = list(range(1, 6202))
        random.shuffle(randomShuffledIndices)
        datasetIndices = randomShuffledIndices[:randomAmount]

    if '-setA' in tokens:
        datasetIndices = ['369', '175', '5540']

    if '-setB' in tokens:
        datasetIndices = ['2999', '2150', '3492', '4474', '2160']

    if '-setC' in tokens:
        datasetIndices = ['1919', '3366', '3521', '3204', '1131', '173', '3749', '2313', '5117', '1920']
    
    # Start
    print('Running program for indices: '+str(datasetIndices))
    print('# of chairs to generate: '+str(chairsToGenerateCount))
    print('Size of the pool: '+str(chairPoolCount))


    models = []
    for index in datasetIndices:
        partsTuples = dt.getDatasetObjParts(index)
        modelParts = dva.parseDatasetChairTuples(index, partsTuples)
        model = mpv.Model(modelParts)
        model.name = str(index)
        model.datasetIndex = str(index)
        model.datasetObjIndex = dt.getDatasetObjIndex(index)
        models.append(model)

    # fill the chair pool
    newChairs = []
    for i in progressbar(range(chairPoolCount), "Generating Chairs"):
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

    # we would need only 10 top chairs
    chairsToDisplay = chairsToDisplay[:chairsToGenerateCount]

    # export the chairs as .objs
    for i in range(len(chairsToDisplay)):
        fileName = str(i) + '.obj'
        mpv.exportModelAsObj(chairsToDisplay[i], fileName)

    # set models in a viewer
    mpv.setInputModels(chairsToDisplay)
    mpv.start()
