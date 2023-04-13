
from datetime import datetime, timedelta
from flask import flash

#a GRBL job
class Job():
    name:str = ""
    start:datetime = None
    end:datetime = None

    def __init__(self, name) -> None:
        self.name = name
        self.start = datetime.now()

    def durationInSec(self) -> float:
        return (self.end - self.start) if self.end != None else timedelta(0)
    
    def finish(self):
        self.end = datetime.now()

    def __str__(self) -> str:
        return f"Job '{self.name}'"
    


#Base class for Notifiers, prints to stdout
class BaseNotifier():
    __dateformat = '{0:%Y/%m/%d@%H:%M:%S}'

    def NotifyServerReady (self):
        print(self._makeReadyMsg())

    def NotifyJobStart(self, j: Job):
        print(self._makeStartMsg(j))

    def NotifyJobCompletion(self, j: Job):
        print(self._makeCompletionMsg(j))

    def NotifyJobError(self, j: Job, extra:str = None):
        print(self._makeErrorMsg(j, extra))

    def _makeReadyMsg(self):
        return "GRBL WebStreamer application startup!"
    
    def _makeStartMsg(self, j:Job):
        return f"Starting job '{j.name}' at {self.__dateformat.format(j.start)}"
    
    def _makeCompletionMsg(self, j:Job):
        return f"Completed job '{j.name}' at {self.__dateformat.format(j.end)} in {j.durationInSec()}."

    def _makeErrorMsg(self, j:Job, extra:str = None):
        return f"Error on job '{j.name}' at {self.__dateformat.format(datetime.now())}" + (": " + extra) if extra and not extra.isspace() else ""




#Flash notifier, does flash() messages in Flask
class FlashNotifier(BaseNotifier):

    def __init__(self) -> None:
        super().__init__()

    def NotifyServerReady (self):
        #do nothing - not in a page
        pass

    def NotifyJobStart(self, j: Job):
        flash(self._makeStartMsg(j))

    def NotifyJobCompletion(self, j: Job):
        flash(self._makeCompletionMsg(j), "success")

    def NotifyJobError(self, j: Job, extra:str = None):
        flash(self._makeErrorMsg(j, extra), "error")

