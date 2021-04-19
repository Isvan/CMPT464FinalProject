import random
import sys

import DatasetUtils as dt
import ModelPartsViewer as mpv

def parseDatasetChairTuples(modelIndex, partsTuples):
    modelParts = []

    # first make a pass on grouped
    for partMesh, partSide, partLabel in partsTuples:
        if partSide != 'grouped':
            continue

        # Add model part
        part = mpv.Part(mesh = partMesh, label = partLabel)
        modelParts.append(part)

    # now make a pass on non grouped
    for partMesh, partSide, partLabel in partsTuples:
        if partSide == 'grouped':
            continue

        # Add model part
        # Add it to .groupedParts array if the grouped version exists
        for modelPart in modelParts:
            if modelPart.label == partLabel:
                sidePart = mpv.Part(mesh = partMesh, side = partSide)
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
    else:
        datasetIndices = sys.argv[1:]

    models = []
    for index in datasetIndices:
        partsTuples = dt.getDatasetObjParts(index)
        modelParts = parseDatasetChairTuples(index, partsTuples)
        model = mpv.Model(modelParts)
        model.name = str(index) # for screenshotting convenience
        models.append(model)

    mpv.setInputModels(models)
    mpv.start()
