import copy
import ModelPartsScreenshot as mps
import numpy as np
import os
from PIL import Image
import ProjectUtils as pUtils
import pyrender
import random
import sys

class Part:
    def __init__(self, mesh, originalPart = None, side = None, label = None):
        self.mesh = copy.deepcopy(mesh)
        if originalPart != None:
            self.side = originalPart.side
            self.label = originalPart.label
            self.groupedParts = copy.deepcopy(originalPart.groupedParts)
        else:
            assert side != None
            assert label != None
            self.side = side
            self.label = label
            self.groupedParts = []
    
    @property
    def isGroupedOnly(self):
        return self.side == 'grouped' and len(self.groupedParts) <= 0
    
    @property
    def hasGroupedParts(self):
        return self.side == 'grouped' and len(self.groupedParts) > 0

class CollectionPart:
    def __init__(self):
        self.left = None
        self.right = None
        self.grouped = None
        self.label = None
        self.isGroupedOnly = False

    @property
    def left(self):
        return copy.deepcopy(self._left)

    @left.setter
    def left(self, value):
        self._left = copy.deepcopy(value)

    @property
    def right(self):
        return copy.deepcopy(self._right)

    @right.setter
    def right(self, value):
        self._right = copy.deepcopy(value)

    @property
    def grouped(self):
        return copy.deepcopy(self._grouped)

    @grouped.setter
    def grouped(self, value):
        self._grouped = copy.deepcopy(value)

class Model:
    def __init__(self, parts):
        self.parts = copy.deepcopy(parts)
        self.name = "default"
    
    def getPartByLabel(self, label):
        for part in self.parts:
            if part.label == label:
                return copy.deepcopy(part)

        return None

class ModelPartsViewer:
    def __init__(self):
        self.models = []
        self.collections = {}
        self.renderMode = 0
        self.viewerModelIndex = 0


modelPartsViewer = ModelPartsViewer()


def setModels(models):
    modelPartsViewer.models = copy.deepcopy(models)


def setCollections(collections):
    modelPartsViewer.collections = copy.deepcopy(collections)


def setSceneMeshes(viewer, parts):
    viewer.render_lock.acquire()

    # Remove all the current meshes
    meshNodes = list(viewer.scene.mesh_nodes)
    for meshNode in meshNodes:
        viewer.scene.remove_node(meshNode)

    # Add all the new meshes
    for part in parts:
        # we never manipulate meshes in the scene, only construct new ones
        # therefore, copying it is much safer because now we can access the "current mesh" parts
        viewer.scene.add(copy.deepcopy(part.mesh))

    viewer.render_lock.release()


def setModelIndex(viewer, index):
    modelPartsViewer.viewerModelIndex = index
    modelPartsViewer.renderMode = 0
    allModelParts = modelPartsViewer.models[index].parts
    setSceneMeshes(viewer, allModelParts)


def setRenderModeIndex(viewer, model, renderModeIndex):
    modelPartsViewer.renderMode = renderModeIndex

    partToView = renderModeIndex - 1
    if partToView == -1:
        setSceneMeshes(viewer, model.parts)
    else:
        setSceneMeshes(viewer, [model.parts[partToView]])


def showNewModelFromParts(viewer, parts):
    generatedChairModel = Model(parts)
    modelPartsViewer.models.append(generatedChairModel)
    setModelIndex(viewer, len(modelPartsViewer.models)-1)


def viewNextModel(viewer):
    nextIndex = (modelPartsViewer.viewerModelIndex +
                 1) % len(modelPartsViewer.models)
    setModelIndex(viewer, nextIndex)


def viewPrevModel(viewer):
    prevIndex = (modelPartsViewer.viewerModelIndex -
                 1) % len(modelPartsViewer.models)
    setModelIndex(viewer, prevIndex)


def viewNextPart(viewer):
    model = modelPartsViewer.models[modelPartsViewer.viewerModelIndex]

    # total of partsCount+1 modes of display, including "full" view and one for each part
    renderModesCount = len(model.parts) + 1
    nextPartIndex = (modelPartsViewer.renderMode + 1) % renderModesCount
    setRenderModeIndex(viewer, model, nextPartIndex)


def viewPrevPart(viewer):
    model = modelPartsViewer.models[modelPartsViewer.viewerModelIndex]

    # total of partsCount+1 modes of display, including "full" view and one for each part
    renderModesCount = len(model.parts) + 1
    nextPartIndex = (modelPartsViewer.renderMode - 1) % renderModesCount
    setRenderModeIndex(viewer, model, nextPartIndex)


