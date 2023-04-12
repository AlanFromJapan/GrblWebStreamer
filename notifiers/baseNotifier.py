
from datetime import datetime


class Job():
    name:str = ""
    start:datetime = None
    end:datetime = None


    def __init__(self, name) -> None:
        self.name = name
        self.start = datetime.now()



class BaseNotifier():
    __dateformat = '{0:%Y/%m/%d@%H:%M:%S}'

    def NotifyJobStart(self, j: Job):
        print(f"Starting job '{j.name}' at {self.__dateformat.format(j.start)}")

    def NotifyJobCompletion(self, j: Job):
        print(f"Completed job '{j.name}' at {self.__dateformat.format(j.end)} in {(j.end -j.start)/60:0.2f} min.")

    def NotifyJobError(self, j: Job):
        print(f"Error on job '{j.name}' at {self.__dateformat.format(datetime.now())}")

