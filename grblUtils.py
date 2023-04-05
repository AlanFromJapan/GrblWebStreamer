import serialUtils
import re
import datetime
import os
import config

REGEX_LIGHTBURN_BOUNDS=";\s+Bounds: X([0-9\.]+) Y([0-9\.]+) to X([0-9\.]+) Y([0-9\.]+)"

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

#Attempts to frame tne file content (just more around where the action will be)
def generateFrame(fileFullPath):
    fromto = __getFrameFromComments(fileFullPath)

    #TODO LOG
    print (f"Extracted from file: { str(fromto) }")

    #make a temp file
    tempfile = os.path.join(config.myconfig['upload folder'],
         "/tmp/frame_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ".nc")
    try:
        #TODO LOG
        print(f"Generating temporary framing file at { tempfile }")

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
; Go to origin, 1 percent  laser, 20 mm /sec (1200/min)
G0 X0Y0S010F1200
; Now move to corner and trace
""")
            f.write(f"G0 X{ fromto[0][0] }Y{ fromto[0][1] }\n")
            f.write(f"G1 X{ fromto[1][0] }\n")
            f.write(f"G1 Y{ fromto[1][1] }\n")
            f.write(f"G1 X{ fromto[0][0] }\n")
            f.write(f"G1 Y{ fromto[0][1] }\n")
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
        serialUtils.simulateFile(config.myconfig["device port"], tempfile)
    finally:
        try:
            os.remove(tempfile)
        except:
            #TODO LOG
            print(f"Couldn't delete temp frame file { tempfile }")