def getRandomCollectionPart(partType):
    collectionSize = len(modelPartsViewer.collections[partType])
    if collectionSize == 0:
        return None

    randomIndex = int(random.randrange(0, collectionSize))
    return modelPartsViewer.collections[partType][randomIndex]

# API END

# Takes random pieces from collection and puts them together in a mesh, replacing parts of a random chair
def generateChair(viewer):

    # quick hack for getting the original number of models
    # use original model as a template, not the new generated one
    originalModelCount = len(sys.argv[1:])
    randomModelIndex = int(random.randrange(0, originalModelCount))
    randomModel = modelPartsViewer.models[randomModelIndex]
    chairParts = {
        'seat': getRandomCollectionPart('seat'), 
        'back': getRandomCollectionPart('back'),
        'leg': getRandomCollectionPart('leg'),
        'arm rest': getRandomCollectionPart('arm rest')
        }

    resultParts = []
    for part in randomModel.parts:
        newPart = chairParts[part.label]

        # if randomly picked mesh is a whole single mesh, then we should just place that mesh in stead of all non-combined present parts
        # same goes if the picked part can be a whole mesh only 
        if newPart.isGroupedOnly or part.isGroupedOnly:
            # the part.mesh is by default a combined mesh
            meshToAppend = newPart.grouped
            pUtils.scaleMeshAToB(meshToAppend, part.mesh)
            pUtils.translateMeshAToB(meshToAppend, part.mesh)
            resultParts.append(Part(mesh = meshToAppend, originalPart = part))
            continue
            
        # otherwise, collection part has left and right and given part has extra parts within
        for part in part.groupedParts:
            meshToAppend = None
            if part.side == 'right':
                meshToAppend = newPart.right
            else:
                meshToAppend = newPart.left
            
            pUtils.scaleMeshAToB(meshToAppend, part.mesh)
            pUtils.translateMeshAToB(meshToAppend, part.mesh)

            resultParts.append(Part(mesh = meshToAppend, originalPart = part))

    # show the new model made out of all parts we need
    # it will appear on the screen and will be appended to the end of the viewable collection
    showNewModelFromParts(viewer, resultParts)

# Takes a screenshot of the present chair model and saves it to the folder.
# Demonstrates how to turn model into a set of pixels.
def takeScreenshot(viewer):
    currentModel = modelPartsViewer.models[modelPartsViewer.viewerModelIndex]

    # Prapre directories to write to
    directory = os.path.dirname('screenshots/')
    if not os.path.exists(directory):
        os.makedirs(directory)

    # images are saved in either {num}/ folder if original chairs or in generated/ folder if were generated.
    isGeneratedModel = currentModel.name == "default"
    modelDirectory = 'generated/'
    if not isGeneratedModel:
        modelDirectory = currentModel.name+'/'        

    directory = os.path.join(directory, modelDirectory)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # initialize perspectives
    rotations = [
        (0, 0, 0),  # front
        (0, np.pi, 0),  # back
        (0, -np.pi/2, 0),  # left
        (0, np.pi/2, 0),  # right
        (np.pi/2, 0, 0),  # top
        (-np.pi/2, 0, 0)  # bottom
    ]

    # each screenshot will have w,h,3 shape in returned array in the same order as the given rotations
    perspectives = mps.captureDepth(
        currentModel, rotations, imageWidth=224, imageHeight=224, depthBegin=1, depthEnd=5)

    im = Image.fromarray(perspectives[0])
    im.save(os.path.join(directory, 'front.png'))

    im = Image.fromarray(perspectives[1])
    im.save(os.path.join(directory, 'back.png'))

    im = Image.fromarray(perspectives[2])
    im.save(os.path.join(directory, 'left.png'))

    im = Image.fromarray(perspectives[3])
    im.save(os.path.join(directory, 'right.png'))

    im = Image.fromarray(perspectives[4])
    im.save(os.path.join(directory, 'top.png'))

    im = Image.fromarray(perspectives[5])
    im.save(os.path.join(directory, 'bottom.png'))


def start():
    modelPartsViewer.renderMode = 0
    modelPartsViewer.viewerModelIndex = 0

    defaultModel = modelPartsViewer.models[0]
    defaultScene = pyrender.Scene()
    for part in defaultModel.parts:
        defaultScene.add(copy.deepcopy(part.mesh))

    pyrender.Viewer(defaultScene, registered_keys={
                    'd': viewNextModel, 'a': viewPrevModel, 's': viewPrevPart, 'w': viewNextPart, 'g': generateChair, 'x': takeScreenshot}, use_raymond_lighting=True)
