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