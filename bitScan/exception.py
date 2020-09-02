class ConnectionError(Exception):
    pass


class RemoteHostClosedConnection(Exception):
    pass


class MessageContentError(Exception):
    pass


class HandshakeContentError(Exception):
    pass
