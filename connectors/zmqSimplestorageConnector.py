from connectors.baseConnector import BaseConnector
import zmq
import base64
import os
import json
import logging

from werkzeug.utils import secure_filename


class ZMQSimpleStorageConnector(BaseConnector):
    __context : zmq.Context = None
    __socket : zmq.Socket = None
    __storagePath : str = "testfolder"
    __hostport: str = "localhost:55555"
    

    # serverHostPort: str = "localhost:5555"
    def __init__(self, storagePath: str, serverHostPort: str ) -> None:
        self.__context = zmq.Context()
        self.__socket = self.__context.socket(zmq.REQ)
        self.__socket.RCVTIMEO = 2000
        self.__hostport = serverHostPort
        self.__socket.connect(f"tcp://{self.__hostport}")
        self.__storagePath = storagePath
        super().__init__()

    def __str__(self) -> str:
        return "ZMQ at " + self.__hostport



    # Fetches the latest data from the connector, returns filename (not full path) if successful, None if no data
    def fetchLatest(self) -> str:
        logging.info(f"Fetching latest data from ZMQ Simple Storage at {self.__hostport}")
        
        try:
            msg = """{
                "message": "fetch"
            }
            """ 

            self.__socket.send_string(msg)

            reply = self.__socket.recv_string()
            
            logging.debug(f"Received message: {reply}")

            if str(reply) in ("None", "null"):
                logging.info("No file to fetch")
                return None

            j = json.loads(reply)
            filename = secure_filename(j["filename"])
            logging.info(f"File fetched '{filename}'")

            ext = os.path.basename(filename).split(".")[-1]
            if ext not in ["gcode", "nc", "gc"]:
                logging.error(f"File extension '{ext}' not supported for file '{filename}'")
                print(f"File extension '{ext}' not supported for file '{filename}'")
                return None


            #force extension to .nc
            filename = filename[:filename.rfind(".")] + ".nc"

            #filename storage location, use basename to avoid path traversal
            output_filename = os.path.join(self.__storagePath, os.path.basename(filename))

            with open(output_filename, "wb") as f:
                f.write(base64.b64decode(j["content"].encode()))       

            
            logging.info(f"File '{filename}' stored as '{ output_filename }'") 

            return filename
        except Exception as e:
            print(str(e))
            logging.error(f"Error fetching data from ZMQ Simple Storage: {e}")
            return None