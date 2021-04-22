import numpy as np
import pyrender
import random
import trimesh
import math


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
    return scale


def translateMeshAToB(meshA, meshB):
    centroidA = meshA.centroid
    centroidB = meshB.centroid

    translationVector = centroidB - centroidA
    for pos in meshA.vertices:
        pos += translationVector
    return translationVector


def vdistancesq(a, b):
    dsum = 0
    for i in range(3):
        dsum = dsum+(a[i]-b[i])*(a[i]-b[i])
    return dsum


def jointCentroid(vertices, indices):
    centroid = [0, 0, 0]
    for index in indices:
        centroid = centroid+vertices[index]
    centroid = centroid/len(indices)
    return centroid


def translateMeshVec(meshA, vector: list):
    for pos in meshA.vertices:
        pos += vector


def connectJoints(parts):
    # parts = array of parts
    # for each joint from each part, move vertices near joint to point on surface of matching part
    partIndices = {'back': -1, 'seat': -1, 'leg': -1, 'arm rest': -1}
    for iter, part in enumerate(parts):
        partIndices[part.label] = iter
    '''
    #match joints in part with joints from other part
    # ie 4 leg joints go to 4 closest seat joints if too far don't move

    #if no matching joints then move to surface

    # moving
    #       first translate the whole model to make the joint closer
    #                           based on joint centroid
    #       move vertices in the joint to the surface


    joint[0] = label
    joint[1] = array of vertex indices

    seat: leg: [[]]
    '''

    for part in parts:
        if(part.label != 'seat'):
            for joint in part.joints:
                print("joint is: ", joint)
                label = joint[0][0]
                print("label: ", label)
                indices = joint[0][1]
                centroid = jointCentroid(part.mesh.vertices, indices)
                # get all joints from joint label matching part.label
                matchingJoints = []
                centroids = []
                try:
                    for mjoint in parts[partIndices[label]].joints:
                        if mjoint[0][0] == part.label:
                            matchingJoints.append(mjoint)
                            centroids.append(
                                jointCentroid(parts[partIndices[label]].mesh.vertices, mjoint[0][1]))
                except IndexError:
                    print("label is: ", label, "\nindices is: ", partIndices)
                closest = -1
                min_d = 10
                for iter, c in enumerate(centroids):
                    cdist = vdistancesq(centroid, c)
                    if(cdist < min_d and cdist < .002):
                        closest = iter
                        min_d = cdist
                # if(closest > -1):
                #     translateMeshVec(part.mesh, (centroids[closest]-centroid))
                # else:

                closest_point = trimesh.proximity.closest_point(
                    parts[partIndices[label]].mesh, [centroid])[0]
                translation = (closest_point[0]-centroid)
                print("translation vector: ", translation)
                for ind in indices:
                    # thisT = translation / \
                    #     max(1.0,
                    #         (vdistancesq(vertex[ind], location[0])/.05))
                    part.mesh.vertices[ind] += translation
                #translateMeshVec(part.mesh, trans_distance)
            # label = joint[0][0]
            # location = [joint[0][1]]
            # #print("location is:", location, np.shape(location))
            # # location.reshape((3, 1))
            # # print("location is:", location, np.shape(location))

            # if(indices[label] > -1):
            #     pos = trimesh.proximity.closest_point(
            #         parts[indices[label]].mesh, location)[0]
            #     translation = pos[0]-location[0]
            #     for vertex in part.mesh.vertices:
            #         # if(vdistancesq(vertex, location[0]) < .05):
            #         thisT = translation / \
            #             max(1.0,
            #                 (vdistancesq(vertex, location[0])/.05))
            #         vertex += thisT
            #         if(vdistancesq(vertex, pos[0]) < .005):
            #             vertex = trimesh.proximity.closest_point(
            #                 parts[indices[label]].mesh, [vertex])[0][0]

    #part[0].mesh.vertices += (pos-part[0].mesh.vertices)*distance_from_location
    # https://computergraphics.stackexchange.com/questions/8195/how-to-convert-euler-angles-to-quaternions-and-get-the-same-euler-angles-back-fr


def transformJoints(scale, translation, part):
    for joint in part.joints:
        joint[0][1][0] = joint[0][1][0]-part.mesh.centroid[0]
        joint[0][1][1] = joint[0][1][1]-part.mesh.centroid[1]
        joint[0][1][2] = joint[0][1][2]-part.mesh.centroid[2]
        joint[0][1][0] = joint[0][1][0]*scale[0]
        joint[0][1][1] = joint[0][1][1]*scale[1]
        joint[0][1][2] = joint[0][1][2]*scale[2]
        joint[0][1][0] = joint[0][1][0]+part.mesh.centroid[0]
        joint[0][1][1] = joint[0][1][1]+part.mesh.centroid[1]
        joint[0][1][2] = joint[0][1][2]+part.mesh.centroid[2]
        joint[0][1][0] = joint[0][1][0]+translation[0]
        joint[0][1][1] = joint[0][1][1]+translation[1]
        joint[0][1][2] = joint[0][1][2]+translation[2]


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

def randomInt(intA, intB):
    return int(random.randrange(intA, intB))