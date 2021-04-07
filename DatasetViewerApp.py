import sys

import DatasetUtils as dt
import ModelPartsViewer as mpv

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please run with dataset indices (1-6201) (example: \"DatasetViewerApp.py 1 2 3\")")
    else:
        datasetIndices = sys.argv[1:]
        models = []
        for index in datasetIndices:
            #objIndex = dt.getDatasetMeshObjIndex(index)
            parts = dt.getDatasetObjParts(index)
            models.append(mpv.Model(parts))

        mpv.setModels(models)
        mpv.start()
