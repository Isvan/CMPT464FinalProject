import trimesh
import pyrender
import re
import io
import sys
import getopt
from optparse import OptionParser
import numpy as np
from os import listdir, mkdir

# https://stackoverflow.com/questions/5967500/how-to-correctly-sort-a-string-with-a-number-inside


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [atoi(c) for c in re.split(r'(\d+)', text)]


def main(argv):
    chairnums = [argv[0]]
    if(argv[1] == 'True'):
        allmodels = listdir('grass-master/Chair/models/')
        allmodels = [re.sub('\.obj', '', m) for m in allmodels]
        chairnums = allmodels
    for modelNum in chairnums:
        f = open('grass-master/Chair/models/'+modelNum+'.obj')
        partPath = 'grass-master/Chair/models/parts/'
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

        chairObj = f.read()
        chair_part_obs = re.split('g \d+', chairObj)
        chair_part_obs.pop(0)
        i = 0
        numv = 0

        try:
            labelFile = open(partPath+modelNum+'/label.txt')
            obbfText = labelFile.read()
        except:
            obbf = open('grass-master/Chair/obbs/'+modelNum+'.obb')
            obbfText = obbf.read()
            obbfText = re.split('L [0-9]*\n', obbfText)[1]
            labelFile = open(partPath+modelNum+'/label.txt', 'x')
            labelFile.write(obbfText)
            obbf.close()

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
                partF.close
                i += 1
            except:
                j += 1
                # print(modelNum + "already separated")
        f.close()

    scene = pyrender.Scene()
    chair_trimesh = []
    meshes = []

    sorted_names = listdir(partPath+modelNum+'/')
    sorted_names.sort(key=natural_keys)
    # print(sorted_names)
    for iter, filename in enumerate(sorted_names):
        if filename.endswith(".obj"):
            thisTri = trimesh.load(partPath+modelNum+'/'+filename)
            thisTri.visual.face_colors = np.full(
                shape=[thisTri.faces.shape[0], 4], fill_value=trimesh.visual.color.hex_to_rgba(part_colors.get(plabels[iter])))
            # print(thisTri.faces.shape)
            chair_trimesh.append(thisTri)
            meshes.append(pyrender.Mesh.from_trimesh(
                chair_trimesh, smooth=False))
    for mesh in meshes:
        scene.add(mesh)
    #camera = pyrender.PerspectiveCamera(yfov=np.pi / 3.0, aspectRatio=1.0)
    #s = np.sqrt(2)/2
    # camera_pose = np.array([[0.0, -s,   s,   0.3],
    #                        [1.0,  0.0, 0.0, 0.0],
    #                        [0.0,  s,   s,   0.35],
    #                        [0.0,  0.0, 0.0, 1.0],
    #                        ])
    #scene.add(camera, pose=camera_pose)
    pyrender.Viewer(scene, use_raymond_lighting=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("please run with model number (example: \"viewModel.py 172\")")
    if len(sys.argv) < 3:
        sys.argv.append('False')
    if len(sys.argv) == 3:
        main(sys.argv[1:])
