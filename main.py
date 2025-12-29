import pyautogui
import autoit # according to a stackoverflow post, this might help make it work? "you have to use pyautoit to make it work inside of roblox" 
import os
import shutil
import math
from pynput import mouse
from pynput import keyboard
import time
from PIL import Image, ImageDraw
# constants
inputDirectory = "./input/"
outputDirectory = "./rendered/"
testDisableLoading = False
clickSpeed: int = 2 # from testing, values below two cause pixels to be double clicked, but if this happens on two, increase until it works
startKey = "G"
stopKey = "C"
polePositionSetKey = "F"

# file list
if not os.path.exists(inputDirectory):
    os.makedirs(inputDirectory)
if not os.path.exists(outputDirectory):
    os.makedirs(outputDirectory)
files = os.listdir(inputDirectory)
totalFiles = len(files)

renderedFrameFiles = os.listdir(outputDirectory)
renderedFiles = len(renderedFrameFiles)
startFrame = 0

# checks
if totalFiles == 0:
    print("Input directory is empty.")
    os._exit(1)
if renderedFiles != 0:
    importFiles = input("Files are already in the output directory. Would you like to continue from the last rendered frame? (Y/N) ")
    if importFiles.upper() == "Y":
        startFrame = renderedFiles
    else:
        clearFiles = ""
        while True:
            clearFiles = input("Clear the output? (Y/N) ")
            if clearFiles.upper() == "Y":
                shutil.rmtree(outputDirectory)
                os.mkdir(outputDirectory)
                break
            elif clearFiles.upper() == "N":
                break

# video metadata
image = Image.open(inputDirectory+files[1],"r") # read dimensions()
width, height = image.size

# helper functions
def mean(tuple):
    return sum(tuple)/len(tuple)

# video functions   
videoFramesProcessed = []
def createFrame(fileName):
    image = Image.open(inputDirectory+fileName,"r")
    pixels = list(image.getdata())
    frame = [False]*width*height
    for index in range(len(pixels)):
        brightness = mean(pixels[index])
        if brightness > 128:
            frame[index] = True
    videoFramesProcessed.append(frame)
    
def printFrame(frame):
    output = ""
    index = 0
    for value in frame:
        if value:
            output += "\x1b[107m1"
        else:
            output += "\x1b[40m0"
        index += 1
        if index % width == 0:
            output += "\x1b[0m\n"
    print(output)

# load input data
if not testDisableLoading:
    startTime = time.time()
    for index in range(totalFiles):
        createFrame(files[index])
        timeElapsed = time.time()-startTime
        fullTimeGuess = timeElapsed/(index/totalFiles+0.01)
        print(f"\rFrames processed: {index+1}/{totalFiles}, ETA {round(fullTimeGuess-timeElapsed,2)}s",end="")
    print(f"\rFinished processing all {totalFiles} files in {round(time.time()-startTime, 2)}s")
else:
    print("Finished processing 0 files in 0.00s (loading skipped)")

# time estimation
print("Estimating render time...", end="\r")
lastProcessedFrame = [False]*width*height
pixelDiffs = 0
for index in range(totalFiles):
    frame = videoFramesProcessed[index]
    if index < startFrame:
        continue
    for index in range(len(frame)):
        if frame[index] == lastProcessedFrame[index]:
            continue
        pixelDiffs += 1
    lastProcessedFrame = frame
pixelDiffs /= 12 # only accurate if speed is 2
pixelDiffs += totalFiles*(2/60+1/12)
pixelDiffs *= 1.7 # fudge factor, more closely matches how long it took to render bad apple
print(f"Render time estimation: ~{round(pixelDiffs//3600)}h {round(pixelDiffs//60 % 60)}m {round(pixelDiffs%1)}s")

# notices
print(f"Press {startKey} to start movement")
print(f"Press {polePositionSetKey} to set the position of the power pole")
print(f"Press {stopKey} to terminate the program") # don't let bad stuff happen if it goes out of control


