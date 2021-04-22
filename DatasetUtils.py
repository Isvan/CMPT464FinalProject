import json
import numpy as np
from os import listdir, mkdir
import pyrender
import re
import trimesh
from io import StringIO

# Splits the legs or arm rests by overlaying a "cross" at the centroid
# Produces the meaningful parts (whole leg, whole armrest, etc.) whenever possible


def splitPartMesh(partMesh, partLabel):
    meshes = []

    # always have the grouped version in the collection
    meshes.append((partMesh, 'grouped'))

    if partLabel == 'leg' or partLabel == 'arm rest':
        centroid = partMesh.centroid

        # if plane (1, 0, 0) intersects the mesh at centroid, then don't slice it - mesh is a whole
        lines = trimesh.intersections.mesh_plane(partMesh, (1, 0, 0), centroid)
        isSplitMesh = len(lines) == 0

        if isSplitMesh:
            sideRight = partMesh.slice_plane(centroid, (-1, 0, 0))
            sideLeft = partMesh.slice_plane(centroid, (1, 0, 0))

            # in we have 2 armrests or 2 legs only, we won't be able to split the sideRight and sideLeft furthermore
            # but if we can split, then there must be 4 legs or >2 arm rests
            isSideRightSplitMesh = len(trimesh.intersections.mesh_plane(
                sideRight, (0, 0, 1), sideRight.centroid)) == 0
            if not isSideRightSplitMesh:
                meshes.append((sideRight, 'right'))
            else:
                meshes.append((sideRight.slice_plane(
                    sideRight.centroid, (0, 0, 1)), 'right'))
                meshes.append((sideRight.slice_plane(
                    sideRight.centroid, (0, 0, -1)), 'right'))

            isSideLeftSplitMesh = len(trimesh.intersections.mesh_plane(
                sideLeft, (0, 0, 1), sideLeft.centroid)) == 0
            if not isSideLeftSplitMesh:
                meshes.append((sideLeft, 'left'))
            else:
                meshes.append((sideLeft.slice_plane(
                    sideLeft.centroid, (0, 0, 1)), 'left'))
                meshes.append((sideLeft.slice_plane(
                    sideLeft.centroid, (0, 0, -1)), 'left'))

    return meshes


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [atoi(c) for c in re.split(r'(\d+)', text)]

# index here is an .obj index and NOT the actual dataset index
# output has an array of pyrender.Mesh objects (parts)


def vdistancesq(a, b):
    dsum = 0
    for i in range(3):
        dsum = dsum+(a[i]-b[i])*(a[i]-b[i])
    return dsum


