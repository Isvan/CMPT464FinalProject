import copy
import pyrender


class Model:
    # parts are an array of type pyrender.Mesh
    def __init__(self, parts):
        self.parts = copy.deepcopy(parts)


class ModelPartsViewer:
    def __init__(self):
        self.models = []
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


def viewNextModel(viewer):
    modelPartsViewer.viewerModelIndex = (
        modelPartsViewer.viewerModelIndex+1) % len(modelPartsViewer.models)
    modelPartsViewer.renderMode = 0
    allModelParts = modelPartsViewer.models[modelPartsViewer.viewerModelIndex].parts
    setSceneMeshes(viewer, allModelParts)


def viewPrevModel(viewer):
    modelPartsViewer.viewerModelIndex = (
        modelPartsViewer.viewerModelIndex-1) % len(modelPartsViewer.models)
    modelPartsViewer.renderMode = 0
    allModelParts = modelPartsViewer.models[modelPartsViewer.viewerModelIndex].parts
    setSceneMeshes(viewer, allModelParts)


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


def setModels(models):
    modelPartsViewer.models = copy.deepcopy(models)


def start():
    modelPartsViewer.renderMode = 0
    modelPartsViewer.viewerModelIndex = 0

    defaultModel = modelPartsViewer.models[0]
    defaultScene = pyrender.Scene()
    for part in defaultModel.parts:
        defaultScene.add(part)

    pyrender.Viewer(defaultScene, registered_keys={
                    'd': viewNextModel, 'a': viewPrevModel, 's': viewPrevPart, 'w': viewNextPart}, use_raymond_lighting=True)
