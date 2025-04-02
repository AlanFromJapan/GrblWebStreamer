import serialUtils
import grblUtils
import config
import threading
from  notifiers.baseNotifier import Job
from werkzeug.serving import is_running_from_reloader

import logging
from enum import Enum

import threading
import time

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
    __CHECKER_THREAD_LOCK = threading.Lock()
    
    #constructor
    def __init__(self, port : str):
        self.port = port
        self.status = DeviceStatus.NOT_FOUND
        self.emergency_stop_requested  = False

        self.checker_thread = None
        self.checker_thread_killed = False


    #destructor
    def __del__(self) -> None:
        if self.checker_thread is not None:
            logging.warning(f"Checker thread to be killed for thread {self.checker_thread}")   
            self.checker_thread_killed = True
            self.checker_thread.join()
            logging.warning(f"Checker thread killed")   


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
        self.emergency_stop_requested = False
        if asynchronous:
            threading.Thread(target=self.__burnAsync, args=(fileOnDisk, job, )).start()
        else:
            self.__burnAsync(fileOnDisk, job)
    
    def __burnAsync (self, fileOnDisk, job : Job = None):
        #the modifiers to use when burning a file
        linemodif = [serialUtils.linemodifier_skipComments]
        if not config.myconfig.get("G4 delays handled by device", True):
            #if your device doesn't handle G4 delays, you can use this to handle them on the software "sending" side
            linemodif.append(serialUtils.linemodifier_delayCommands)

        serialUtils.processFile(self.port, fileOnDisk, lineModifiers=linemodif, forceStopCheck=self.__checkForJobCancellation)
        if self.emergency_stop_requested:
            #send outro
            grblUtils.sendOutroOnly(self.port)
        self.emergency_stop_requested = False
        self.__completeJob(job)


    #called by the serial utils to check if a job cancellation was requested
    def __checkForJobCancellation (self):
        #change status in the __burnAsync method
        return self.emergency_stop_requested


    #-------------------------------------------------------------
    def frame(self, fileOnDisk, asynchronous = False, job : Job = None):
        self.status = DeviceStatus.BUSY
        if asynchronous:
            threading.Thread(target=self.__frameAsync, args=(fileOnDisk,job, )).start()
        else:
            self.__frameAsync(fileOnDisk, job)

    def __frameAsync(self, fileOnDisk, job : Job = None):
        grblUtils.generateFrame(self.port, fileOnDisk, framingSpeendInMMPerSec=25)
        self.__completeJob(job)


    #-------------------------------------------------------------
    def frameWithCornerPause(self, fileOnDisk, asynchronous = False, job : Job = None):
        self.status = DeviceStatus.BUSY
        if asynchronous:
            threading.Thread(target=self.__frameWithCornerPauseAsync, args=(fileOnDisk,job, )).start()
        else:
            self.__frameWithCornerPauseAsync(fileOnDisk, job)

    def __frameWithCornerPauseAsync(self, fileOnDisk, job : Job = None):
        grblUtils.generateFrame(self.port, fileOnDisk, pauseAtCornersInSec=4, framingSpeendInMMPerSec=50)
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
    def connect(self, port : str = None) -> DeviceStatus:
        if port is None:
            port = self.port

        if not self.status in [DeviceStatus.NOT_FOUND, DeviceStatus.ERROR]:
            logging.warning(f"Device.connect() : wrong status {self.status}")
            #no change
            return self.status

        #not need to try on ports that aren't available
        if port not in serialUtils.listAvailableSerialPorts(portname_only=True):
            logging.warning(f"Device.connect() : port not available {port}")
            self.status = DeviceStatus.NOT_FOUND
            return self.status

        try:
            logging.warning(f"Device.connect() : Connecting to device on port {port}")
            self.port = port
            serialUtils.connect(self.port)
            self.status = DeviceStatus.IDLE
        except:
            self.status = DeviceStatus.ERROR
        
        return self.status


    #-------------------------------------------------------------
    def reconnect(self, port) -> DeviceStatus:
        self.disconnect()

        return self.connect(port)
    

    #-------------------------------------------------------------
    def check_for_device(self):
        #will terminate once the device is found
        while not self.checker_thread_killed and self.status in [DeviceStatus.NOT_FOUND]:
            logging.warning(f"Checking for device on port {self.port}")
            self.connect()

            logging.warning(f"Trying to connect to device on port {self.port} with status {self.status}")

            #wait a few seconds before trying again
            time.sleep(3)


    def start_thread_check_for_device(self):
        #https://stackoverflow.com/questions/25504149/why-does-running-the-flask-dev-server-run-itself-twice
        #in dev mode, the server is started twice, so we need to check if we are in the reloader (and ignore it): we want to run in child subprocess only
        if not is_running_from_reloader():
            return
        

        with Device.__CHECKER_THREAD_LOCK:
            if self.checker_thread != None:
                logging.warning(f"ABORT Checker thread already started for port {self.port}")
                return
            
            logging.warning(f"Starting thread to check for device on port {self.port}")

            self.checker_thread = threading.Thread(target=self.check_for_device)
            #stop when main thread stops
            self.checker_thread.daemon = True
            self.checker_thread.start()