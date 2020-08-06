class ConnectionError(Exception):
    pass

class PayloadTooShortError(Exception):
    pass

class RemoteHostClosedConnection(Exception):
    pass

class HeaderTooShortError(Exception):
    pass

class InvalidPayloadChecksum(Exception):
    pass

class InvalidMagicNumberError(Exception):
    pass

class IncompatibleClientError(Exception):
    pass

class ReadError(Exception):
    pass