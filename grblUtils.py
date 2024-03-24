import serialUtils
import re
import datetime
import os
import config
import logging

import grbl2image.grbl2image as G2I
from PIL import Image

REGEX_LIGHTBURN_BOUNDS=";\s+Bounds: X([0-9\.]+) Y([0-9\.]+) to X([0-9\.]+) Y([0-9\.]+)"
REGEX_DEVICE_STATUS = "<(?P<state>[^:|]+)(?::||).*"

#Try to extract the wellknown comment about boundaries to get the frame details.
#Ok it's ugly and risky but hey it's here so no need to redo what was done by professionals
def __getFrameFromComments (fileFullPath):
    with open(fileFullPath, "r") as f:
        for l in f:
            m = re.search(REGEX_LIGHTBURN_BOUNDS, l.strip())
            if None != m:
                #got it !
                grp = m.groups()
                grp = [float(x) for x in grp]
                return [[grp[0], grp[1]], [grp[2], grp[3]]]

    return None


#Used for cancellation, to force the device to stop and terminate nicely
def sendOutroOnly (port:str):
    logging.warn("Sending outro only")

    outro = """; Outro, turn everything off nicely
G90
M9
G1 S0
M5
G90
; return to user-defined finish pos
G0 X0 Y0
M2
"""
    try:
        for l in outro.split("\n"):
            l = l.strip()
            if l == '':
                continue
            #If you send outro, you don't care about the busy status (most likely it IS busy and you cancel a job)
            res = serialUtils.sendCommand(port, l, ignoreBusyStatus=True)
            logging.debug(f"Outro line '{ l }' result: { res }")

    except Exception as ex:
        logging.error("Error at outro : " + str(ex))


#Attempts to frame tne file content (just more around where the action will be)
def generateFrame(port, fileFullPath, pauseAtCornersInSec:float = 0.0, framingSpeendInMMPerSec:int = 20):
    fromto = __getFrameFromComments(fileFullPath)

    logging.info (f"Extracted from file: { str(fromto) }")

    #make a temp file
    tempfile = os.path.join(config.myconfig['upload folder'],
         "/tmp/frame_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ".nc")
    try:
        logging.info(f"Generating temporary framing file at { tempfile }")

        with open(tempfile, "w+") as f:
            f.write(f"""; Framing temporary file autogenerated
; { tempfile }
; Assuming creator was a chad and uses metric system
; Using minmax coordinates : { fromto }
; 
G00 G17 G40 G21 G54
G90
M4
M8
; Go to origin, 1 percent  laser, {framingSpeendInMMPerSec} mm /sec ({framingSpeendInMMPerSec * 60} mm/min)
G0 X0Y0S010F{framingSpeendInMMPerSec * 60}
; Now move to corner and trace
""")
            
            f.write(f"G0 X{ fromto[0][0] }Y{ fromto[0][1] }\n")
            if pauseAtCornersInSec > 0.0: f.write(f"G4 P{ pauseAtCornersInSec:0.1f}\n")
            f.write(f"G1 X{ fromto[1][0] }\n")
            if pauseAtCornersInSec > 0.0: f.write(f"G4 P{ pauseAtCornersInSec:0.1f}\n")
            f.write(f"G1 Y{ fromto[1][1] }\n")
            if pauseAtCornersInSec > 0.0: f.write(f"G4 P{ pauseAtCornersInSec:0.1f}\n")
            f.write(f"G1 X{ fromto[0][0] }\n")
            if pauseAtCornersInSec > 0.0: f.write(f"G4 P{ pauseAtCornersInSec:0.1f}\n")
            f.write(f"G1 Y{ fromto[0][1] }\n")
            if pauseAtCornersInSec > 0.0: f.write(f"G4 P{ pauseAtCornersInSec:0.1f}\n")

            f.write("""
; Outro, turn everything off nicely
G90
M9
G1 S0
M5
G90
; return to user-defined finish pos
G0 X0 Y0
M2
""")

        #debug
        #with open(tempfile, "r") as f: print("".join(f.readlines()))
        
        
        #not taking risks
        serialUtils.simulateFile(port, tempfile)
    finally:
        try:
            os.remove(tempfile)
        except:
            logging.error(f"Couldn't delete temp frame file { tempfile }")


#From a filename, returns the path to the thumbnail
def pathToThumbnail (filename:str):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(dir_path, "static", "thumbnails", os.path.basename(filename) + ".png")


#Creates an image PNG of the job stored in same folder, same name, with PNG suffix
def createThumbnailForJob(fileFullPath:str):
    #Generate the PIL Image object based on sample code
    img, _ = G2I.processFile(fileFullPath, color="crimson")

    #final flip because the image 0,0 is top left and for us human it's at the bottom left
    img = img.transpose(Image.FLIP_TOP_BOTTOM)    

    #make sure it is saved in the subfolder of current file
    thumbnail = pathToThumbnail(fileFullPath) 
    img.save(thumbnail)


#Delete thumbnail
def deleteThumbnailForJob(filename:str):
    thumbnail = pathToThumbnail(filename) 
    os.remove(thumbnail)


#Returns the DEVICE status (Idle, Hold, ...)
def getDeviceStatus():
    deviceStatus = serialUtils.serialStatusEnum()

    if deviceStatus == serialUtils.ConnectionStatus.READY:
        #device is not communicating but ready to receive order
        res = serialUtils.sendCommand(config.myconfig["device port"], serialUtils.CMD_STATUS )
        m = re.search(REGEX_DEVICE_STATUS, res)
        if m != None:
            return m.group("state")
        else:
            #Shouldn't happen but just in case
            return "Unknown"            
    else:
        return "Not Ready or Busy?"