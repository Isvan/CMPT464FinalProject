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


def jointExtents(vertices):
    minx, maxx = vertices[0][0], vertices[0][0]
    miny, maxy = vertices[0][1], vertices[0][1]
    minz, maxz = vertices[0][2], vertices[0][2]
    for v in vertices:
        minx = min(minx, v[0])
        maxx = max(maxx, v[0])

        miny = min(miny, v[1])
        maxy = max(maxy, v[1])

        minz = min(minz, v[2])
        maxz = max(maxz, v[2])
    return [maxx-minx, maxy-miny, maxz-minz]


def vdistancesq(a, b):
    dsum = 0
    for i in range(3):
        dsum = dsum+(a[i]-b[i])*(a[i]-b[i])
    return dsum


def vdistancesql(inp, b):
    result = []
    for a in inp:
        dsum = 0
        for i in range(3):
            dsum = dsum+(a[i]-b[i])*(a[i]-b[i])
        dsum = dsum/.0025
        if(dsum < 1):
            dsum = 1
        dsum = math.sqrt(dsum)
        result.append([dsum, dsum, dsum])

    return np.array(result)


def jointCentroid(vertices, indices):
    # centroid = [0, 0, 0]
    # for index in indices:
    #     centroid = centroid+vertices[index]
    # centroid = centroid/len(indices)
    # print(centroid, "centroid")

    return np.average(vertices[indices], axis=0)


def translateMeshVec(meshA, vector: list):
    for pos in meshA.vertices:
        pos += vector


def connectJoints(parts):
    # parts = array of parts
    # for each joint from each part, move vertices near joint to point on surface of matching part
    partIndices = {'back': -1, 'seat': -1, 'leg': -1, 'arm rest': -1}
    threshold = 0.1
    for iter, part in enumerate(parts):
        partIndices[part.label] = iter
    bbpartmeshes = []
    for part in parts:
        bbpartmeshes.append(trimesh.convex.convex_hull(
            part.mesh, qhull_options='QbB Pp Qt'))

    '''
    # match joints in part with joints from other part
    # ie 4 leg joints go to 4 closest seat joints if too far don't move

    # if no matching joints then move to surface

    # moving
    #       first translate the whole model to make the joint closer
    #                           based on joint centroid
    #       move vertices in the joint to the surface


    joint[0] = label
    joint[1] = array of vertex indices

    seat: leg: [[]]
    '''
    partNameorder = ['arm rest', 'leg', 'back', 'seat']
    if(True):
        for name in partNameorder:
            part = parts[partIndices[name]]
            translation = [0, 0, 0]
            for label, indices in part.joints:

                centroid = jointCentroid(part.mesh.vertices, indices)
                # get all joints from joint label matching part.label
                matchingJoints = []
                centroids = []
                try:
                    for mlabel, mindices in parts[partIndices[label]].joints:
                        if mlabel == part.label:
                            matchingJoints.append((mlabel, mindices))
                            centroids.append(
                                jointCentroid(parts[partIndices[label]].mesh.vertices, mindices))
                except IndexError:
                    print("label is: ", label,
                          "\nindices is: ", partIndices)
                closest = -1
                min_d = 10
                for iter, c in enumerate(centroids):
                    cdist = vdistancesq(centroid, c)
                    if(cdist < min_d and cdist < .05):
                        closest = iter
                        min_d = cdist
                if(closest > -1):
                    translation = (centroids[closest] -
                                   centroid)

                else:
                    closest_point = trimesh.proximity.closest_point(
                        bbpartmeshes[partIndices[label]], [centroid])[0]
                    translation = (closest_point[0] - centroid)
                part.mesh.vertices += translation / \
                    np.maximum([1.0, 1.0, 1.0], (vdistancesql(
                        part.mesh.vertices, centroid)))

                #     closest_point = trimesh.proximity.closest_point(
                #         parts[partIndices[label]].mesh, [centroid])[0]
                #     translation += (closest_point[0] -
                #                     centroid)
                # translateMeshVec(part.mesh, translation)

            # move vertices based on distance from centroid
            # for label, indices in part.joints:
            #     centroid = jointCentroid(part.mesh.vertices, indices)
            #     if partIndices[label] > -1:
            #         closest_point = trimesh.proximity.closest_point(
            #             parts[partIndices[label]].mesh, [centroid])[0][0]

            #         for v in part.mesh.vertices:
            #             v += (closest_point-v) / \
            #                 max(1.0, (vdistancesq(v, centroid)*1000))

    for i in range(0, 1):
        for name in partNameorder:
            part = parts[partIndices[name]]
            for label, indices in part.joints:

                # for ind in indices:
                closest_point_info = trimesh.proximity.closest_point(
                    bbpartmeshes[partIndices[label]], part.mesh.vertices[indices])
                closest_point = closest_point_info[0]
                cp_dist = closest_point_info[1]
                newind = np.where(cp_dist < threshold)[0]
                closest_point = closest_point[newind]
                cp_dist = indices[newind]
                part.mesh.vertices[cp_dist] = closest_point
                # if(cp_dist < threshold/20):
                #     mask = np.ones(len(part.mesh.vertices), np.bool)
                #     mask[indices] = 0
                #     for v in part.mesh.vertices[mask]:
                #         v += (closest_point-v)/max(
                #             1.0, (vdistancesq(v, closest_point)*1000))
                # if(cp_dist < threshold):

    for part in parts:
        for label, indices in part.joints:
            if partIndices[label] < 0:
                centroid = jointCentroid(part.mesh.vertices, indices)
                jointExts = jointExtents(part.mesh.vertices[indices])
                if max(jointExts) == jointExts[0]:
                    ind1 = 1
                    ind2 = 2
                if max(jointExts) == jointExts[1]:
                    ind1 = 0
                    ind2 = 2
                if max(jointExts) == jointExts[2]:
                    ind1 = 0
                    ind2 = 1
                for ind in indices:
                    part.mesh.vertices[ind][ind1] = centroid[ind1]
                    part.mesh.vertices[ind][ind2] = centroid[ind2]
            elif label == 'seat':
                centroid = jointCentroid(part.mesh.vertices, indices)
                jointExts = jointExtents(part.mesh.vertices[indices])
                if max(jointExts) == jointExts[0]:
                    ind1 = 1
                    ind2 = 2
                if max(jointExts) == jointExts[1]:
                    ind1 = 0
                    ind2 = 2
                if max(jointExts) == jointExts[2]:
                    ind1 = 0
                    ind2 = 1
                closest_point_info = trimesh.proximity.closest_point(
                    parts[partIndices[label]].mesh, part.mesh.vertices[indices])
                for iter, ind in enumerate(indices):

                    closest_point = closest_point_info[0][iter]
                    cp_dist = closest_point_info[1][iter]
                    # if cp_dist > threshold:
                    part.mesh.vertices[ind] = closest_point
                    # for thisind in indices:
                    # part.mesh.vertices[ind][ind1] = centroid[ind1]
                    # part.mesh.vertices[ind][ind2] = centroid[ind2]
                    # break

    # for part in parts:
    #     # result = trimesh.remesh.subdivide(
    #     #     part.mesh.vertices, part.mesh.faces)
    #     # part.mesh.vertices = result[0]
    #     # part.mesh.faces = result[1]
    #     trimesh.smoothing.filter_humphrey(part.mesh, iterations=2)


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
