import os
import sys
import shutil


# https://stackoverflow.com/questions/3160699/python-progress-bar
# Code for progress bar as it can take a while and I want some sort of visual that its working
def progressbar(it, prefix="", size=60, file=sys.stdout):
    count = len(it)

    def show(j):
        x = int(size*j/count)
        file.write("%s[%s%s] %i/%i\r" %
                   (prefix, "#"*x, "."*(size-x), j, count))
        file.flush()
    show(0)
    for i, item in enumerate(it):
        yield item
        show(i+1)
    file.write("\n")
    file.flush()


def stageData(folderName):
    folderPath = os.path.join(".", folderName)
    totalSize = len(os.listdir((folderPath)))
    amountToPad = len(str(totalSize))
    count = 1

    for filename in progressbar((os.listdir(os.path.join(".", folderName))), "Staging data in " + folderName):
        newStr = str(count)
        numLen = len(newStr)
        for i in range(amountToPad-numLen):
            newStr = "0" + newStr

        os.rename(os.path.join(folderPath, filename),
                  os.path.join(folderPath, "s"+newStr+"."+filename.split(".")[1]))

        count += 1


def mergeData(folderName):
    # Pad all non staged data
    padData(folderName)
    folderPath = os.path.join(".", folderName)
    totalSize = len(os.listdir((folderPath)))
    amountToPad = len(str(totalSize))
    count = 1
    # Now iterate over staged and non-staged data and merge them
    for filename in progressbar((os.listdir(folderPath)), "Merging data in " + folderName):
        newStr = str(count)
        numLen = len(newStr)
        for i in range(amountToPad-numLen):
            newStr = "0" + newStr

        os.rename(os.path.join(folderPath, filename),
                  os.path.join(folderPath, newStr+"."+filename.split(".")[1]))

        count += 1


def padData(folderName):
    folderPath = os.path.join(".", folderName)
    totalSize = len(os.listdir((folderPath)))
    amountToPad = len(str(totalSize))
    for filename in progressbar((os.listdir(folderPath)), "Padding data in " + folderName):
        strNum = filename.split(".")[0]
        if "s" in strNum:
            continue
        strType = filename.split(".")[1]
        numLen = len(strNum)
        newStr = strNum
        for i in range(amountToPad-numLen):
            newStr = "0" + newStr

        os.rename(os.path.join(folderPath, filename),
                  os.path.join(folderPath, newStr+"."+strType))


src = "."
imagesPerChair = 3

tokens = sys.argv[1:]

if len(tokens) <= 0:
    print('-s : Stage Data to be merged in')
    print('-m : Merge Data together')
    print('-p : Pad Data')
    quit()

if '-p' in tokens:
    padData("negative")
    padData("positive")
    print("Done padding data you can now stage")
    quit()

if '-s' in tokens:
    stageData("positive")
    stageData("negative")
    print("Done staging data you can now merge")
    quit()

if '-m' in tokens:
    mergeData("negative")
    mergeData("positive")
    quit()
