import json
import numpy as np
from os import listdir, mkdir, makedirs, path
import pyrender
import re
import trimesh
from io import StringIO
import pickle
from getJoints import findJoints, dtoBB2

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


def getDatasetObjIndex(datasetIndex):
    json_data_path = 'dataset/compiled/'
    dataset_path = 'dataset/Chair/'

    with open(json_data_path+str(datasetIndex)+'.json') as jsonFile:
        try:
            obJson = json.load(jsonFile)
        except:
            print("error opening json file")

    modelNum = str(obJson['obj'])
    return modelNum


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

    # ensure that directory always exists
    directory = path.dirname(dataset_path + "models/joints/")
    if not path.exists(directory):
        makedirs(directory)

    try:
        with open(dataset_path + "models/joints/"+modelNum,  "rb") as Joint:
            chairJoints = pickle.load(Joint)
    except:
        findJoints(dataset_path, json_data_path, partPath,
                   part_labels, atoi(datasetIndex), atoi(datasetIndex))
        with open(dataset_path + "models/joints/"+modelNum,  "rb") as Joint:
            chairJoints = pickle.load(Joint)

    part_arrays = {'back': [], 'seat': [], 'arm rest': [], 'leg': []}
    for iter, filename in enumerate(sorted_names):
        if filename.endswith(".obj"):
            partLabel = part_labels.get(plabels[iter])
            # pfile = open(partPath+modelNum+'/'+filename)
            partTri = trimesh.load(partPath+modelNum+'/'+filename)
            if(partLabel != 'seat'):  # (part == 'leg' or part == 'arm rest'):
                trimesh.repair.fix_normals(partTri)
            part_arrays[partLabel].append(partTri)

    for key in part_arrays.keys():
        if len(part_arrays[key]) > 0:
            thismesh = trimesh.util.concatenate(
                trimesh.base.Trimesh(), part_arrays[key])
            thismesh.visual.face_colors = np.full(
                shape=[thismesh.faces.shape[0], 4], fill_value=trimesh.visual.color.hex_to_rgba(part_colors[key]))
            if(key != 'seat'):
                trimesh.repair.fix_normals(thismesh)
            parts.append((thismesh, 'grouped', key, chairJoints[key]))

    return parts


def getDatasetMeshObjIndex(datasetIndex):
    meshData = open('grass_dataset_viewer/Compiled-data/'+datasetIndex+'.json')
    meshJsonString = meshData.read()
    meshJson = json.loads(meshJsonString)
    return int(meshJson['obj'])
