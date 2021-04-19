import numpy as np
import pyrender
import random


def normalizeVector(vector):
    v2 = np.atleast_1d(np.linalg.norm(vector))
    v2[v2 == 0] = 1
    return vector / v2


def randomUnitVector():
    randX = random.randrange(-1, 1)
    randY = random.randrange(-1, 1)
    randZ = random.randrange(-1, 1)
    vector = np.array([randX, randY, randZ])
    return normalizeVector(vector)


def scaleMeshAToB(meshA, meshB):
    extentsA = meshA.extents
    extentsB = meshB.extents
    centera = meshA.centroid
    scale = [extentsB[0]/extentsA[0], extentsB[1] /
             extentsA[1], extentsB[2]/extentsA[2]]

    for pos in meshA.vertices:
        pos -= centera
        pos[0] *= scale[0]
        pos[1] *= scale[1]
        pos[2] *= scale[2]
        pos += centera            


def translateMeshAToB(meshA, meshB):
    centroidA = meshA.centroid
    centroidB = meshB.centroid

    translationVector = centroidB - centroidA
    for pos in meshA.vertices:
        pos += translationVector            

# https://computergraphics.stackexchange.com/questions/8195/how-to-convert-euler-angles-to-quaternions-and-get-the-same-euler-angles-back-fr


def radEuler2Quat(vec3):
    x = vec3[0]
    y = vec3[1]
    z = vec3[2]
    qx = np.sin(x/2) * np.cos(y/2) * np.cos(z/2) - \
        np.cos(x/2) * np.sin(y/2) * np.sin(z/2)
    qy = np.cos(x/2) * np.sin(y/2) * np.cos(z/2) + \
        np.sin(x/2) * np.cos(y/2) * np.sin(z/2)
    qz = np.cos(x/2) * np.cos(y/2) * np.sin(z/2) - \
        np.sin(x/2) * np.sin(y/2) * np.cos(z/2)
    qw = np.cos(x/2) * np.cos(y/2) * np.cos(z/2) + \
        np.sin(x/2) * np.sin(y/2) * np.sin(z/2)

    return [qx, qy, qz, qw]


def clamp(num, minVal, maxVal):
    return max(min(num, maxVal), minVal)


def lerp(a, b, t):
    return t * a + (1-t) * b


def inverseLerp(a, b, value):
    num = (value-a)/(b-a)
    return clamp(num, 0, 1)
