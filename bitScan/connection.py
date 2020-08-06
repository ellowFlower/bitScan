import socket
import logging
import time

from collections import deque
from io import BytesIO
from bitScan.serializer import Serializer
from bitScan.utils import *
from bitScan.exception import PayloadTooShortError, RemoteHostClosedConnection



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
        self.bps = deque([], maxlen=128)  # bps samples for this connection

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
        print('request: ' + str(msg))
        self.socket.sendall(msg)

        # <<< [version 124 bytes]
        response = self.get_messages(length=124)
        print('response: ' + str(response))

    def get_messages(self, length=0):
        """Receive data from a bitcoin node.

        Note:
            More than one message can be received

        Args:
            length (int): number of how many bytes we want to read

        Returns:
            A readable format of all message we got. [msg1, msg2, ...]
            msg = {<headerValues>, <payload>}
        """
        msgs = []
        data = self.recv(length)
        data = BytesIO(data)

        # header
        msg = self.serializer.deserialize_header(data.read(HEADER_LEN))

        # payload
        if msg['command'] == 'version':
            msg.update({'payload':self.serializer.deserialize_version_payload(data.read(msg['length']))})

        msgs.append(msg)
        return msgs

    def recv(self, length=0):
        """Receive length data from a socket.

        Args:
            length (int): number of how many bytes we want to read

        Returns:
            The receive data in bytes.
        """
        if length > 0:
            data = b''
            # receive until length for wanted message is reached
            while length > 0:
                chunk = self.socket.recv(SOCKET_BUFSIZE)

                if not chunk:
                    raise RemoteHostClosedConnection("{} closed connection".format(self.to_addr))

                data += chunk
                length -= len(chunk)
        else:
            data = self.socket.recv(SOCKET_BUFSIZE)

            if not data:
                raise RemoteHostClosedConnection("{} closed connection".format(self.to_addr))

        return data
