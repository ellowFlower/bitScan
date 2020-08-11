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

        try:
            self.socket = socket.create_connection(self.to_addr)
        except (socket.error) as err:
            logging.error("Error occured: {}".format(err))

    def close(self):
        logging.info("Close connection if active.")
        if self.socket:
            self.socket.close()

    def handshake(self):
        """Send and then receive version/verrack message from a bitcoin node.

        Note:
            To send a message it must be first serialized.
            When receiving a message it must be deserialized to be readable.

        Returns: The response of the handshake in a readable format.
        """
        logging.info("Make handshake.")

        payload_version = self.serializer.serialize_version_payload(self.to_addr, self.from_addr)
        msg = self.serializer.create_message('version', payload_version)
        self.socket.sendall(msg)

        # <<< [version 124 bytes] [verack 24 bytes]
        return self.get_messages(length=148, commands=['version', 'verack'])

    def getaddr_addr(self):
        """Send getaddr and then receive addr message.

        Note:
            A getaddr message has no payload.
        """
        # getaddr
        logging.info("Send getaddr.")
        msg = self.serializer.create_message('getaddr', b'')
        self.socket.sendall(msg)

        # addr
        logging.info("Receive addr.")
        a = self.recv_addr()
        print(a)
        return a

    # TODO refactor (version and getaddr message)
    def get_messages(self, length=0, commands=None):
        """Receive data from a bitcoin node.

        Note:
            More than one message can be received. When receiving a verack message there is no payload,
            therefore only the header has to be deserialized.
            If a version message is received, send a verack message immediately.
            Because it is possible, that we receive more than the messages we want to handle further, we
            filter the response in the end.

        Args:
            length (int): Number of how many bytes we want to read.
            commands (list): List of the type of the message(s) we want to receive.

        Returns:
            A readable format of all message we got. [msg1, msg2, ...]
            msg = {<headerValues>, <payload>}
        """
        data = self.recv(length)
        data = BytesIO(data)
        msgs = []

        # read until buffer is empty or after addr message is read (because we don't know the size)
        while length > 0:
            # header
            msg = self.serializer.deserialize_header(data.read(HEADER_LEN))

            # payload
            if msg['command'] == 'version':
                msg.update({'payload':self.serializer.deserialize_version_payload(data.read(msg['length']))})
                self.socket.sendall(self.serializer.create_message('verack', b''))
            elif msg['command'] == 'addr':
                msg.update({'payload':self.serializer.deserialize_addr_payload(data.read(msg['length']))})
                break

            msgs.append(msg)
            length -= (HEADER_LEN + msg['length'])

        # filter response
        if len(msgs) > 0 and commands:
            msgs[:] = [m for m in msgs if m.get('command') in commands]

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

    def recv_addr(self):
        """Receive data until addr message ocurs. Then return addr message.

        Note:
             An addr message it at most 30000 bytes long.
        """
        data = b''
        msg = []
        while True:
            chunk = self.socket.recv(HEADER_LEN)
            data = BytesIO(chunk)

            helper = self.serializer.deserialize_header(data.read(HEADER_LEN))

            # check if addr message
            if helper['command'] == 'addr':
                msg = helper
                chunk = self.socket.recv(msg['length'])
                data = BytesIO(chunk)
                msg.update({'payload': self.serializer.deserialize_addr_payload(data.read(msg['length']))})
                break
            else:
                chunk = self.socket.recv(helper['length'])
                data = BytesIO(chunk)
                not_used = data.read(helper['length'])

        return msg
