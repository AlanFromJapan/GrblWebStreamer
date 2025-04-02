import serial
import serial.tools.list_ports
import time
import re
from enum import Enum, auto
import config
import logging

#GRBL so assume it constant
BAUDRATE=115200


#THE connection and textual port name associated
__SERIAL = None
__PORT = ''

#The status of the device connected from Serial/GRBL PoV
class ConnectionStatus(Enum):
    NOT_CONNECTED = auto()
    READY = auto()
    BUSY = auto()
    ERROR = auto()
__STATUS = ConnectionStatus.NOT_CONNECTED


##############################################################################################################################

#returns the text list of all the available comports
def listAvailableSerialPorts(portname_only = False):
    l = [str(port) for port in serial.tools.list_ports.comports()]

    #ports on linux are in format "/dev/ttyUSB0 - USB Serial Port"
    #portname_only = True will return only the "/dev/ttyUSB0" part
    if portname_only:
        l = [p[:p.index(" ")] for p in l]

    return l




#connects or reconnect or do nothing
def connect(port, forceDisconnect = False):
    global __SERIAL, __PORT, __STATUS
    #rightly connected?
    if __PORT == port and __SERIAL != None :
        #nothing to do
        logging.debug("Already connected to the right port.")
        return

    #connected to wrong port?
    if __PORT != '' or __SERIAL != None:        
        #first DIS-connect
        logging.debug("Disconnecting from current port.")

        if __STATUS in [ConnectionStatus.BUSY] and not forceDisconnect:
            logging.error("Status error: device is busy, cannot disconnect (try force).")
            raise Exception ("Status error: device is busy, cannot disconnect (try force).")

        disconnect()
        
    logging.debug(f"Connecting to new port= {port}")
    #not connected
    __SERIAL = serial.Serial(port,BAUDRATE)
    __PORT = port

    logging.debug(f"Connected to port= {port}")
    # Wait for grbl to initialize and flush startup text in serial input
    time.sleep(2)
    __SERIAL.flushInput()

    #set status
    __STATUS = ConnectionStatus.READY




#Disconnects from Serial
def disconnect():
    global __SERIAL, __PORT, __STATUS
    try:
        if __SERIAL != None:
            __SERIAL.close()
    except Exception as ex:
        logging.error("EXCEPT on disconnect:" + str(ex))
    
    __SERIAL = None
    __PORT = ''
    __STATUS = ConnectionStatus.NOT_CONNECTED




#send 1 command to the serial device (creating a new connection) and returns the response
def sendCommand (port, cmd:str, ignoreBusyStatus = False) -> str:
    global __SERIAL, __STATUS

    if not ignoreBusyStatus and __STATUS in [ConnectionStatus.BUSY]:
        #allow for error, contrary to send file so you can "unstuck" the device with a magic command ... maybe.
        logging.error("Status error: device is busy, cannot send a command.")
        raise Exception ("Status error: device is busy, cannot send a command.")

    try:
        connect(port)

        #update status
        __STATUS = ConnectionStatus.BUSY

        #send
        __SERIAL.write(str.encode(cmd + '\n'))

        #return result (try to empty the buffer)
        res = ''
        while True:
            res += __SERIAL.readline().decode().strip()
            time.sleep(0.1)
            if __SERIAL.in_waiting <= 0:
                break

        #update status
        __STATUS = ConnectionStatus.READY

        return res
    except Exception as ex:
        logging.error ("EXCEPT on sendCommand: " + str(ex))
        #update status
        __STATUS = ConnectionStatus.ERROR


#line modifier : set comments to None
def linemodifier_skipComments(l:str) -> str:
    if l[0] == ";":
        return None
    else:
        return l


#line modifier : set laser to 1% (replace Sxxx with S010)
def linemodifier_laserMinimum(l:str) -> str:
    #TODO find a way to NOT catch the final "G1 S0" that (should be here to) turn off the laser. Too late for regex now.
    l = re.sub("S\\d+", "S010", l)
    return l

REGEX_CMD_LASER_POWER = re.compile("S\\d+")
def linemodifier_laserAdjust(l:str, jobParams: dict = None) -> str:
    #lasers are usually set with Sxxx where xxx is a FLOAT between 0.0 and 1000.0 (in perThousands)
    if jobParams != None and "laserPowerAdjust" in jobParams:
        match = REGEX_CMD_LASER_POWER.search(l)
        if match != None:
            v = int(match.group(0)[1:])
            v = min(1000, v * jobParams['laserPowerAdjust'] // 100 )
            l = l[:match.start()] + f"S{v}" + l[match.end():]

    return l


#line modifier : on delay commands, sleep for a while
def linemodifier_delayCommands(l:str) -> str:
    """ https://www.sainsmart.com/blogs/news/grbl-v1-1-quick-reference
    G4 Pxxx : Dwell, Pause / Delay in SECONDS
    """
    if l.startswith("G4"):
        #assume they RTFM and sent duration in SECONDS or it's going to be a very LONG pause 
        # https://github.com/gnea/grbl/issues/343
        time.sleep(float(re.search(r"P[0-9.]+", l).group(0)[1:]))
        return None
    else:
        return l
    

#process a file, line per line, applying modifiers to each line before sending them (ignore comments, change values on the fly, etc.)
def processFile (port:str, fileFullPath:str, lineModifiers = [linemodifier_skipComments], forceStopCheck = None):
    global __SERIAL, __STATUS

    if __STATUS in [ConnectionStatus.BUSY, ConnectionStatus.ERROR]:
        logging.error("Status error: device is busy or in error, cannot start a new job.")
        raise Exception ("Status error: device is busy or in error, cannot start a new job.")

    try:
        connect(port)
    except Exception as ex:
        logging.error("Error at connection : " + str(ex))
        #update status
        __STATUS = ConnectionStatus.NOT_CONNECTED
        raise Exception("Failed to connect to device - see logs")

    try:
        #update status
        __STATUS = ConnectionStatus.BUSY

        with open(fileFullPath, "r") as f:
            for line in f:
                l = line.strip()
                if l == '':
                    continue
                for mod in lineModifiers:
                    l = mod(l)
                    if l == None:
                        break
                if l != None:
                    #send
                    __SERIAL.write(str.encode(l + '\n'))
                    # Wait for grbl response with carriage return
                    grbl_out = __SERIAL.readline().decode().strip() 

                    #TODO check for the answer to be "ok" and if not handle it

                    logging.debug(f"{line.strip()} ==> {l.strip()} ==? {str(grbl_out).strip()}")
                
                #check for foreceful stop
                if forceStopCheck != None and forceStopCheck():
                    #it will stop here: so execute the outro somewhere else.
                    logging.warning(f"Force stop requested on file {fileFullPath}.")
                    break
        #update status
        __STATUS = ConnectionStatus.READY

    except Exception as ex:
        logging.error("Exception processing file : " + str(ex))
        #update status
        __STATUS = ConnectionStatus.ERROR

        raise ex


#process one file for fake (laser min val)
def simulateFile(port:str, fileFullPath:str):
    #the modifiers to use when burning a file
    linemodif = [linemodifier_skipComments, linemodifier_laserMinimum]
    if not config.myconfig.get("G4 delays handled by device", True):
        #if your device doesn't handle G4 delays, you can use this to handle them on the software "sending" side
        linemodif.append(linemodifier_delayCommands)

    processFile(port, fileFullPath, lineModifiers=linemodif)


#returns serial status
def serialStatusEnum():
    global __SERIAL, __PORT, __STATUS
    return ConnectionStatus.NOT_CONNECTED if __SERIAL == None or __PORT == '' else __STATUS



