import copy
import cv2
import numpy as np
import ProjectUtils as pUtils
import pyrender

# Permanently changes the rotation
def rotateAllMeshesInScene(scene, rotationRad):
    for meshNode in scene.mesh_nodes:
            quaternionRotation = pUtils.radEuler2Quat(rotationRad)
            meshNode.rotation = quaternionRotation

# Rotates meshes, takes picture and resets the rotation back
def renderSceneWithRotation(offscreenRenderer, scene, rotationRad, imageSize, grayscale):
    rotateAllMeshesInScene(scene, rotationRad)

    pixels, depth = offscreenRenderer.render(scene)
    if grayscale:
        # Convert there and back so we still have shape w,h,3
        pixels = cv2.cvtColor(pixels, cv2.COLOR_RGB2GRAY)
        pixels = cv2.cvtColor(pixels, cv2.COLOR_GRAY2RGB)

    pixels = cv2.resize(pixels, dsize=imageSize, interpolation=cv2.INTER_CUBIC)

    rotateAllMeshesInScene(scene, (0, 0, 0))
    return pixels


def capture(model, rotations, viewportWidth = 500, viewportHeight = 500, imageWidth = 224, imageHeight = 224, cameraZTranslation = 2.5, lightIntensity = 2.0, grayscale=True):
    # Construct an offline scene
    scene = pyrender.Scene()

    # add parts
    for part in model.parts:
        scene.add(part)

    # add camera
    renderCamera = pyrender.PerspectiveCamera(yfov=np.pi / 3.0, aspectRatio=viewportWidth/viewportHeight)
    cameraNode = pyrender.Node(camera=renderCamera, matrix=np.eye(4))
    cameraNode.translation[2] = cameraZTranslation
    scene.add_node(cameraNode)

    # add light
    light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=lightIntensity)
    lightNode = pyrender.Node(light=light, matrix=np.eye(4))
    scene.add_node(lightNode)

    # initialize offscreen renderer
    offscreenRenderer = pyrender.OffscreenRenderer(viewport_width = viewportWidth, viewport_height = viewportHeight, point_size = 1.0)

    # render
    result = []
    for rotation in rotations:
        result.append(renderSceneWithRotation(offscreenRenderer, scene, rotation, (imageWidth, imageHeight), grayscale))

    return result