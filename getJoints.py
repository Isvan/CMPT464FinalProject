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
                    # pfile = open(part_path+modelNum+'/'+filename)
                    partTri = trimesh.load(part_path+modelNum+'/'+filename)
                    partTrihull = trimesh.convex.convex_hull(
                        partTri, qhull_options='QbB Pp Qt')
                    indivParts.append((partLabel, partTri))
                    indivhulls.append((partLabel, partTrihull))
            psums = {'back': 0, 'seat': 0, 'leg': 0, 'arm rest': 0}
            chairJoints = {'back': [], 'seat': [], 'leg': [], 'arm rest': []}
            for label, part in indivParts:
                partJoints = []
                for olabel, opart in indivhulls:
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
                        # consider iterating through vertices in part to get the indices properly ie if if v==curjoint then append that index to joint....
                        # print(part.vertices[curJoint])
                        if(len(curJoint) > 0):
                            curJoint = curJoint+psums[label]
                            partJoints.append((olabel, curJoint))
                            # print(partJoints)
                psums[label] += len(part.vertices)
                # print(psums)
                if(len(partJoints) > 0):
                    chairJoints[label].append(partJoints)
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
        # f1 = executor.submit(findJoints, dataset_path,
        #                      json_data_path, part_path, part_labels, 1, 8)
        # f2 = executor.submit(findJoints, dataset_path,
        #                       json_data_path, part_path, part_labels, 3, 4)
        # f3 = executor.submit(findJoints, dataset_path,
        #                       json_data_path, part_path, part_labels, 5, 6)
        # f4 = executor.submit(findJoints, dataset_path,
        #                       json_data_path, part_path, part_labels, 7, 8)
        # f1.result()
        # f2.result()
        # f3.result()
        # f4.result()


if __name__ == "__main__":
    main()