def getDatasetObjParts(datasetIndex):
    json_data_path = 'dataset/compiled/'
    dataset_path = 'dataset/Chair/'

    with open(json_data_path+str(datasetIndex)+'.json') as jsonFile:
        try:
            obJson = json.load(jsonFile)
        except:
            print("error opening json file")

    modelNum = str(obJson['obj'])

    f = open(dataset_path + 'models/'+modelNum+'.obj')
    partPath = dataset_path + 'models/parts/'

    try:
        mkdir(partPath)
        print("created directory for all parts")
    except:
        # print("parts directory exists")
        i = 0

    try:
        mkdir(partPath+modelNum)
        print("created directory for parts of chair"+modelNum)
    except:
        # print("directory for "+modelNum+" exists")
        i = 0

    part_colors = {
        'back': 'd1310a',  # back
        'seat': 'f3c701',  # seat
        'leg': '19d625',  # leg
        'arm rest': '3737d0',  # arm rest
    }

    part_labels = {
        0: 'back',
        1: 'seat',
        2: 'leg',
        3: 'arm rest'
    }

    chairObj = f.read()
    chair_part_obs = re.split('g \d+', chairObj)
    chair_part_obs.pop(0)
    i = 0
    numv = 0

    try:
        labelFile = open(partPath+modelNum+'/label.txt')
        obbfText = labelFile.read()
    except:
        # obbf = open(dataset_path + 'obbs/'+modelNum+'.obb')
        # obbfText = obbf.read()
        obbfText = obJson['obbs']
        obbfText = re.split('L [0-9]*\n', obbfText)[1]
        labelFile = open(partPath+modelNum+'/label.txt', 'x')
        labelFile.write(obbfText)
        # obbf.close()

    obbfText = map(int, obbfText.split('\n'))
    plabels = [pi for pi in obbfText]
    labelFile.close()
    j = 0
    for pind, ob in enumerate(chair_part_obs):
        try:
            partF = open(partPath+modelNum+'/'+str(i)+'.obj', "x")

            if (numv > 0):
                lines = ob.split('\n')
                for lineind, line in enumerate(lines):
                    if(len(line) > 0):
                        if(line.count('f') > 0):
                            subline = line.split(' ')
                            for index, part in enumerate(subline):
                                if part.isnumeric():
                                    newindex = int(part)-numv
                                    subline[index] = str(newindex)
                            lines[lineind] = ' '.join(subline)
                chair_part_obs[pind] = '\n'.join(lines)

            partF.write(chair_part_obs[pind])
            numv += ob.count('v')
            partF.close()
            i += 1
        except:
            j += 1
    f.close()

    parts = []

    sorted_names = listdir(partPath+modelNum+'/')
    sorted_names.sort(key=natural_keys)
    chairParts = {'back': {'text': "", 'vcount': 0}, 'seat': {'text': "", 'vcount': 0}, 'leg': {
        'text': "", 'vcount': 0}, 'arm rest': {'text': "", 'vcount': 0}}
    # for iter, filename in enumerate(sorted_names):
    #     if filename.endswith(".obj"):
    #         partTri = trimesh.load(partPath+modelNum+'/'+filename)
    #         trimesh.repair.fix_normals(partTri, multibody=False)
    #         partLabel = part_labels.get(plabels[iter])

    #         partTri.visual.face_colors = np.full(
    #             shape=[partTri.faces.shape[0], 4], fill_value=trimesh.visual.color.hex_to_rgba(part_colors.get(part_labels[plabels[iter]])))

    #         partMesh = pyrender.Mesh.from_trimesh(partTri, smooth=False)

    #         parts.append((partMesh, partLabel))
    for iter, filename in enumerate(sorted_names):
        if filename.endswith(".obj"):
            pfile = open(partPath+modelNum+'/'+filename)
            partLabel = part_labels.get(plabels[iter])
            lines = pfile.read().split('\n')
            for lineind, line in enumerate(lines):
                if(len(line) > 0):
                    if(line.count('f') > 0):
                        subline = line.split(' ')
                        for index, part in enumerate(subline):
                            if part.isnumeric():
                                newindex = int(
                                    part)+int(chairParts[partLabel]['vcount'])
                                subline[index] = str(newindex)
                        lines[lineind] = ' '.join(subline)

            joinedlines = '\n'.join(lines)
            chairParts[partLabel]['text'] = chairParts[partLabel]['text']+joinedlines
            chairParts[partLabel]['vcount'] = chairParts[partLabel]['text'].count(
                'v')
            pfile.close()
    indivParts = []
    for iter, filename in enumerate(sorted_names):
        if filename.endswith(".obj"):
            partLabel = part_labels.get(plabels[iter])
            # pfile = open(partPath+modelNum+'/'+filename)
            partTri = trimesh.load(partPath+modelNum+'/'+filename)
            partTri = trimesh.convex.convex_hull(
                partTri, qhull_options='QbB Pp Qt')
            indivParts.append((partLabel, partTri))
    psums = {'back': 0, 'seat': 0, 'leg': 0, 'arm rest': 0}
    chairJoints = {'back': [], 'seat': [], 'leg': [], 'arm rest': []}
    for label, part in indivParts:
        partJoints = []
        for olabel, opart in indivParts:
            curJoint = []
            if(olabel != label):

                # This needs to be multithreaded
                # for iter, vertex in enumerate(part.vertices):
                #     dist = trimesh.proximity.closest_point(
                #         opart, part.vertices)[1]
                #     if(dist < threshold):
                #        curJoint.append(iter+psums[label])
                # end of multithreading
                # curJoint = [index0,index1........]
                curJoint = trimesh.proximity.closest_point(
                    opart, part.vertices)[1]
                curJoint = np.where(curJoint < .005)[0]

                if(len(curJoint) > 0):
                    partJoints.append((olabel, curJoint))
                    # print(partJoints)
        psums[label] += len(part.vertices)
        if(len(partJoints) > 0):
            chairJoints[label].append(partJoints)
    print(chairJoints)

    for part in chairParts:
        if(len(chairParts[part]['text']) > 0):
            partTri = trimesh.load(
                StringIO(chairParts[part]['text']), file_type='obj')
            if(part != 'seat'):  # (part == 'leg' or part == 'arm rest'):
                trimesh.repair.fix_normals(partTri)

            meshes = splitPartMesh(partTri, part)  # part is label
            for body, side in meshes:
                body.visual.face_colors = np.full(
                    shape=[body.faces.shape[0], 4], fill_value=trimesh.visual.color.hex_to_rgba(part_colors[part]))
                # trimesh.repair.broken_faces(
                #     body, color=trimesh.visual.color.hex_to_rgba("fd00f9"))
                # body = trimesh.convex.convex_hull(
                #     body, qhull_options='QbB Pp Qt')
                parts.append((body, side, part, chairJoints[part]))

    return parts


def getDatasetMeshObjIndex(datasetIndex):
    meshData = open('grass_dataset_viewer/Compiled-data/'+datasetIndex+'.json')
    meshJsonString = meshData.read()
    meshJson = json.loads(meshJsonString)
    return int(meshJson['obj'])
