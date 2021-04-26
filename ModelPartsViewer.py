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
import trimesh


class Part:
    def __init__(self, mesh, hostDatasetIndex, label=None, side=None, joints=None):
        self.mesh = copy.deepcopy(mesh)
        self.hostDatasetIndex = copy.deepcopy(hostDatasetIndex)
        if label != None:
            self.label = label

        if side != None:
            self.side = side
        if joints != None:
            self.joints = joints

        self.groupedParts = []

    def getSide(self, side):
        assert len(self.groupedParts) > 0
        for part in self.groupedParts:
            if part.side == side:
                return copy.deepcopy(part)
        return None

    def getJoints(self, side):
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
        self.datasetIndex = None
        self.datasetObjIndex = None

    def getPartByLabel(self, label):
        for part in self.parts:
            if part.label == label:
                return copy.deepcopy(part)

        return None

    # identifier only specifies the parts but not the original model the parts are based on
    def getIdentifier(self):
        identifier = ''
        for part in self.parts:
            identifier += part.hostDatasetIndex + ' '
        return identifier


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


def getCaptionForModel(model, index):
    captionText = '#'+str(index)+' - '
    if model.datasetIndex != None:
        captionText += str(model.datasetIndex)+'.mat, ' + \
            str(model.datasetObjIndex)+'.obj'
    else:
        captionText += "generated"

    caption = {'text': captionText,
               'location': pyrender.constants.TextAlign.TOP_CENTER,
               'font_name': 'fonts/Arial.ttf',
               'font_pt': 20,
               'color': (0, 0, 0, 255),
               'scale': 1
               }

    captionList = []
    captionList.append(caption)
    return captionList


def setModelIndex(viewer, index):
    modelPartsViewer.viewerModelIndex = index
    modelPartsViewer.renderMode = 0
    model = modelPartsViewer.models[index]
    viewer.viewer_flags['caption'] = getCaptionForModel(model, index)
    setViewerSceneMeshes(viewer, model.parts)


def setRenderModeIndex(viewer, model, renderModeIndex):
    modelPartsViewer.renderMode = renderModeIndex

    partToView = renderModeIndex - 1
    if partToView == -1:
        setViewerSceneMeshes(viewer, model.parts)
    else:
        setViewerSceneMeshes(viewer, [model.parts[partToView]])


def showNewModel(viewer, model):
    modelPartsViewer.models.append(model)
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


def getRandomCollectionPart(partType, inputModels):
    shuffledModels = inputModels.copy()
    random.shuffle(shuffledModels)
    requiredPart = None
    for model in shuffledModels:
        requiredPart = model.getPartByLabel(partType)
        if requiredPart != None:
            break

    return requiredPart, model


def removeFromModelListByName(models, name):
    for model in models:
        if model.name == name:
            models.remove(model)
            break


def modelListContains(models, modelToCompare):
    for model in models:
        if model.getIdentifier() == modelToCompare.getIdentifier():
            return True

    return False


# API END

# generate chair model without welding
def generateChairFast(inputModels):
    # we use a random model to "fill" out with new parts
    randomModel = inputModels[pUtils.randomInt(0, len(inputModels))]

    # initialize chair parts by default to belong to the original model
    chairParts = {
        'seat': randomModel.getPartByLabel('seat'),
        'back': randomModel.getPartByLabel('back'),
        'leg': randomModel.getPartByLabel('leg'),
        'arm rest': randomModel.getPartByLabel('arm rest')}

    # generator models holds the dynamic list of all possible chairs used for generation
    generatorModels = inputModels.copy()

    # we will fill the model by parts in random order
    partLabels = ['seat', 'back', 'leg', 'arm rest']
    random.shuffle(partLabels)

    # find a part and then remove its chair from the list of suggestions
    # if ran out of chairs - stop
    for i in range(len(partLabels)):
        if len(generatorModels) <= 0:
            break

        partLabel = partLabels[i]
        newPart, refModel = getRandomCollectionPart(partLabel, generatorModels)
        if newPart != None:
            chairParts[partLabel] = newPart
            removeFromModelListByName(generatorModels, refModel.name)

    resultParts = []
    for part in randomModel.parts:
        newPart = chairParts[part.label]
        #pUtils.scaleMeshAToB(newPart.mesh, part.mesh)
        #pUtils.translateMeshAToB(newPart.mesh, part.mesh)
        resultParts.append(newPart)
    return Model(resultParts)


# Takes random pieces from collection and puts them together in a mesh, replacing parts of a random chair
def generateChair(inputModels):
    generatedChair = generateChairFast(inputModels)
    weldChairParts(generatedChair)
    return generatedChair


def weldChairParts(chair):
    pUtils.connectJointsBeta(chair.parts)


def generateChairViewer(viewer):
    generatedChair = generateChair(modelPartsViewer.inputModels)

    # show the new model made out of all parts we need
    # it will appear on the screen and will be appended to the end of the viewable collection
    showNewModel(viewer, generatedChair)

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
    generateChairViewer(viewer)
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
    print("Saved as a Negative Chair " + outputDir + str(currentIndex))
    generateChairViewer(viewer)
    pass


def exportModelAsObj(model, filePath):
    directory = os.path.dirname('export_objs/')
    if not os.path.exists(directory):
        os.makedirs(directory)

    path = os.path.join(directory, filePath)

    resultCombinedMesh = trimesh.base.Trimesh()
    for part in model.parts:
        resultCombinedMesh = trimesh.util.concatenate(
            [resultCombinedMesh, part.mesh])

    obj = trimesh.exchange.obj.export_obj(resultCombinedMesh)
    f = open(path, "w")
    f.write(obj)
    f.close()


def exportCurrentChair(viewer):
    currentModel = modelPartsViewer.models[modelPartsViewer.viewerModelIndex]
    exportModelAsObj(currentModel, 'viewer_generated.obj')


def start():
    modelPartsViewer.renderMode = 0
    modelPartsViewer.viewerModelIndex = 0

    defaultModel = modelPartsViewer.models[modelPartsViewer.viewerModelIndex]
    defaultScene = pyrender.Scene()
    defaultCaption = getCaptionForModel(
        defaultModel, modelPartsViewer.viewerModelIndex)
    setSceneMeshes(defaultScene, defaultModel.parts)

    pyrender.Viewer(
        defaultScene,
        viewer_flags={'caption': defaultCaption},
        registered_keys={
            'd': viewNextModel,
            'a': viewPrevModel,
            's': viewPrevPart,
            'w': viewNextPart,
            'g': generateChairViewer,
            'x': takeScreenshot,
            'y': takePositiveScreenShot,
            'n': takeNegativeScreenShot,
            'e': evalCurrentChair,
            'o': exportCurrentChair},
        use_raymond_lighting=True)
