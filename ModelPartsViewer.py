import copy
import ModelPartsScreenshot as mps
import numpy as np
import os
from PIL import Image
import ProjectUtils as pUtils
import pyrender
import random

class Part:
    def __init__(self, mesh, originalPart = None, side = None, label = None):
        self.mesh = copy.deepcopy(mesh)
        if originalPart != None:
            self.side = originalPart.side
            self.label = originalPart.label
        else:
            assert side != None
            assert label != None
            self.side = side
            self.label = label

class CollectionPart:
    def __init__(self):
        self.left = None
        self.right = None
        self.grouped = None
        self.label = None

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


# Use this method if you want to make a copy of the model with parts not being a part of any scene.
# This is more of a temporary hack to generate un-bound mesh, will be fixed later.
def generateOfflineModel(model):
    resultParts = []
    for part in model.parts:
        primitives = []
        for partPrimitive in part.mesh.primitives:
            primitive = pyrender.Primitive(
                partPrimitive.positions,
                partPrimitive.normals,
                partPrimitive.tangents,
                partPrimitive.texcoord_0,
                partPrimitive.texcoord_1,
                partPrimitive.color_0,
                partPrimitive.joints_0,
                partPrimitive.weights_0,
                partPrimitive.indices,
                partPrimitive.material,
                partPrimitive.mode,
                partPrimitive.targets,
                partPrimitive.poses
            )
            primitives.append(primitive)
        partCopy = pyrender.Mesh(primitives)
        resultParts.append(Part(mesh = partCopy, side = part.side, label = part.label))
    resultModel = Model(resultParts)
    resultModel.name = model.name
    return resultModel


# API END

# Takes random pieces from collection and puts them together in a mesh
def generateChair(viewer):
    currentModel = modelPartsViewer.models[modelPartsViewer.viewerModelIndex]
    chairParts = {
        'seat': getRandomCollectionPart('seat'), 
        'back': getRandomCollectionPart('back'),
        'leg': getRandomCollectionPart('leg'),
        'arm rest': getRandomCollectionPart('arm rest')
        }

    resultParts = []
    for part in currentModel.parts:
        newPart = chairParts[part.label]

        # there are three total sided-ness: grouped, left and right
        newPartMesh = None
        if part.side == 'grouped':
            newPartMesh = newPart.grouped
        elif part.side == 'right':
            newPartMesh = newPart.right
        else:
            newPartMesh = newPart.left

        pUtils.scaleMeshAToB(newPartMesh, part.mesh)
        pUtils.translateMeshAToB(newPartMesh, part.mesh)

        resultParts.append(Part(mesh = newPartMesh, originalPart = part))

    # show the new model made out of all parts we need
    # it will appear on the screen and will be appended to the end of the viewable collection
    showNewModelFromParts(viewer, resultParts)

# Takes a screenshot of the present chair model and saves it to the folder.
# Demonstrates how to turn model into a set of pixels.
def takeScreenshot(viewer):
    currentModel = modelPartsViewer.models[modelPartsViewer.viewerModelIndex]
    offlineModel = generateOfflineModel(currentModel)

    # Prapre directories to write to
    directory = os.path.dirname('screenshots/')
    if not os.path.exists(directory):
        os.makedirs(directory)

    # images are saved in either {num}/ folder if original chairs or in generated/ folder if were generated.
    isGeneratedModel = offlineModel.name == "default"
    modelDirectory = 'generated/'
    if not isGeneratedModel:
        modelDirectory = offlineModel.name+'/'        

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
        offlineModel, rotations, imageWidth=224, imageHeight=224, depthBegin=1, depthEnd=5)

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
        defaultScene.add(part.mesh)

    pyrender.Viewer(defaultScene, registered_keys={
                    'd': viewNextModel, 'a': viewPrevModel, 's': viewPrevPart, 'w': viewNextPart, 'g': generateChair, 'x': takeScreenshot}, use_raymond_lighting=True)
