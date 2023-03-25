import serial
import serial.tools.list_ports
import time

#GRBL so assume it constant
BAUDRATE=115200

#Wellknown commands
CMD_STATUS = "?"

#returns the text list of all the available comports
def listAvailableSerialPorts():
    return [str(port) for port in serial.tools.list_ports.comports()]


#send 1 command to the serial device (creating a new connection) and returns the response
#DOn't use this to send a lot of command: creating new connection each time will take time and each time most likely reset the device
def sendCommand (port, cmd:str) -> str:
    s = None
    try:
        s = serial.Serial(port,BAUDRATE)

        # Wait for grbl to initialize and flush startup text in serial input
        time.sleep(2)
        s.flushInput()
        
        #send
        s.write(str.encode(cmd + '\n'))

        #return result 
        return str(s.readline().strip()) 
    finally:
        if s != None:
            s.close()