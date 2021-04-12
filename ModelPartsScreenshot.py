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
def renderSceneWithRotation(offscreenRenderer, scene, rotationRad, depthBegin, depthEnd):
    rotateAllMeshesInScene(scene, rotationRad)

    pixels, depth = offscreenRenderer.render(scene)

    rows = depth.shape[0]
    cols = depth.shape[1]

    for x in range(0, rows):
        for y in range(0, cols):
            depthValue = depth[x][y]

            # make it white if no depth is present
            if depthValue == 0.0:
                depth[x][y] = 255
            else:
                # at begin depth color would be the darkest, at end - the lightest
                value = pUtils.inverseLerp(depthBegin, depthEnd, depthValue)
                depth[x][y] = 255 * value

    # convert to int
    depth = depth.astype(np.uint8)

    # turn it to w,h,3 shape
    depth = cv2.cvtColor(depth, cv2.COLOR_GRAY2RGB)

    rotateAllMeshesInScene(scene, (0, 0, 0))
    return depth


def capture(model, rotations, imageWidth = 224, imageHeight = 224, cameraZTranslation = 2.5, lightIntensity = 2.0, depthBegin = 1, depthEnd = 5):
    # Construct an offline scene
    scene = pyrender.Scene()

    # add parts
    for part in model.parts:
        scene.add(part)

    # add camera
    renderCamera = pyrender.PerspectiveCamera(yfov=np.pi / 3.0, aspectRatio=imageWidth/imageHeight)
    cameraNode = pyrender.Node(camera=renderCamera, matrix=np.eye(4))
    cameraNode.translation[2] = cameraZTranslation
    scene.add_node(cameraNode)

    # add light
    light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=lightIntensity)
    lightNode = pyrender.Node(light=light, matrix=np.eye(4))
    scene.add_node(lightNode)

    # initialize offscreen renderer
    offscreenRenderer = pyrender.OffscreenRenderer(viewport_width = imageWidth, viewport_height = imageHeight, point_size = 1.0)

    # render
    result = []
    for rotation in rotations:
        result.append(renderSceneWithRotation(offscreenRenderer, scene, rotation, depthBegin, depthEnd))

    return result