# handle keyboard input
started = False
polePositionSelected = False
dualPoleMode = False
keyboardController = keyboard.Controller()
mouseController = mouse.Controller()
# why do i have to account for casing...
keyboardStartKeyLower = keyboard.KeyCode.from_char(startKey.lower())
keyboardStartKeyUpper = keyboard.KeyCode.from_char(startKey.upper())
keyboardStopKeyLower = keyboard.KeyCode.from_char(stopKey.lower())
keyboardStopKeyUpper = keyboard.KeyCode.from_char(stopKey.upper())
polePositionSetKeyLower = keyboard.KeyCode.from_char(polePositionSetKey.lower())
polePositionSetKeyUpper = keyboard.KeyCode.from_char(polePositionSetKey.upper())
polePosition = []
upperPolePosition = []
lowerPolePosition = []
def onPress(key):
    global started, polePosition, lowerPolePosition, upperPolePosition, polePositionSelected, dualPoleMode
    if key == keyboardStartKeyLower or key == keyboardStartKeyUpper:
        started = True
    elif key == keyboardStopKeyLower or key == keyboardStopKeyUpper:
        keyboardController.release(keyboard.Key.shift_l)
        os._exit(1)
    elif key == polePositionSetKeyLower or key == polePositionSetKeyUpper:
        polePosition = [mouseController.position[0],mouseController.position[1]]
        if polePosition[1] < pyautogui.size()[1]/2:
            upperPolePosition = polePosition
        else:
            lowerPolePosition = polePosition
        polePositionSelected = True
        if lowerPolePosition and upperPolePosition:
            dualPoleMode = True
            print("Dual pole mode activated.")

    
keyboardListener = keyboard.Listener(
    on_press=onPress
)
keyboardListener.start()
while not started:
    time.sleep(1/60)

# four corners of the display
topLeft = []
topRight = []
bottomLeft = []
bottomRight = []

screenshot = pyautogui.screenshot("searchedImage.png")
screenWidth, screenHeight = screenshot.size

biggestXPixel = 0
smallestXPixel = math.inf
biggestYPixel = 0
smallestYPixel = math.inf

for y in range(screenHeight):
    for x in range(screenWidth):
        brightness = mean(screenshot.getpixel((x,y)))
        # this magic number came from the brightness of the chrome ui, which is ~28
        if brightness <= 248:
            continue
        if x < smallestXPixel:
            smallestXPixel = x
        if x > biggestXPixel:
            biggestXPixel = x
        if y < smallestYPixel:
            smallestYPixel = y
        if y > biggestYPixel:
            biggestYPixel = y
topLeft = [smallestXPixel,smallestYPixel]
topRight = [biggestXPixel,smallestYPixel]
bottomLeft = [smallestXPixel,biggestYPixel]
bottomRight = [biggestXPixel,biggestYPixel]
screenshotDrawable = ImageDraw.Draw(screenshot)
screenshotDrawable.line([topLeft, topRight, bottomRight, bottomLeft, topLeft],fill=(255,0,0),width=2)
areaWidth = width + 2
areaHeight = height + 2
# generate led positions
ledPositions = [[(0,0) for x in range(height)] for y in range(width)] 
for x in range(width):
    for y in range(height):
        xPosition = topLeft[0] + ((x+1.5)/areaWidth)*(topRight[0]-topLeft[0])
        yPosition = topLeft[1] + ((y+1.5)/areaHeight)*(bottomLeft[1]-topLeft[1])
        ledPositions[x][y] = [xPosition, yPosition]
        screenshotDrawable.point((xPosition, yPosition))
screenshot.save("imageRecognizedParts.png")
print("Set the location of the power pole.")
while not polePositionSelected:
    time.sleep(1/60)

lastRenderedFrame = [False]*width*height
def placeFrame(frame):
    global lastRenderedFrame
    switchToLowerPoleFlag = dualPoleMode
    keyboardController.press(keyboard.Key.shift_l) # occaisionally this line doesn't work, and i have no idea how to make it 100% reliable, but it's good enough
    time.sleep(1/60)
    for index in range(len(frame)):
        if frame[index] == lastRenderedFrame[index]:
            continue
        # i don't know why you'd want a display with an odd number of pixels, but you can
        if index // width >= math.ceil(height/2) and switchToLowerPoleFlag:
            switchToLowerPoleFlag = False
            autoit.send("2")
            time.sleep(1/60)
            autoit.send("2")
            autoit.mouse_click("left",int(lowerPolePosition[0]),int(lowerPolePosition[1]),speed=clickSpeed)
            keyboardController.press(keyboard.Key.shift_l)

        position = ledPositions[index % width][index // width]
        autoit.mouse_click("left",int(position[0]),int(position[1]),speed=clickSpeed)
    lastRenderedFrame = frame

# begin placement
pyautogui.FAILSAFE = False # kerchow
pyautogui.PAUSE = 0
for index in range(totalFiles):
    if index < startFrame:
        continue
    print(f"Rendering frame {index+1}/{totalFiles}", end="\r")
    placeFrame(videoFramesProcessed[index])
    autoit.send("2")
    time.sleep(1/60)
    pyautogui.screenshot(outputDirectory+str(index)+".png")
    autoit.send("2")
    position = polePosition
    if dualPoleMode:
        position = upperPolePosition
    autoit.mouse_click("left",int(position[0]),int(position[1]),speed=clickSpeed) # you better not be a race condition
keyboardListener.stop()
autoit.send("+p")