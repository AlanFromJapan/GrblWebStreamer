import serial
import serial.tools.list_ports
import time

#GRBL so assume it constant
BAUDRATE=115200

#Wellknown commands
CMD_STATUS = "?"
CMD_GOTO_ORIGIN = "G0 X0Y0"


#THE connection and textual port name associated
__SERIAL = None
__PORT = ''

#returns the text list of all the available comports
def listAvailableSerialPorts():
    return [str(port) for port in serial.tools.list_ports.comports()]

#connects or reconnect or do nothing
def connect(port):
    global __SERIAL, __PORT
    #rightly connected?
    if __PORT == port and __SERIAL != None :
        #nothing to do
        return

    #connected to wrong port?
    if __PORT != '' or __SERIAL != None:
        #first DIS-connect
        disconnect()

    #not connected
    __SERIAL = serial.Serial(port,BAUDRATE)
    __PORT = port

    # Wait for grbl to initialize and flush startup text in serial input
    time.sleep(2)
    __SERIAL.flushInput()


#Disconnects from Serial
def disconnect():
    global __SERIAL, __PORT
    try:
        __SERIAL.close()
    except Exception as ex:
        #TODO LOG!
        print("EXCEPT on disconnect:" + str(ex))
    
    __SERIAL = None
    __PORT = ''


#send 1 command to the serial device (creating a new connection) and returns the response
def sendCommand (port, cmd:str) -> str:
    global __SERIAL
    try:
        connect(port)

        #send
        __SERIAL.write(str.encode(cmd + '\n'))

        #return result 
        return str(__SERIAL.readline().strip()) 
    except Exception as ex:
        print ("EXCEPT on sendCommand: " + str(ex))