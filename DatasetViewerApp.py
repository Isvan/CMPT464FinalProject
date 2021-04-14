import sys

import DatasetUtils as dt
import ModelPartsViewer as mpv

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please run with dataset indices (1-6201) (example: \"DatasetViewerApp.py 1 2 3\")")
    else:
        datasetIndices = sys.argv[1:]
        models = []
        collections = {'back': [], 'seat':[], 'leg': [], 'arm rest': []}
        for index in datasetIndices:
            partsTuples = dt.getDatasetObjParts(index)
            modelParts = []

            for partTuple in partsTuples:
                partMesh = partTuple[0]
                partSide = partTuple[1]
                partLabel = partTuple[2]

                # naming is important because we will match parts later
                partMesh.name = str(index)+'_'+partLabel
                modelParts.append(partMesh)
                collections[partLabel].append(partMesh)

            models.append(mpv.Model(modelParts))

        # models now have full formed models
        # collections now have part meshes
        mpv.setCollections(collections)
        mpv.setModels(models)
        mpv.start()
