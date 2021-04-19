import random
import sys

import DatasetUtils as dt
import ModelPartsViewer as mpv

def getOrAddCollectionPart(modelIndex, partLabel, partsDictionary):
    partIdentifier = str(modelIndex)+'_'+partLabel
    collectionPart = None
    if partIdentifier in partsDictionary:
        collectionPart = partsDictionary[partIdentifier]
    else:
        collectionPart = mpv.CollectionPart()
        partsDictionary[partIdentifier] = collectionPart

    return collectionPart

def parseDatasetChairTuples(modelIndex, partsTuples, collections):
    modelParts = []
    partsDictionary = {}

    # first make a pass on grouped
    for partMesh, partSide, partLabel in partsTuples:
        if partSide != 'grouped':
            continue

        # Add model part
        part = mpv.Part(mesh = partMesh, side = partSide, label = partLabel)
        modelParts.append(part)

        # Add collection part
        collectionPart = getOrAddCollectionPart(modelIndex, partLabel, partsDictionary)
        collectionPart.label = partLabel
        collectionPart.grouped = partMesh

    # now make a pass on non grouped
    for partMesh, partSide, partLabel in partsTuples:
        if partSide == 'grouped':
            continue

        # Add model part
        # Add it to .groupedParts array if the grouped version exists
        part = mpv.Part(mesh = partMesh, side = partSide, label = partLabel)
        for modelPart in modelParts:
            if modelPart.label == partLabel and modelPart.side == 'grouped':
                modelPart.groupedParts.append(part)
                break

        # Add collection part
        collectionPart = getOrAddCollectionPart(modelIndex, partLabel, partsDictionary)
        collectionPart.label = partLabel
        if partSide == 'left':
            collectionPart.left = partMesh
        if partSide == 'right':
            collectionPart.right = partMesh
    
    # Ensure the consistency of the parts collection
    for partIdentifier, part in partsDictionary.items():
        # grouped must always be present
        assert part.grouped != None

        # if no left and right, then grouped becomes left and right
        # isGroupedOnly flag is set to true
        if part.left == None:
            assert part.right == None
            part.isGroupedOnly = True
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
    else:
        datasetIndices = sys.argv[1:]

    models = []
    collections = {'back': [], 'seat':[], 'leg': [], 'arm rest': []}
    for index in datasetIndices:
        partsTuples = dt.getDatasetObjParts(index)
        modelParts = parseDatasetChairTuples(index, partsTuples, collections)
        model = mpv.Model(modelParts)
        model.name = str(index) # for screenshotting convenience
        models.append(model)

    mpv.setCollections(collections)
    mpv.setModels(models)
    mpv.start()
