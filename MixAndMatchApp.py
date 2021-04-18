import numpy as np
import random
import sys

import DatasetUtils as dt
import DatasetViewerApp as dva
import ModelPartsScreenshot as mps
import ModelPartsViewer as mpv
import ProjectUtils as pUtils
import Scorer as scorer

def getRandomCollectionPart(partType, collections):
    collectionSize = len(collections[partType])
    if collectionSize == 0:
        return None

    randomIndex = int(random.randrange(0, collectionSize))
    return collections[partType][randomIndex]

def generateChair(models, collections):
    randomModelIndex = int(random.randrange(0, len(models)))
    randomModel = models[randomModelIndex]
    chairParts = {
        'seat': getRandomCollectionPart('seat', collections), 
        'back': getRandomCollectionPart('back', collections),
        'leg': getRandomCollectionPart('leg', collections),
        'arm rest': getRandomCollectionPart('arm rest', collections)
        }

    resultParts = []
    for part in randomModel.parts:
        newPart = chairParts[part.label]

        # there are three total sided-ness: grouped, left and right
        if part.side == 'grouped':
            newPartMesh = newPart.grouped
        elif part.side == 'right':
            newPartMesh = newPart.right
        else:
            newPartMesh = newPart.left

        pUtils.scaleMeshAToB(newPartMesh, part.mesh)
        pUtils.translateMeshAToB(newPartMesh, part.mesh, part.label)

        resultParts.append(mpv.Part(mesh=newPartMesh, originalPart=part))
    return mpv.Model(resultParts)


if __name__ == "__main__":
    # take 10 random chairs and form collections
    sourceChairCount = 3
    datasetIndices = []
    for i in range(sourceChairCount):
        randomIndex = int(random.randrange(1, 6201))
        datasetIndices.append(str(randomIndex))
    
    models = []
    collections = {'back': [], 'seat':[], 'leg': [], 'arm rest': []}
    for index in datasetIndices:
        partsTuples = dt.getDatasetObjParts(index)
        modelParts = dva.parseDatasetChairTuples(index, partsTuples, collections)
        model = mpv.Model(modelParts)
        model.name = str(index)
        models.append(model)
    
    # generate 10 new chairs
    generatedChairCount = 10
    newChairs = []
    for i in range(generatedChairCount):
        newChair = generateChair(models, collections)
        newChairs.append(newChair)
    
    # screenshot every new chair
    rotations = [
        (0, 0, 0),  # front
        (0, np.pi, 0),  # back
        (0, -np.pi/2, 0),  # left
        (0, np.pi/2, 0),  # right
        (np.pi/2, 0, 0),  # top
        (-np.pi/2, 0, 0)  # bottom
    ]

    depthScreenshots = []
    for generatedChair in newChairs:
        perspectives = mps.captureDepth(generatedChair, rotations, imageWidth=224, imageHeight=224)
        depthScreenshots.append((generatedChair, perspectives))

    # Assign a score
    scoredChairs = []
    for generatedChair, perspectives in depthScreenshots:
        score = scorer.score(perspectives)
        scoredChairs.append((generatedChair, score))

    # sort models depending on the score, from bigger to smaller
    chairsToDisplay = []
    sortedChairs = sorted(scoredChairs, reverse=True, key=lambda tup: tup[1])
    for chair, value in sortedChairs:
        print(value)
        chairsToDisplay.append(chair)

    # set models in a viewer
    mpv.setCollections(collections)
    mpv.setModels(chairsToDisplay)
    mpv.start()