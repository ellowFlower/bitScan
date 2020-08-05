import socket
import logging

from bitScan.serializer import Serializer


class Connection(object):
    """Handles the connection to a bitcoin node.

    Args:
        to_addr ((str, int)): Address of the bitcoin node we connect to in the form (ip, port).

    Attributes:
        to_addr ((str, int)): Address of the bitcoin node we connect to in the form (ip, port).
        from_addr (str, int): Our address where we make the connection to the bitcoin node in the form (ip, port).
        serializer (obj): Serializer object for this connection.
        socket (obj): Socket for communication with a bitcoin node.
    """
    def __init__(self, to_addr):
        logging.info('Create connection object.')

        self.to_addr = to_addr
        self.from_addr = ('0.0.0.0', 0)
        # TODO Maybe not necessary to use a own serializer object for every connection
        self.serializer = Serializer()
        self.socket = None

    def open(self):
        """Create connection to a bitcoin node.

        Note:
            The address of the bitcoin node is taken from to_addr. The active connection is accesible
            through self.socket.
        """
        logging.info('Open connection.')

        self.socket = socket.create_connection(self.to_addr)

    def close(self):
        logging.info("Close connection if active.")
        if self.socket:
            self.socket.close()

    def handshake(self):
        """Send and then receive version/verrack message from a bitcoin node.

        Note:
            To send a message it must be first serialized.
            When receiving a message it must be deserialized to be readable.
        """
        payload_version = self.serializer.serialize_version_payload(self.to_addr, self.from_addr)
        msg = self.serializer.create_message('version', payload_version)
        self.send(msg)

    def send(self, data):
        self.socket.sendall(data)
