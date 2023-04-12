#Notifier for NAVER Line bot
from  baseNotifier import Job, BaseNotifier
from datetime import datetime

class LineBotNotifier(BaseNotifier):

    def __init__(self) -> None:
        super().__init__()


    def NotifyJobStart(self, j: Job):
        print(f"Starting job {j.name} at {self.__dateformat.format(j.start)}")

    def NotifyJobCompletion(self, j: Job):
        print(f"Completed job {j.name} at {self.__dateformat.format(j.end)} in {(j.end -j.start)/60:0.2f} min.")

    def NotifyJobError(self, j: Job):
        print(f"Error on job {j.name} at {self.__dateformat.format(datetime.now())}")
