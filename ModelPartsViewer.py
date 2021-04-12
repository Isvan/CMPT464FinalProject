import copy
import ModelPartsScreenshot as mps
import numpy as np
import os
from PIL import Image
import ProjectUtils as pUtils
import pyrender
import random

class Model:
    # parts are an array of type pyrender.Mesh
    def __init__(self, parts):
        self.parts = copy.deepcopy(parts)


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

def setSceneMeshes(viewer, meshes):
    viewer.render_lock.acquire()

    # Remove all the current meshes
    meshNodes = list(viewer.scene.mesh_nodes)
    for meshNode in meshNodes:
        viewer.scene.remove_node(meshNode)

    # Add all the new meshes
    for mesh in meshes:
        viewer.scene.add(mesh)

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
    nextIndex = (modelPartsViewer.viewerModelIndex+1) % len(modelPartsViewer.models)
    setModelIndex(viewer, nextIndex)


def viewPrevModel(viewer):
    prevIndex = (modelPartsViewer.viewerModelIndex-1) % len(modelPartsViewer.models)
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
    mesh = modelPartsViewer.collections[partType][randomIndex]
    return copy.deepcopy(mesh)

def partExistsInCollection(part, label):
    for collectionPart in modelPartsViewer.collections[label]:
        if part.name == collectionPart.name:
            return True
    return False

def getPartLabel(part):
    if partExistsInCollection(part, 'back'):
        return 'back'
    if partExistsInCollection(part, 'seat'):
        return 'seat'
    if partExistsInCollection(part, 'leg'):
        return 'leg'
    if partExistsInCollection(part, 'arm rest'):
        return 'arm rest'

    return None

def getModelPartByLabel(model, label):
    for part in model.parts:
        for collectionPart in modelPartsViewer.collections[label]:
            if part.name == collectionPart.name:
                return copy.deepcopy(collectionPart)
                
    return None

# Use this method if you want to make a copy of the model with parts not being a part of any scene.
# This is more of a temporary hack to generate un-bound mesh, will be fixed later.
def generateOfflineModel(model):
    resultParts = []
    for part in model.parts:
        primitives = []
        for partPrimitive in part.primitives:
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
        partCopy = pyrender.Mesh(primitives, name=part.name)
        resultParts.append(partCopy)
    return Model(resultParts)


############################ API END

def generateChair(viewer):
    # get random back, random seat, random leg, random arm rest
    backPartMesh = getRandomCollectionPart('back')
    seatPartMesh = getRandomCollectionPart('seat')
    legPartMesh = getRandomCollectionPart('leg')
    armRestPartMesh = getRandomCollectionPart('arm rest')

    parts = []
    if backPartMesh != None:
        parts.append(backPartMesh)
    if seatPartMesh != None:
        parts.append(seatPartMesh)
    if legPartMesh != None:
        parts.append(legPartMesh)
    if armRestPartMesh != None:
        parts.append(armRestPartMesh)

    showNewModelFromParts(viewer, parts)

def testFeature(viewer):
    # models contain all input chair models, each has .parts field with all available parts
    models = modelPartsViewer.models

    # collections['back'] contain all of back parts as pyrender.Mesh objects
    collections = modelPartsViewer.collections

    # Test task: let's take the seat of the currently displayed chair, replace all the legs and take some random back.

    # getModelPartByLabel(model, 'seat') can be used to get the seat part from the given model
    # altering the mesh does not lead to altering of the model
    # type: pyrender.Mesh 
    currentModel = models[modelPartsViewer.viewerModelIndex]
    currentModelSeatMesh = getModelPartByLabel(currentModel, 'seat')

    # getRandomCollectionPart('back') can be used to retrieve a random mesh from the collection.
    # altering the mesh does not lead to altering of the collection
    # type: pyrender.Mesh 
    randomBackMesh = getRandomCollectionPart('back')

    # each mesh contains primitives (pyrender.Primitive) and each primitive is our more familiar "mesh" with vertices, normals, etc.
    # usually mesh would have just one primitive (itself)
    # let's alter the back slightly
    for primitive in randomBackMesh.primitives:
        for pos in primitive.positions:
            randomVector = pUtils.randomUnitVector() * 0.02
            pos+=randomVector

    # now let's replace all the chair legs
    legToReplaceWith = getRandomCollectionPart('leg')
    newLegs = []
    for part in currentModel.parts:
        if getPartLabel(part) != 'leg':
            continue
        
        # if it's a leg, then translate all the vertices from one centroid to another
        newLeg = copy.deepcopy(legToReplaceWith)
        pUtils.translateMeshAToB(newLeg, part)
        newLegs.append(newLeg)

    # combine all the parts
    resultParts = []
    resultParts.append(randomBackMesh)
    resultParts.append(currentModelSeatMesh)
    for leg in newLegs:
        resultParts.append(leg)

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

    firstIndex = int(offlineModel.parts[0].name[0:offlineModel.parts[0].name.find("_")])
    isGeneratedModel = False
    for part in offlineModel.parts:
        index = int(part.name[0:part.name.find("_")])
        if firstIndex != index:
            isGeneratedModel = True

    # images are saved in either {num}/ folder if original chairs or in generated/ folder if were generated.
    modelDirectory = str(firstIndex) + '/'
    if isGeneratedModel:
        modelDirectory = 'generated/'

    directory = os.path.join(directory, modelDirectory)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # initialize perspectives
    rotations = [
        (0, 0, 0),          #front
        (0, np.pi, 0),      #back
        (0,-np.pi/2,0),     #left
        (0,np.pi/2,0),      #right
        (np.pi/2,0,0),      #top
        (-np.pi/2,0,0)      #bottom
    ]

    # each screenshot will have w,h,3 shape in returned array in the same order as the given rotations
    perspectives = mps.capture(offlineModel, rotations, viewportWidth = 640, viewportHeight = 640, imageWidth=224, imageHeight=224, grayscale=True)

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
        defaultScene.add(part)

    pyrender.Viewer(defaultScene, registered_keys={
                    'd': viewNextModel, 'a': viewPrevModel, 's': viewPrevPart, 'w': viewNextPart, 'g': generateChair, 't': testFeature, 'x':takeScreenshot}, use_raymond_lighting=True)
