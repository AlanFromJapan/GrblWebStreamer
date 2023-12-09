import serialUtils
import grblUtils
import config
import threading
from  notifiers.baseNotifier import Job

import logging
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


# Methods are sync unless stated otherwise
class Device:
    port: str = None
    status = DeviceStatus.NOT_FOUND
    
    #constructor
    def __init__(self, port):
        self.port = port


    def __notifyAll (self, job : Job):
        if job is not None:
            #notify
            for x in config.myconfig["notifiers"]: 
                try:
                    x.NotifyJobCompletion(job)
                except Exception as ex:
                    #fail silently
                    logging.warning(f"Failed to notify job {job} completion {x} with message {ex}")


    def __completeJob (self, job : Job):
        self.status = DeviceStatus.IDLE
        if job is not None:
            job.finish()
            self.__notifyAll(job)

    #-------------------------------------------------------------
    def simulate (self, fileOnDisk, asynchronous = False, job : Job = None):
        self.status = DeviceStatus.BUSY
        if asynchronous: 
            threading.Thread(target=self.__simulateAsync, args=(fileOnDisk, job, )).start()   
        else:   
            self.__simulateAsync(fileOnDisk, job)

    def __simulateAsync (self, fileOnDisk, job : Job = None):
        serialUtils.simulateFile(self.port, fileOnDisk)
        self.__completeJob(job)


    #-------------------------------------------------------------
    def burn (self, fileOnDisk, asynchronous = False, job : Job = None):
        self.status = DeviceStatus.BUSY
        if asynchronous:
            threading.Thread(target=self.__burnAsync, args=(fileOnDisk, job, )).start()
        else:
            self.__burnAsync(fileOnDisk, job)
    
    def __burnAsync (self, fileOnDisk, job : Job = None):
        serialUtils.processFile(self.port, fileOnDisk)
        self.__completeJob(job)





    #-------------------------------------------------------------
    def frame(self, fileOnDisk, asynchronous = False, job : Job = None):
        self.status = DeviceStatus.BUSY
        if asynchronous:
            threading.Thread(target=self.__frameAsync, args=(fileOnDisk,job, )).start()
        else:
            self.__frameAsync(fileOnDisk, job)

    def __frameAsync(self, fileOnDisk, job : Job = None):
        grblUtils.generateFrame(self.port, fileOnDisk)
        self.__completeJob(job)


    #-------------------------------------------------------------


    # send command to device and returns result
    def sendCommand(self, command) -> str:
        self.status = DeviceStatus.BUSY
        res = serialUtils.sendCommand(self.port, command)
        if res is not None:
            self.status = DeviceStatus.IDLE
        else:
            self.status = DeviceStatus.ERROR
        return res
    

    #-------------------------------------------------------------
    def disconnect(self):
        self.status = DeviceStatus.BUSY
        serialUtils.disconnect()
        self.status = DeviceStatus.NOT_FOUND


    #-------------------------------------------------------------
    def reconnect(self, port) -> DeviceStatus:
        self.disconnect()

        self.port = port

        try:
            serialUtils.connect(self.port)
            self.status = DeviceStatus.IDLE
        except:
            self.status = DeviceStatus.ERROR
        
        return self.status