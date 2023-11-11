import serial
import serial.tools.list_ports
import time
import re
from enum import Enum, auto
import config
import logging

#GRBL so assume it constant
BAUDRATE=115200

#Wellknown commands
CMD_STATUS = "?"
CMD_GOTO_ORIGIN = "G0 X0Y0"
CMD_RESUME = "~" #to resume after a HOLD state


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
def listAvailableSerialPorts():
    return [str(port) for port in serial.tools.list_ports.comports()]




#connects or reconnect or do nothing
def connect(port, forceDisconnect = False):
    global __SERIAL, __PORT, __STATUS
    #rightly connected?
    if __PORT == port and __SERIAL != None :
        #nothing to do
        return

    #connected to wrong port?
    if __PORT != '' or __SERIAL != None:        
        #first DIS-connect

        if __STATUS in [ConnectionStatus.BUSY] and not forceDisconnect:
            logging.error("Status error: device is busy, cannot disconnect (try force).")
            raise Exception ("Status error: device is busy, cannot disconnect (try force).")

        disconnect()
        
    #not connected
    __SERIAL = serial.Serial(port,BAUDRATE)
    __PORT = port

    # Wait for grbl to initialize and flush startup text in serial input
    time.sleep(2)
    __SERIAL.flushInput()

    #set status
    __STATUS = ConnectionStatus.READY




#Disconnects from Serial
def disconnect():
    global __SERIAL, __PORT, __STATUS
    try:
        __SERIAL.close()
    except Exception as ex:
        logging.error("EXCEPT on disconnect:" + str(ex))
    
    __SERIAL = None
    __PORT = ''
    __STATUS = ConnectionStatus.NOT_CONNECTED




#send 1 command to the serial device (creating a new connection) and returns the response
def sendCommand (port, cmd:str) -> str:
    global __SERIAL, __STATUS

    if __STATUS in [ConnectionStatus.BUSY]:
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
def __linemodifier_skipComments(l:str) -> str:
    if l.strip()[0] == ";":
        return None
    else:
        return l


#line modifier : set laser to 1% (replace Sxxx with S010)
def __linemodifier_laserMinimum(l:str) -> str:
    l = l.strip()
    #TODO find a way to NOT catch the final "G1 S0" that (should be here to) turn off the laser. Too late for regex now.
    l = re.sub("S\\d+", "S010", l)
    return l


#process a file, line per line, applying modifiers to each line before sending them (ignore comments, change values on the fly, etc.)
def processFile (port:str, fileFullPath:str, lineModifiers = [__linemodifier_skipComments]):
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
        #update status
        __STATUS = ConnectionStatus.READY

    except Exception as ex:
        logging.error("Exception processing file : " + str(ex))
        #update status
        __STATUS = ConnectionStatus.ERROR

        raise ex


#process one file for fake (laser min val)
def simulateFile(port:str, fileFullPath:str):
    processFile(port, fileFullPath, [__linemodifier_skipComments, __linemodifier_laserMinimum])


#returns serial status
def serialStatusEnum():
    global __SERIAL, __PORT, __STATUS
    return ConnectionStatus.NOT_CONNECTED if __SERIAL == None or __PORT == '' else __STATUS



