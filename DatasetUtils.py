import json
import numpy as np
from os import listdir, mkdir
import pyrender
import re
import trimesh


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
        print("parts directory exists")

    try:
        mkdir(partPath+modelNum)
        print("created directory for parts of chair"+modelNum)
    except:
        print("directory for "+modelNum+" exists")

    part_colors = {
        0: 'd1310a',  # back
        1: 'f3c701',  # seat
        2: '19d625',  # leg
        3: '3737d0',  # arm rest
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
        #obbf = open(dataset_path + 'obbs/'+modelNum+'.obb')
        #obbfText = obbf.read()
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
    for iter, filename in enumerate(sorted_names):
        if filename.endswith(".obj"):
            partTri = trimesh.load(partPath+modelNum+'/'+filename)
            partLabel = part_labels.get(plabels[iter])

            partTri.visual.face_colors = np.full(
                shape=[partTri.faces.shape[0], 4], fill_value=trimesh.visual.color.hex_to_rgba(part_colors.get(plabels[iter])))

            partMesh = pyrender.Mesh.from_trimesh(partTri, smooth=False)
            parts.append((partMesh, partLabel))

    return parts


def getDatasetMeshObjIndex(datasetIndex):
    meshData = open('grass_dataset_viewer/Compiled-data/'+datasetIndex+'.json')
    meshJsonString = meshData.read()
    meshJson = json.loads(meshJsonString)
    return int(meshJson['obj'])
