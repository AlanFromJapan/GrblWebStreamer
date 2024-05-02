import sqlite3
import datetime
from threading import Lock

class LaserJobDB:
    __lock = Lock()
    __conn = None
    __cursor = None

    @classmethod
    def initialize(cls, db_file):
        LaserJobDB.__conn = sqlite3.connect(db_file)
        LaserJobDB.__cursor = LaserJobDB.__conn.cursor()
        LaserJobDB.create_table()


    @classmethod
    def create_table(cls):
        with LaserJobDB.__lock:
            LaserJobDB.__cursor.execute('''
                CREATE TABLE IF NOT EXISTS laser_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    submission_date TEXT,
                    estimated_duration INTEGER
                )
            ''')
            LaserJobDB.__conn.commit()


    @classmethod
    def get_jobs(cls):
        with LaserJobDB.__lock:
            LaserJobDB.__cursor.execute('SELECT * FROM laser_jobs')
            return LaserJobDB.__cursor.fetchall()

    @classmethod
    def get_job(cls, job_name):
        with LaserJobDB.__lock:
            LaserJobDB.__cursor.execute('SELECT * FROM laser_jobs where name = ? ORDER BY submission_date DESC', (job_name,))
            ro = LaserJobDB.__cursor.fetchone()
            if ro:
                return LaserJobDB(ro[1], ro[3], ro[2])
            else:
                return None
            
    @classmethod
    def close(cls):
        LaserJobDB.__cursor.close()
        LaserJobDB.__conn.close()


    def __init__(self, name, duration, submission_date=datetime.datetime.now()):
        self.name = name
        self.estimated_duration = duration
        self.submission_date = submission_date
        
    def record_job(self):
        with LaserJobDB.__lock:
            LaserJobDB.__cursor.execute('''
                INSERT INTO laser_jobs (name, submission_date, estimated_duration)
                VALUES (?, ?, ?)
            ''', (self.name, datetime.datetime.now(), self.estimated_duration))
            LaserJobDB.__conn.commit()
