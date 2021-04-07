import copy
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


def viewNextModel(viewer):
    nextIndex = (modelPartsViewer.viewerModelIndex+1) % len(modelPartsViewer.models)
    setModelIndex(viewer, nextIndex)


def viewPrevModel(viewer):
    prevIndex = (modelPartsViewer.viewerModelIndex-1) % len(modelPartsViewer.models)
    setModelIndex(viewer, prevIndex)


def viewNextPart(viewer):
    model = modelPartsViewer.models[modelPartsViewer.viewerModelIndex]
    totalPartsCount = len(model.parts)

    # total of partsCount+1 modes of display
    modelPartsViewer.renderMode = (
        modelPartsViewer.renderMode + 1) % (totalPartsCount + 1)

    partToView = modelPartsViewer.renderMode - 1
    if partToView == -1:
        setSceneMeshes(viewer, model.parts)
    else:
        setSceneMeshes(viewer, [model.parts[partToView]])


def viewPrevPart(viewer):
    model = modelPartsViewer.models[modelPartsViewer.viewerModelIndex]
    totalPartsCount = len(model.parts)

    # total of partsCount+1 modes of display
    modelPartsViewer.renderMode = (
        modelPartsViewer.renderMode - 1) % (totalPartsCount + 1)

    partToView = modelPartsViewer.renderMode - 1
    if partToView == -1:
        setSceneMeshes(viewer, model.parts)
    else:
        setSceneMeshes(viewer, [model.parts[partToView]])

def getRandomCollectionPart(partType):
    collectionSize = len(modelPartsViewer.collections[partType])
    if collectionSize == 0:
        return None

    randomIndex = int(random.randrange(0, collectionSize))
    mesh = modelPartsViewer.collections[partType][randomIndex]
    return mesh

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

    generatedChairModel = Model(parts)
    modelPartsViewer.models.append(generatedChairModel)

    setModelIndex(viewer, len(modelPartsViewer.models)-1)


def setModels(models):
    modelPartsViewer.models = copy.deepcopy(models)

def setCollections(collections):
    modelPartsViewer.collections = copy.deepcopy(collections)


def start():
    modelPartsViewer.renderMode = 0
    modelPartsViewer.viewerModelIndex = 0

    defaultModel = modelPartsViewer.models[0]
    defaultScene = pyrender.Scene()
    for part in defaultModel.parts:
        defaultScene.add(part)

    pyrender.Viewer(defaultScene, registered_keys={
                    'd': viewNextModel, 'a': viewPrevModel, 's': viewPrevPart, 'w': viewNextPart, 'g': generateChair}, use_raymond_lighting=True)
