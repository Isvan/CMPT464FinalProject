import os
import random
import sys

import DatasetUtils as dt
import numpy as np
import pyrender
import ModelPartsViewer as mpv
from MLStatics import *
from PIL import Image
import ModelPartsScreenshot as mps

def convertModelsToTrainingData():
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

def parseDatasetChairTuples(modelIndex, partsTuples):
    modelParts = []

    # first make a pass on grouped
    for partMesh, partSide, partLabel, pjoints in partsTuples:
        if partSide != 'grouped':
            continue

        # Add model part
        part = mpv.Part(mesh=partMesh, label=partLabel, joints=pjoints)
        modelParts.append(part)

    # now make a pass on non grouped
    for partMesh, partSide, partLabel, _ in partsTuples:
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

# last element in the history is the latest one
def getRunningHistory():
    if not os.path.exists('.input_history'):
        return []
    
    f = open('.input_history', 'r')
    inputs = f.readlines()
    history = []
    for line in inputs:
        strippedLine = line.strip()
        indices = strippedLine.split()
        history.append(indices)
    return history

def runProgram(datasetIndices):
    print('Running program for indices: '+str(datasetIndices))

    # save indices to history first

    # get existent history
    history = getRunningHistory()

    # append with the new indices
    newInput = []
    for index in datasetIndices:
        newInput.append(str(index))
    history.append(newInput)

    # filter by only last 10 inputs
    # we keep only the last 10 inputs
    if len(history) > 10:
        history = history[len(history) - 10:]

    # write
    f = open('.input_history', 'w')
    for elem in history:
        stringToWrite = ' '.join(elem)
        f.write(stringToWrite+'\n')
    f.close()

    # run the program
    models = []
    for index in progressbar(newInput, "Fetching Model Data"):
        partsTuples = dt.getDatasetObjParts(index)
        modelParts = parseDatasetChairTuples(index, partsTuples)
        model = mpv.Model(modelParts)
        model.name = str(index)  # for screenshotting convenience
        models.append(model)

    mpv.setInputModels(models)
    mpv.start()

if __name__ == "__main__":

    tokens = sys.argv[1:]

    if len(tokens) <= 0:
        print('- Run with dataset indices e.g. \"DatasetViewerApp.py 1 2 3\"')
        print('- Run with random dataset indices e.g. \"DatasetViewerApp.py -r 5\"')
        print('- Run last input e.g. \"DatasetViewerApp.py -l\"')
        print('- See input history  e.g. \"DatasetViewerApp.py -h\"')
        quit()

    if '-t' in tokens:
        convertModelsToTrainingData()
        quit()

    if '-h' in tokens:
        # just show history
        history = getRunningHistory()
        if len(history) > 0:
            for i in range(0, len(history)):
                displayString = '\t'+' '.join(map(str, history[i]))
                if i == len(history)-1:
                    displayString = displayString + '\t(latest)'
                print(displayString)
        else:
            print('Run the program at least once to ensure that there is a history.')
        quit()

    if '-l' in tokens:
        # retrieve latest from history and run it
        history = getRunningHistory()
        if len(history) <= 0:
            print('Run the program at least once to ensure that there is a latest input.')
            quit()
        
        lastInput = history[-1]
        runProgram(lastInput)
        quit()

    if '-r' in tokens:
        # generate n random indices and run it
        index = tokens.index('-r')
        randomAmount = int(tokens[index+1])
        randomShuffledIndices = list(range(1, 6202))
        random.shuffle(randomShuffledIndices)

        datasetIndices = randomShuffledIndices[:randomAmount]
        runProgram(datasetIndices)
        quit()

    if '-setA' in tokens:
        datasetIndices = ['369', '175', '5540']
        runProgram(datasetIndices)
        quit()

    if '-setB' in tokens:
        datasetIndices = ['2999', '2150', '3492', '4474', '2160']
        runProgram(datasetIndices)
        quit()

    if '-setC' in tokens:
        datasetIndices = ['1919', '3366', '3521', '3204', '1131', '173', '3749', '2313', '5117', '1920']
        runProgram(datasetIndices)
        quit()

    runProgram(tokens)

