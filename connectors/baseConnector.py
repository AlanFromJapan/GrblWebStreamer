class BaseConnector():
    def __init__(self) -> None:
        pass

    # Fetches the latest data from the connector, returns filename if successful, None if no data
    def fetchLatest(self) -> str:
        pass