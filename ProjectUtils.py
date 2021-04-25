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
    return np.array([maxx-minx, maxy-miny, maxz-minz])


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


def jointCentroid(vertices, indices=[]):
    # centroid = [0, 0, 0]
    # for index in indices:
    #     centroid = centroid+vertices[index]
    # centroid = centroid/len(indices)
    # print(centroid, "centroid")
    if(len(indices) > 0):
        result = np.average(vertices[indices], axis=0)
    else:
        result = np.average(vertices, axis=0)
    return result


def translateMeshVec(meshA, vector: list):
    for pos in meshA.vertices:
        pos += vector


def matchPoints(a: list, b: list):
    new_a_order = []
    a = np.array(a)
    center_b = np.average(b, axis=0)
    if(len(a) == len(b)):
        for pa in a:
            va = normalizeVector(pa-center_b)
            ind = -1
            maxDot = -2
            for iter, pb in enumerate(b):
                vb = normalizeVector(pb-center_b)
                cDot = va[0]*vb[0]+va[1]*vb[1]+va[2]*vb[2]
                if(cDot > maxDot):
                    maxDot = cDot
                    ind = iter
            new_a_order.append(ind)
    # print('a', a)
    # print('new_order', new_a_order)
    a += a[new_a_order]-a
    return a


def icpalign(new, old):
    trans = trimesh.registration.mesh_other(
        new, old, samples=500, scale=True, icp_first=10, icp_final=50)[0]
    new.apply_transform(trans)


