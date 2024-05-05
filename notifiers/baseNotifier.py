
from datetime import datetime, timedelta
from flask import flash
from enum import Enum, auto
import logging

#The type of job
class JobType(Enum):
    BURN = auto()
    FRAME = auto()
    SIMULATE = auto()


#a GRBL job
class Job():
    name:str = ""
    start:datetime = None
    end:datetime = None
    jobType : JobType = JobType.BURN

    def __init__(self, name, jobType : JobType = JobType.BURN, details=None) -> None:
        self.name = name
        self.start = datetime.now()
        self.jobType = jobType
        self.details = details

    def durationInSec(self) -> float:
        d = self.duration()
        return d.total_seconds()

    def duration(self) -> timedelta:
        return (self.end - self.start) if self.end != None else timedelta(0)

    def durationPretty(self) -> str:
        d = self.duration()
        sec = self.durationInSec()
        s = ""

        if sec < 60.0:
            s = f"{sec:0.1f} seconds"
        elif sec < 3600.0:
            s = f"{sec/60:0.0f} min {sec % 60:0.0f} sec"
        elif sec < (3600.0 * 24.0):
            s = f"{sec/3600:0.0f} hour(s) {(sec % 3600) /60:0.0f} min"
        else:
            s = str(d)

        return s

    def finish(self):
        self.end = datetime.now()

    def __str__(self) -> str:
        return f"Job '{self.name}'"
    


#Base class for Notifiers, prints to stdout
class BaseNotifier():
    __dateformat = '{0:%H:%M:%S}'

    def NotifyServerReady (self, ip:str = "<unknown IP>"):
        print(self._makeReadyMsg(ip))

    def NotifyJobStart(self, j: Job):
        print(self._makeStartMsg(j))

    def NotifyJobCompletion(self, j: Job):
        print(self._makeCompletionMsg(j))

    def NotifyJobError(self, j: Job, extra:str = None):
        print(self._makeErrorMsg(j, extra))

    def _makeReadyMsg(self, ip:str):
        return f"GRBL WebStreamer startup, now listening on http://{ip}"
    
    def _makeStartMsg(self, j:Job):
        expectedDuration = "unknown"
        try:
            expectedDuration = j.details.durationPretty() if j.details else "unknown"
        except Exception as ex:
            logging.error(f"Error getting expected duration for job '{j.name}': {str(ex)}")
        return f"Starting job '{j.name}' in mode {j.jobType.name} at {self.__dateformat.format(j.start)}. \nExpected duration: {expectedDuration}."
    
    def _makeCompletionMsg(self, j:Job):
        return f"Completed job '{j.name}' at {self.__dateformat.format(j.end)} in {j.durationPretty()}."

    def _makeErrorMsg(self, j:Job, extra:str = None):
        return f"Error on job '{j.name}' at {self.__dateformat.format(datetime.now())}" + (": " + extra) if extra and not extra.isspace() else ""




#Flash notifier, does flash() messages in Flask
class FlashNotifier(BaseNotifier):

    def __init__(self) -> None:
        super().__init__()

    def NotifyServerReady (self, ip:str = "<unknown IP>"):
        #do nothing - not in a page
        pass

    def NotifyJobStart(self, j: Job):
        flash(self._makeStartMsg(j))

    def NotifyJobCompletion(self, j: Job):
        flash(self._makeCompletionMsg(j), "success")

    def NotifyJobError(self, j: Job, extra:str = None):
        flash(self._makeErrorMsg(j, extra), "error")

