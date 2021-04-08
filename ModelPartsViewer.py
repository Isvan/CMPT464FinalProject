import copy
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
    # collections['back'] contain all of back parts as pyrender.Mesh objects
    collections = modelPartsViewer.collections

    # getRandomCollectionPart('back') can be used to retrieve a random mesh.
    # altering the mesh does not lead to altering of the collection
    # type: pyrender.Mesh 
    randomBackMesh = getRandomCollectionPart('back')

    # each mesh contains primitives and each primitive is our more familiar "mesh" with vertices, normals, etc.
    # usually mesh would have just one primitive (itself)
    for primitive in randomBackMesh.primitives:
        for pos in primitive.positions:
            randomVector = pUtils.randomUnitVector() * 0.02
            pos+=randomVector

    # just use this one as is for demo purposes
    randomSeatMesh = getRandomCollectionPart('seat')

    # show the new model made out of all parts we need
    # it will appear on the screen and will be appended to the end of the viewable collection
    showNewModelFromParts(viewer, [randomBackMesh, randomSeatMesh])

def start():
    modelPartsViewer.renderMode = 0
    modelPartsViewer.viewerModelIndex = 0

    defaultModel = modelPartsViewer.models[0]
    defaultScene = pyrender.Scene()
    for part in defaultModel.parts:
        defaultScene.add(part)

    pyrender.Viewer(defaultScene, registered_keys={
                    'd': viewNextModel, 'a': viewPrevModel, 's': viewPrevPart, 'w': viewNextPart, 'g': generateChair, 't': testFeature}, use_raymond_lighting=True)
