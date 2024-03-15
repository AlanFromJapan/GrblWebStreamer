from baseConnector import BaseConnector
import zmq
import base64
import os
import json
import logging


context = zmq.Context()
socket = context.socket(zmq.REQ)

class ZQMSimpleStorageConnector(BaseConnector):
    __socket : zmq.Socket = None
    __storagePath : str = "testfolder"

    # serverHostPort: str = "localhost:5555"
    def __init__(self, storagePath: str, serverHostPort: str = "localhost:55555") -> None:
        self.__socket = context.socket(zmq.REQ)
        self.__socket.connect(f"tcp://{serverHostPort}")
        self.__storagePath = storagePath
        super().__init__()



    # Fetches the latest data from the connector, returns filename if successful, None if no data
    def fetchLatest(self) -> str:
        logging.info("Fetching latest data from ZQM Simple Storage")
        try:
            msg = """{
                "message": "fetch"
            }
            """ 

            socket.send_string(msg)

            message = socket.recv_string()
            
            logging.debug(f"Received message: {message}")

            if str(message) in ("None", "null"):
                logging.info("No file to fetch")
                return None

            j = json.loads(message)
            logging.info(f"File fetched '{j["filename"]}'")

            #filename storage location, use basename to avoid path traversal
            output_filename = os.path.join(self.__storagePath, os.path.basename(j["filename"]))

            with open(output_filename, "wb") as f:
                f.write(base64.b64decode(j["content"].encode()))        

            return output_filename
        except Exception as e:
            logging.error(f"Error fetching data from ZQM Simple Storage: {e}")
            return None