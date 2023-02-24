class MissingTokenError(Exception):
    pass


class HomeConnectTimeout(Exception):
    pass


class HomeConnectRequestError(Exception):
    def __init__(self, data):
        self.data = data


class HomeConnectParsingError(Exception):
    pass


class HomeConnectConnectionClosed(Exception):
    pass
