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


def createOutputFolder(destination, origin, imageIndex, currentIndex):
    if currentIndex % imagesPerChair != imageIndex:
        return

    shutil.copy(origin, destination)


def processSubFolder(subFolder):
    count = 0

    for folderName in folderNames:
        os.makedirs(os.path.join(outputFolder+folderName, subFolder))

    for fileName in progressbar(os.listdir(os.path.join(src, subFolder)), "Trasnfering " + subFolder + " Files"):
        indexCount = 0
        for folderName in folderNames:
            destination = os.path.join(
                outputFolder+folderName, subFolder,  fileName)
            origin = os.path.join(src, subFolder, fileName)
            createOutputFolder(destination, origin,  indexCount, count)
            indexCount += 1
        count += 1


def processEvalData():
    count = 0
    subFolder = "Eval"
    for folderName in folderNames:
        os.makedirs(os.path.join(outputFolder+folderName+"-"+subFolder))

    for fileName in progressbar(os.listdir(os.path.join("../", "evaluate-chairs")), "Trasnfering " + subFolder + " Files"):
        indexCount = 0
        for folderName in folderNames:
            destination = os.path.join(
                outputFolder+folderName+"-"+subFolder,  fileName)
            origin = os.path.join("../", "evaluate-chairs", fileName)
            createOutputFolder(destination, origin,  indexCount, count)
            indexCount += 1
        count += 1


src = "."
outputFolder = os.path.join("ourChairData", "chairs-")
folderNames = ["Front", "Side", "Top"]
imagesPerChair = 3

if(len(folderNames) != imagesPerChair):
    print("MISMATCH BETWEEN FOLDERNAMES AND IMAGES PER CHAIR")

# processSubFolder("positive")
# processSubFolder("negative")
processEvalData()

print("Done formating data!")
