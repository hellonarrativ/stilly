class Message:
    def __init__(self, destination: str='', body: dict=None) -> None:
        self.destination = destination
        self.body = body or {}

    def __repr__(self) -> str:
        return '<{} destination={} body={}>'.format(
            self.__class__.__name__,
            self.destination,
            self.body,
        )


class ShutdownMessage(Message):
    def __init__(self, destination: str) -> None:
        super().__init__(destination=destination)


class HeartbeatMessage(Message):
    def __init__(self, destination: str, heartbeat_address: str='') -> None:
        super().__init__(destination=destination)
        self.heartbeat_address = heartbeat_address


class RequestMessage(Message):
    def __init__(self, destination: str, return_address: str, return_id: str,
                 body: dict):
        super().__init__(destination=destination, body=body)
        self.return_address = return_address
        self.return_id = return_id


class ResponseMessage(Message):
    def __init__(self, destination: str, return_id: str,
                 body: dict):
        super().__init__(destination=destination, body=body)
        self.return_id = return_id