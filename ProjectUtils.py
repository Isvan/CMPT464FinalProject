import numpy as np
import pyrender
import random

def normalizeVector(vector):
    return vector / np.linalg.norm(vector)

def randomUnitVector():
    randX = random.randrange(-1, 1)
    randY = random.randrange(-1, 1)
    randZ = random.randrange(-1, 1)
    vector = np.array([randX, randY, randZ])
    return normalizeVector(vector)

def translateMeshAToB(meshA, meshB):
    centroidA = meshA.centroid
    centroidB = meshB.centroid

    translationVector = centroidB - centroidA

    for primitive in meshA.primitives:
        for pos in primitive.positions:
            pos+=translationVector

#https://computergraphics.stackexchange.com/questions/8195/how-to-convert-euler-angles-to-quaternions-and-get-the-same-euler-angles-back-fr
def radEuler2Quat(vec3):
    x = vec3[0]
    y = vec3[1]
    z= vec3[2]
    qx = np.sin(x/2) * np.cos(y/2) * np.cos(z/2) - np.cos(x/2) * np.sin(y/2) * np.sin(z/2)
    qy = np.cos(x/2) * np.sin(y/2) * np.cos(z/2) + np.sin(x/2) * np.cos(y/2) * np.sin(z/2)
    qz = np.cos(x/2) * np.cos(y/2) * np.sin(z/2) - np.sin(x/2) * np.sin(y/2) * np.cos(z/2)
    qw = np.cos(x/2) * np.cos(y/2) * np.cos(z/2) + np.sin(x/2) * np.sin(y/2) * np.sin(z/2)

    return [qx, qy, qz, qw]