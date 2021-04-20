import copy
import ModelPartsScreenshot as mps
import numpy as np
import os
from PIL import Image
import ProjectUtils as pUtils
import pyrender
import random
import sys
from Scorer import Scorer



class Part:
    def __init__(self, mesh, label=None, side=None):
        self.mesh = copy.deepcopy(mesh)
        if label != None:
            self.label = label

        if side != None:
            self.side = side

        self.groupedParts = []

    def getSide(self, side):
        assert len(self.groupedParts) > 0
        for part in self.groupedParts:
            if part.side == side:
                return copy.deepcopy(part)
        return None

    @property
    def isGroupedOnly(self):
        return len(self.groupedParts) <= 0



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
        self.inputModels = []
        self.renderMode = 0
        self.viewerModelIndex = 0
        self.scorer = Scorer()


modelPartsViewer = ModelPartsViewer()


def setInputModels(models):
    modelPartsViewer.inputModels = copy.deepcopy(models)
    modelPartsViewer.models = copy.deepcopy(models)


def setSceneMeshes(scene, parts):
    # Remove all the current meshes
    meshNodes = list(scene.mesh_nodes)
    for meshNode in meshNodes:
        scene.remove_node(meshNode)

    # Add all the new meshes
    for part in parts:
        # we never manipulate meshes in the scene, only construct new ones
        # therefore, copying it is much safer because now we can access the "current mesh" parts
        partMesh = pyrender.Mesh.from_trimesh(part.mesh, smooth=False)
        scene.add(partMesh)


def setViewerSceneMeshes(viewer, parts):
    viewer.render_lock.acquire()
    setSceneMeshes(viewer.scene, parts)
    viewer.render_lock.release()


def setModelIndex(viewer, index):
    modelPartsViewer.viewerModelIndex = index
    modelPartsViewer.renderMode = 0
    allModelParts = modelPartsViewer.models[index].parts
    setViewerSceneMeshes(viewer, allModelParts)


def setRenderModeIndex(viewer, model, renderModeIndex):
    modelPartsViewer.renderMode = renderModeIndex

    partToView = renderModeIndex - 1
    if partToView == -1:
        setViewerSceneMeshes(viewer, model.parts)
    else:
        setViewerSceneMeshes(viewer, [model.parts[partToView]])


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
    shuffledModels = modelPartsViewer.inputModels.copy()
    random.shuffle(shuffledModels)
    requiredPart = None
    for model in shuffledModels:
        requiredPart = model.getPartByLabel(partType)
        if requiredPart != None:
            break

    return requiredPart


# API END

# Takes random pieces from collection and puts them together in a mesh, replacing parts of a random chair


def generateChair(viewer):
    # use original model as a template, not the new generated one
    originalModelCount = len(modelPartsViewer.inputModels)
    randomModelIndex = int(random.randrange(0, originalModelCount))
    randomModel = modelPartsViewer.inputModels[randomModelIndex]
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
            meshToAppend = newPart.mesh
            pUtils.scaleMeshAToB(meshToAppend, part.mesh)
            pUtils.translateMeshAToB(meshToAppend, part.mesh)
            resultParts.append(Part(mesh=meshToAppend))
            continue

        # otherwise, collection part has left and right and given part has extra parts within
        for groupedPart in part.groupedParts:
            meshToAppend = None
            if groupedPart.side == 'right':
                meshToAppend = newPart.getSide('right').mesh
            else:
                meshToAppend = newPart.getSide('left').mesh

            pUtils.scaleMeshAToB(meshToAppend, groupedPart.mesh)
            pUtils.translateMeshAToB(meshToAppend, groupedPart.mesh)

            resultParts.append(Part(mesh=meshToAppend))

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


def evalCurrentChair(viewer):
    currentModel = modelPartsViewer.models[modelPartsViewer.viewerModelIndex]

    # initialize perspectives
    rotations = [
        (0, 0, 0),  # front
        (0, np.pi/2, 0),  # right
        (np.pi/2, 0, 0),  # top
    ]

    # each screenshot will have w,h,3 shape in returned array in the same order as the given rotations
    perspectives = mps.captureDepth(
        currentModel, rotations, imageWidth=224, imageHeight=224, depthBegin=1, depthEnd=5)

    score = modelPartsViewer.scorer.score(perspectives)

    print("Evaluator Gave the Chair a score of " + str(score))
    pass


def takePositiveScreenShot(viewer):
    currentModel = modelPartsViewer.models[modelPartsViewer.viewerModelIndex]

    outputDir = "dataset/imageData/chairs-data/positive/"

    # initialize perspectives
    rotations = [
        (0, 0, 0),  # front
        (0, np.pi/2, 0),  # right
        (np.pi/2, 0, 0),  # top
    ]

    # each screenshot will have w,h,3 shape in returned array in the same order as the given rotations
    perspectives = mps.captureDepth(
        currentModel, rotations, imageWidth=224, imageHeight=224, depthBegin=1, depthEnd=5)

    currentIndex = len(os.listdir(outputDir))
    currentIndex += 1

    im = Image.fromarray(perspectives[0])
    im.save(os.path.join(outputDir, str(currentIndex) + '.png'))

    currentIndex += 1

    im = Image.fromarray(perspectives[1])
    im.save(os.path.join(outputDir, str(currentIndex) + '.png'))

    currentIndex += 1

    im = Image.fromarray(perspectives[2])
    im.save(os.path.join(outputDir, str(currentIndex) + '.png'))
    print("Saved as a Positive Chair")
    generateChair(viewer)
    pass


def takeNegativeScreenShot(viewer):
    currentModel = modelPartsViewer.models[modelPartsViewer.viewerModelIndex]

    outputDir = "dataset/imageData/chairs-data/negative/"

    # initialize perspectives
    rotations = [
        (0, 0, 0),  # front
        (0, np.pi/2, 0),  # right
        (np.pi/2, 0, 0),  # top
    ]

    # each screenshot will have w,h,3 shape in returned array in the same order as the given rotations
    perspectives = mps.captureDepth(
        currentModel, rotations, imageWidth=224, imageHeight=224, depthBegin=1, depthEnd=5)

    currentIndex = len(os.listdir(outputDir))
    currentIndex += 1

    im = Image.fromarray(perspectives[0])
    im.save(os.path.join(outputDir, str(currentIndex) + '.png'))

    currentIndex += 1

    im = Image.fromarray(perspectives[1])
    im.save(os.path.join(outputDir, str(currentIndex) + '.png'))

    currentIndex += 1

    im = Image.fromarray(perspectives[2])
    im.save(os.path.join(outputDir, str(currentIndex) + '.png'))
    print("Saved as a Negative Chair")
    generateChair(viewer)
    pass


def start():
    modelPartsViewer.renderMode = 0
    modelPartsViewer.viewerModelIndex = 0

    defaultModel = modelPartsViewer.models[0]
    defaultScene = pyrender.Scene()
    setSceneMeshes(defaultScene, defaultModel.parts)

    pyrender.Viewer(defaultScene, registered_keys={
                    'd': viewNextModel, 'a': viewPrevModel, 's': viewPrevPart, 'w': viewNextPart, 'g': generateChair, 'x': takeScreenshot, 'y': takePositiveScreenShot, 'n': takeNegativeScreenShot, 'e': evalCurrentChair}, use_raymond_lighting=True)