def connectJointsBeta(parts):
    partIndices = {'back': -1, 'seat': -1, 'leg': -1, 'arm rest': -1}
    jointCenters = {'back': {'back': [], 'seat': [], 'leg': [], 'arm rest': []}, 'seat': {'back': [], 'seat': [], 'leg': [], 'arm rest': [
    ]}, 'leg': {'back': [], 'seat': [], 'leg': [], 'arm rest': []}, 'arm rest': {'back': [], 'seat': [], 'leg': [], 'arm rest': []}}

    for iter, part in enumerate(parts):
        partIndices[part.label] = iter

    for part in parts:
        for label, indices in part.joints:
            # if(part.label == 'leg' or label == 'leg'):
            centroid = jointCentroid(part.mesh.vertices, indices)
            jointCenters[part.label][label].append(centroid)

    labels = ['back', 'seat', 'leg', 'arm rest']
    labels2 = ['back', 'seat', 'leg', 'arm rest']
    # print(jointCenters)
    if(len(jointCenters['leg']['seat']) == len(jointCenters['seat']['leg']) and len(jointCenters['leg']['seat']) > 2):
        label = 'leg'
        label2 = 'seat'
        toMove = jointCenters['leg']['seat']
        toMoveExt = jointExtents(toMove)
        toMatch = jointCenters['seat']['leg']
        toMatchExt = jointExtents(toMatch)
        legScale = trimesh.transformations.scale_matrix(
            1, [0, 0, 0])
        legScale[0, 0] = toMatchExt[0]/toMoveExt[0]
        # legScale[1, 1] = toMatchExt[1]/toMoveExt[1]
        legScale[2, 2] = min(2, toMatchExt[2]/toMoveExt[2])
        destination = np.average(toMatch, axis=0)
        origin = np.average(toMove, axis=0)
        parts[partIndices['leg']].mesh.vertices -= origin
        # print("transformed ", label, " to match ", label2)
        parts[partIndices['leg']].mesh.apply_transform(legScale)
        parts[partIndices['leg']].mesh.vertices += destination
    else:
        label = 'leg'
        label2 = 'seat'
        legBounds = parts[partIndices['leg']].mesh.bounds
        legExtents = legBounds[1]-legBounds[0]
        seatBounds = parts[partIndices['seat']].mesh.bounds
        seatExtents = seatBounds[1]-seatBounds[0]
        origin = parts[partIndices['leg']].mesh.centroid
        if(len(jointCenters['leg']['seat']) > 2):
            toMove = jointCenters['leg']['seat']
            toMoveExt = jointExtents(toMove)
            legExtents = toMoveExt
            origin = jointCentroid(toMove)
        legScale = trimesh.transformations.scale_matrix(
            1, [0, 0, 0])
        legScale[0, 0] = min(2, seatExtents[0]/legExtents[0])
        # legScale[1, 1] = toMatchExt[1]/toMoveExt[1]
        legScale[2, 2] = min(2, seatExtents[2]/legExtents[2])

        destination = parts[partIndices['seat']].mesh.centroid

        parts[partIndices['leg']].mesh.vertices -= origin
        parts[partIndices['leg']].mesh.apply_transform(legScale)

        destination = [destination[0], origin[1] + seatBounds[0][1] -
                       legBounds[1][1], seatBounds[0][2]-parts[partIndices['leg']].mesh.bounds[0][2]]
        parts[partIndices['leg']].mesh.vertices += destination
        # print("transformed ", label, " to match ", label2, "with default method")
    if(len(jointCenters['back']['seat']) > 0 and len(jointCenters['seat']['back']) > 0):
        # JOINING SEATS TO BACKS
        label='back'
        label2='seat'
        seatBounds=parts[partIndices['seat']].mesh.bounds
        toMove=jointCenters['back']['seat']
        toMoveExt=jointExtents(toMove)
        backBounds=parts[partIndices['back']].mesh.bounds
        toMatch=jointCenters['seat']['back']
        toMatchExt=jointExtents(toMatch)
        if toMoveExt[0] == 0:
            toMoveExt[0]=1
            toMatchExt[0]=1
        if(toMatchExt[0] < .1):
            toMatchExt[0]=seatBounds[1][0]-seatBounds[0][0]

        if toMoveExt[2] < .05:
            toMoveExt[2]=1
            toMatchExt[2]=1
        if(toMatchExt[0] < .01):
            toMoveExt[0]=1
            toMatchExt[0]=1
        if(toMatchExt[2] < .01):
            toMoveExt[2]=1
            toMatchExt[2]=1

        backScale=trimesh.transformations.scale_matrix(
            1, [0, 0, 0])
        backScale[0, 0] = toMatchExt[0]/toMoveExt[0]
        if(backScale[0, 0] < .05):
            backScale[0, 0] = .5
        # if(toMoveExt[1] > toMatchExt[1] and toMatchExt[1] > 0.05):
        #     backScale[1, 1] = toMatchExt[1]/toMoveExt[1]
        backScale[2, 2] = toMatchExt[2]/toMoveExt[2]
        if(backScale[2, 2] < .05):
            backScale[2, 2] = .5
        destination = np.average(toMatch, axis=0)
        origin = np.average(toMove, axis=0)
        parts[partIndices['back']].mesh.vertices -= origin
        # print("transformed ", label, " to match ", label2)
        parts[partIndices['back']].mesh.apply_transform(backScale)
        parts[partIndices['back']].mesh.vertices += [origin[0],
                                                     destination[1], destination[2]]
        parts[partIndices['back']].mesh.vertices += [0, (parts[partIndices['seat']
                                                               ].mesh.bounds[1][1]-parts[partIndices['back']].mesh.bounds[0][1])/2, 0]
        for v in parts[partIndices['back']].mesh.vertices:
            v[0] = min(v[0], seatBounds[1][0]+.05)
            v[0] = max(v[0], seatBounds[0][0]-.05)
    else:
        label = 'back'
        label2 = 'seat'
        seatBounds = parts[partIndices['seat']].mesh.bounds
        seatBounds = seatBounds[1]-seatBounds[0]
        seatCenter = parts[partIndices['seat']].mesh.centroid
        backBounds = parts[partIndices['back']].mesh.bounds
        backBounds = backBounds[1]-backBounds[0]
        backCenter = parts[partIndices['back']].mesh.centroid

        backScale = trimesh.transformations.scale_matrix(
            1, [0, 0, 0])
        backScale[0, 0] = seatBounds[0]/backBounds[0]
        parts[partIndices['back']].mesh.vertices -= backCenter
        parts[partIndices['back']].mesh.apply_transform(backScale)
        parts[partIndices['back']].mesh.vertices += backCenter
        back_maxz = backCenter[2]+backBounds[2]/2
        seat_minz = seatCenter[2]-seatBounds[2]/2
        parts[partIndices['back']].mesh.vertices += [0,
                                                     0, seat_minz-back_maxz+.05]
        if(len(jointCenters['back']['seat']) > 0):
            for label, indices in parts[partIndices['back']].joints:
                if(label == 'back'):
                    toMove = jointCenters['back']['seat']
                    toMoveExt = jointExtents(
                        parts[partIndices['back']].mesh.vertices[indices])
                    backjointmaxy = toMove[1]+toMoveExt[1]/2
                    seat_maxy = seatCenter[1]-seatBounds[1]/2
                    parts[partIndices['back']].mesh.vertices += [0,
                                                                 seat_maxy-backjointmaxy, 0]
                    break

    if(len(jointCenters['arm rest']['back']) > 1 and len(jointCenters['back']['arm rest']) > 1):
        label = 'arm rest'
        label2 = 'back'
        toMove = jointCenters[label][label2]
        toMoveExt = jointExtents(toMove)
        toMatch = jointCenters[label2][label]
        toMatchExt = jointExtents(toMatch)
        armScale = trimesh.transformations.scale_matrix(
            1, [0, 0, 0])
        armScale[0, 0] = toMatchExt[0]/toMoveExt[0]

        armCenter = parts[partIndices['arm rest']].mesh.centroid
        parts[partIndices['arm rest']].mesh.vertices -= armCenter
        parts[partIndices['arm rest']].mesh.apply_transform(armScale)
        dest = [armCenter[0], np.average(toMatch, axis=0)[1], armCenter[2]]
        parts[partIndices['arm rest']].mesh.vertices += dest
    # MISSING Default armrest movement?
    if(len(jointCenters['arm rest']['seat']) > 1 and len(jointCenters['seat']['arm rest']) > 1):
        label = 'arm rest'
        label2 = 'seat'
        toMove = jointCenters[label][label2]
        toMoveExt = jointExtents(toMove)
        toMatch = jointCenters[label2][label]
        toMatchExt = jointExtents(toMatch)
        armScale = trimesh.transformations.scale_matrix(
            1, [0, 0, 0])
        armScale[0, 0] = toMatchExt[0]/toMoveExt[0]
        armBounds = parts[partIndices['arm rest']].mesh.bounds
        seatBounds = parts[partIndices['seat']].mesh.bounds
        armScale[1, 1] = (seatBounds[0][1]-armBounds[1][1]) / \
            (armBounds[0][1]-armBounds[1][1])
        armScale[2, 2] = (seatBounds[1][2]-seatBounds[0][2]) / \
            (armBounds[1][2]-armBounds[0][2])
        armCenter = parts[partIndices['arm rest']].mesh.centroid
        parts[partIndices['arm rest']].mesh.vertices -= armCenter
        parts[partIndices['arm rest']].mesh.apply_transform(armScale)
        armBounds = parts[partIndices['arm rest']].mesh.bounds
        seatBounds = parts[partIndices['seat']].mesh.bounds
        parts[partIndices['arm rest']].mesh.vertices += [armCenter[0],
                                                         seatBounds[0][1]-armBounds[0][1], armCenter[2]]
    # otherwise should scale arm rest so that minimum armrest y value is same as minimum seat y value
    # MISSING
    # make sure arm-rest is mostly above seat if no joints : defaults for arm?
    # leg-arm/arm-leg Probably do leg->arm
    #

    # attempt to fill holes
    for part in parts:
        for label, indices in part.joints:
            if(len(indices) > 4):
                centroid = jointCentroid(part.mesh.vertices, indices)
                toTriangulate = np.array(part.mesh.vertices[indices])
                # print('point 0')
                # print(toTriangulate[0])
                # np.append(toTriangulate, centroid)
                try:
                    triangulation = trimesh.PointCloud(
                        toTriangulate).convex_hull
                    triangulation.vertices, triangulation.faces = trimesh.remesh.subdivide(
                        triangulation.vertices, triangulation.faces)
                    triangulation.vertices, triangulation.faces = trimesh.remesh.subdivide(
                        triangulation.vertices, triangulation.faces)
                    triangulation.vertices, triangulation.faces = trimesh.remesh.subdivide(
                        triangulation.vertices, triangulation.faces)
                    part.mesh = trimesh.util.concatenate(
                        part.mesh, triangulation)
                except:
                    continue# print('couldn\'t triangulate joint')
    # attach joints
    bbpartmeshes = []
    for part in parts:
        bbpartmeshes.append(trimesh.convex.convex_hull(
            part.mesh, qhull_options='QbB Pp Qt'))
    partNameorder = ['back', 'leg', 'arm rest']
    # print("start of thingy")
    if(len(jointCenters['arm rest']['leg']) > 0 and len(jointCenters['leg']['arm rest']) == 0):
        for j in parts[partIndices['arm rest']].joints:
            if j[0] == 'leg':
                parts[partIndices['arm rest']].joints.remove(j)
    backlegOK = True
    if(len(jointCenters['back']['leg']) > 0 and len(jointCenters['leg']['back']) == 0):
        backlegOK = False
        # for j in parts[partIndices['back']].joints:
        #     if j[0] == 'leg':
        #         parts[partIndices['back']].joints.remove(j)
    for name in partNameorder:
        part = parts[partIndices[name]]
        translation = [0, 0, 0]
        # print(part.joints)
        for label, indices in part.joints:
            if(backlegOK or name != 'back' or label != 'leg'):
                centroid = jointCentroid(part.mesh.vertices, indices)
                # print(part.label, ' : ', label)
                # print(centroid)
                closest_point = trimesh.proximity.closest_point(
                    parts[partIndices[label]].mesh, [centroid])
                # if(closest_point[1][0] < .2):
                if(name == 'arm rest' and label == 'back' and len(jointCenters['back']['arm rest']) < 1):
                    continue
                closest_point = closest_point[0]
                translation = closest_point[0]-centroid
                dists = part.mesh.vertices-closest_point
                dists = dists*dists
                dists = np.sum(dists, axis=1, keepdims=True)
                part.mesh.vertices += translation * \
                    np.maximum(0, (1-(np.sqrt(dists))))
        # for v in part.mesh.vertices:
        #     v += translation/max(1.0, (vdistancesq(v, centroid)*500))

        #     if(backlegOK or name != 'back' or label != 'leg')):
        #         closest_point=trimesh.proximity.closest_point(
        #             parts[partIndices[label]].mesh, part.mesh.vertices[indices])[0]
        #         part.mesh.vertices[indices]=closest_point

        # arm-back and arm-seat
        # close holes in arm/seat by using part centroid and joint centroid, and move the joint verts to the max dist in the main direction of that vector, for seats maybe just down
        # if(len(jointCenters['back']['seat']) > 0 and len(jointCenters['seat']['back']) > 0):

        #                                             #[origin[0], destination[1], destination[2]]

        # elif(len(jointCenters['leg']['seat']) == len(jointCenters['seat']['leg']) and len(jointCenters['leg']['seat']) == 2):


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
