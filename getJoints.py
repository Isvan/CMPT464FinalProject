import json
import pickle
import trimesh
from os import listdir, mkdir
import re
import concurrent.futures
import numpy as np


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [atoi(c) for c in re.split(r'(\d+)', text)]


def dtoBB2(bb, vert):
    # print(bb)
    bx_min, bx_max = bb[0][0], bb[1][0]
    by_min, by_max = bb[0][1], bb[1][1]
    bz_min, bz_max = bb[0][2], bb[1][2]
    result = []
    for v in vert:
        px = v[0]
        py = v[1]
        pz = v[2]
        dx = max(bx_min - px, 0, px - bx_max)
        dy = max(by_min - py, 0, py - by_max)
        dz = max(bz_min - pz, 0, pz - bz_max)
        result.append(dx*dx + dy*dy + dz*dz)
    result = np.array(result)

    return result  # Math.sqrt(dx*dx + dy*dy +dz*dz)


def findJoints(dataset_path, json_data_path, part_path, part_labels, start, end):
    for datasetIndex in range(start, end+1):

        with open(json_data_path+str(datasetIndex)+'.json') as jsonFile:
            try:
                obJson = json.load(jsonFile)
            except:
                print("error opening json file")
        modelNum = str(obJson['obj'])
        try:
            labelFile = open(part_path+modelNum+'/label.txt')
            obbfText = labelFile.read()
        except:
            obbfText = obJson['obbs']
            obbfText = re.split('L [0-9]*\n', obbfText)[1]
            labelFile = open(part_path+modelNum+'/label.txt', 'x')
            labelFile.write(obbfText)

        obbfText = map(int, obbfText.split('\n'))
        plabels = [pi for pi in obbfText]

        sorted_names = listdir(part_path+modelNum+'/')
        sorted_names.sort(key=natural_keys)
        try:
            with open(dataset_path + "models/joints/"+modelNum,  "rb") as Joint:
                chairJoints = pickle.load(Joint)
        except:

            indivParts = []
            indivhulls = []
            for iter, filename in enumerate(sorted_names):
                if filename.endswith(".obj"):
                    partLabel = part_labels.get(plabels[iter])
                    partTri = trimesh.load(part_path+modelNum+'/'+filename)
                    partTrihull = trimesh.convex.convex_hull(
                        partTri, qhull_options='QbB Pp Qt')
                    indivParts.append((partLabel, partTri))
                    indivhulls.append((partLabel, partTrihull))
            psums = {'back': 0, 'seat': 0, 'leg': 0, 'arm rest': 0}
            chairJoints = {'back': [], 'seat': [], 'leg': [], 'arm rest': []}
            for i in range(len(indivParts)):
                label, part = indivParts[i]
                partJoints = []

                for j in range(len(indivhulls)):
                    olabel, opart = indivhulls[j]
                    curJoint = []
                    if(i != j and olabel != label):
                        bb_dists = dtoBB2(opart.bounds, part.vertices) # get distance from vertices to bounding box of other part
                        cand_vert_indices = np.where(bb_dists < 0.03)[0]
                        cand_verts = part.vertices[cand_vert_indices]
                        if(len(cand_vert_indices) > 0):#use candidate points to find indices of joint vertices
                            curJoint = trimesh.proximity.closest_point(
                                opart, cand_verts)[1]
                            curJoint = np.where(curJoint < .025)[0] 
                            curJoint = cand_vert_indices[curJoint]
                            if(len(curJoint) > 0):
                                curJoint = curJoint+psums[label]
                                partJoints.append((olabel, curJoint))
                psums[label] += len(part.vertices)
                if(len(partJoints) > 0):
                    chairJoints[label] += (partJoints)
            with open(dataset_path + "models/joints/"+modelNum, 'wb') as output:
                pickle.dump(chairJoints, output, pickle.HIGHEST_PROTOCOL)


def main():
    dataset_path = 'dataset/Chair/'
    json_data_path = 'dataset/compiled/'
    part_path = dataset_path + 'models/parts/'
    start = 1
    end = 6200
    offset = 775
    part_labels = {
        0: 'back',
        1: 'seat',
        2: 'leg',
        3: 'arm rest'
    }
    threads = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for i in range(0, 8):
            threads.append(executor.submit(findJoints, dataset_path,
                                           json_data_path, part_path, part_labels, start, start+offset))
            start += offset
            end += offset
        for thread in threads:
            thread.result()


if __name__ == "__main__":
    main()
