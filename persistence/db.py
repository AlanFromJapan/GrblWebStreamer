import sqlite3
import datetime
from threading import Lock
import grbl2image.grbl2image as G2I
import os

class LaserJobDB:
    __lock = Lock()
    __conn = None
    __cursor = None

    @classmethod
    def initialize(cls, db_file):
        try:
            #check_same_thread=False to allow jobs (on worker thread) to use the connection (static, that was created on MAIN thread)
            LaserJobDB.__conn = sqlite3.connect(db_file, check_same_thread=False)
            LaserJobDB.__cursor = LaserJobDB.__conn.cursor()
            LaserJobDB.create_table()
        except sqlite3.OperationalError:
            print(f"DB File not found: '{db_file}' [current dir: {os.getcwd()}]")
            #farewell everyone
            raise


    @classmethod
    def create_table(cls):
        with LaserJobDB.__lock:
            LaserJobDB.__cursor.execute('''
                CREATE TABLE IF NOT EXISTS laser_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    submission_date TEXT,
                    estimated_duration INTEGER,
                    fromXYmm TEXT,
                    toXYmm TEXT                 
                )
            ''')
            LaserJobDB.__conn.commit()


    @classmethod
    def get_jobs(cls):
        with LaserJobDB.__lock:
            LaserJobDB.__cursor.execute('SELECT * FROM laser_jobs')
            return LaserJobDB.__cursor.fetchall()

    @classmethod
    def strXY2array(cls, xyStr):
        xy = xyStr.split(',')
        return [float(xy[0]), float(xy[1])]
    
    @classmethod
    def get_job(cls, job_name):
        with LaserJobDB.__lock:
            LaserJobDB.__cursor.execute('SELECT * FROM laser_jobs where name = ? ORDER BY submission_date DESC', (job_name,))
            ro = LaserJobDB.__cursor.fetchone()
            if ro:
                return LaserJobDB(name=ro[1], submission_date=ro[2], duration=ro[3], fromXY=LaserJobDB.strXY2array(ro[4]), toXY=LaserJobDB.strXY2array(ro[5]), stats=None)
            else:
                return None
            
    @classmethod
    def close(cls):
        LaserJobDB.__cursor.close()
        LaserJobDB.__conn.close()


    def __init__(self, name, duration=0, submission_date=datetime.datetime.now(), fromXY=[0,0], toXY=[200, 200], stats:G2I.JobStats=None):
        self.name = name
        self.submission_date = submission_date

        if stats:
            self.estimated_duration = stats.estimatedDurationSec
            self.fromXY = stats.pointFromMM
            self.toXY = stats.pointToMM
        else:
            self.estimated_duration = duration
            self.fromXY = fromXY
            self.toXY = toXY
        
    def record_job(self):
        with LaserJobDB.__lock:
            LaserJobDB.__cursor.execute('''
                INSERT INTO laser_jobs (name, submission_date, estimated_duration, fromXYmm, toXYmm)
                VALUES (?, ?, ?, ?, ?)
            ''', (self.name, datetime.datetime.now(), f"{self.estimated_duration:0.1f}", f"{self.fromXY[0]:0.1f},{self.fromXY[1]:0.1f}", f"{self.toXY[0]:0.1f},{self.toXY[1]:0.1f}"))
            LaserJobDB.__conn.commit()

    #Couldn't find an easy way to NOT replicate this function from baseNotifier.py I hate copy paste but I see no (easy) other way here
    def durationPretty(self) -> str:
        sec = self.estimated_duration
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