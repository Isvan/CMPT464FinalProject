import random
import sys

import DatasetUtils as dt
import ModelPartsViewer as mpv

def parseDatasetChairTuples(partsTuples, collections):
    modelParts = []
    partsDictrionary = {}
    for partMesh, partSide, partLabel in partsTuples:
        part = mpv.Part(mesh = partMesh, side = partSide, label = partLabel)

        # first - construct the model to manipulate and display
        # remove 'grouped' piece if just found 'left' or 'right'
        for modelPart in modelParts:
            if modelPart.label == partLabel and modelPart.side == 'grouped':
                modelParts.remove(modelPart)
                break

        modelParts.append(part)

        # second - form the new collection
        # would like to access collections['leg'][0] for example, which would have .left, .right, .grouped
        partIdentifier = str(index)+'_'+partLabel
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
    else:
        datasetIndices = sys.argv[1:]

    models = []
    collections = {'back': [], 'seat':[], 'leg': [], 'arm rest': []}
    for index in datasetIndices:
        partsTuples = dt.getDatasetObjParts(index)
        modelParts = parseDatasetChairTuples(partsTuples, collections)
        model = mpv.Model(modelParts)
        model.name = str(index) # for screenshotting convenience
        models.append(model)

    mpv.setCollections(collections)
    mpv.setModels(models)
    mpv.start()
