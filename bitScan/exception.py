class ConnectionError(Exception):
    """General errors during connection
    """
    pass


class RemoteHostClosedConnection(Exception):
    """Assuming remote host closed the connection

    Note:
        When this error happens, close connection on our side.
    """
    pass


class MessageContentError(Exception):
    """Error in message content
    """
    pass


class HandshakeContentError(Exception):
    """Error while doing handshake

    Note:
        When this error happens, start handshake again from the beginning.
    """
    pass


class PingError(Exception):
    pass
