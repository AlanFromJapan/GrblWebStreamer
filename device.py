import os
import serialUtils
import grblUtils

from enum import Enum

class DeviceStatus(Enum):
    IDLE = 1
    BUSY = 2
    ERROR = 3
    NOT_FOUND = 4
    HOLD = 5


class WellKnownCommands(Enum):
    CMD_STATUS = "?"
    CMD_GOTO_ORIGIN = "G0 X0Y0"
    CMD_RESUME = "~" #to resume after a HOLD state



class Device:
    port: str = None
    status = DeviceStatus.NOT_FOUND
    
    #constructor
    def __init__(self, port):
        self.port = port


    def simulate (self, fileOnDisk):
        self.status = DeviceStatus.BUSY
        serialUtils.simulateFile(self.port, fileOnDisk)
        self.status = DeviceStatus.IDLE


    def burn (self, fileOnDisk):
        self.status = DeviceStatus.BUSY
        serialUtils.processFile(self.port, fileOnDisk)
        self.status = DeviceStatus.IDLE


    def frame(self, fileOnDisk):
        self.status = DeviceStatus.BUSY
        grblUtils.generateFrame(self.port, fileOnDisk)
        self.status = DeviceStatus.IDLE


    # send command to device and returns result
    def sendCommand(self, command) -> str:
        self.status = DeviceStatus.BUSY
        res = serialUtils.sendCommand(self.port, command)
        self.status = DeviceStatus.IDLE
        return res
    

    def disconnect(self):
        self.status = DeviceStatus.BUSY
        serialUtils.disconnect()
        self.status = DeviceStatus.NOT_FOUND


    def reconnect(self, port) -> DeviceStatus:
        self.disconnect()

        self.port = port

        try:
            serialUtils.connect(self.port)
            self.status = DeviceStatus.IDLE
        except:
            self.status = DeviceStatus.NOT_FOUND
        
        return self.status