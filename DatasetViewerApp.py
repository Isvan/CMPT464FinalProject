import sys

import DatasetUtils as dt
import ModelPartsViewer as mpv

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please run with .obj numbers (example: \"DatasetViewerApp.py 1997 2110 2121\")")
    else:
        datasetIndices = sys.argv[1:]
        models = []
        for index in datasetIndices:
            objIndex = dt.getDatasetMeshObjIndex(index)
            parts = dt.getDatasetObjParts(objIndex)
            models.append(mpv.Model(parts))

        mpv.setModels(models)
        mpv.start()
        

