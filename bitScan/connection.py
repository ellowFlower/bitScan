import socket
import logging
from binascii import hexlify

from collections import deque
from io import BytesIO
import time

from bitScan.serializer import Serializer
from bitScan.utils import *
from bitScan.exception import PayloadTooShortError



class Connection(object):
    """Handles the connection to a bitcoin node.

    Args:
        to_addr ((str, int)): Address of the bitcoin node we connect to in the form (ip, port).

    Attributes:
        to_addr (tuple): tuple containing:
            host (str): Host
            port (int): Port
        from_addr (tuple): tuple containing:
            host (str): Host
            port (int): Port
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
        # works for ipv4 and ipv6
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

        Returns:
            list: The response of the handshake in a readable format.
        """
        logging.info("Make handshake.")

        payload_version = self.serializer.serialize_version_payload(self.to_addr, self.from_addr)
        msg = self.serializer.create_message('version', payload_version)
        self.socket.sendall(msg)

        # <<< [header version 24 bytes][version 102 bytes] [verack 24 bytes]
        return self.get_messages(length=150, commands=['version', 'verack'])

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
        return self.get_messages(commands=['addr'])

    def get_messages(self, length=0, commands=None):
        """Receive data.

        Note:
            More than one message can be received. When receiving a verack message there is no payload,
            therefore only the header has to be deserialized.
            If a version message is received, send a verack message immediately.

        Args:
            length (int): Number of how many bytes we want to read.
            commands (list): List of the type of the message(s) we want to receive. If 'addr' is in it, it must be the only entry.

        Returns:
            list: A readable format of all message we got. [msg1, msg2, ...]; msg = {<headerValues>, <payload>}
        """
        data = b''
        msgs = []

        while length > 0 or commands[0] == 'addr':
            # header
            print('receive header')
            chunk = self.socket.recv(HEADER_LEN)
            print('receive header')
            data = BytesIO(chunk)

            msg = self.serializer.deserialize_header(data.read(HEADER_LEN))

            if (length - HEADER_LEN) < msg['length'] and commands[0] != 'addr':
                raise PayloadTooShortError("Payload is to short. Got {} of {} bytes".format(length, HEADER_LEN + msg['length']))

            # payload
            print('receive payload')
            chunk = self.socket.recv(msg['length'])
            data = BytesIO(chunk)
            payload = data.read(msg['length'])

            computed_checksum = sha256_util(sha256_util(payload))[:4]
            if computed_checksum != msg['checksum']:
                raise InvalidPayloadChecksum("Invalid checksum. {} != {}".format(hexlify(computed_checksum), hexlify(msg['checksum'])))

            # check if addr message
            if msg['command'] == 'addr':
                msg.update({'payload': self.serializer.deserialize_addr_payload(payload)})
                msgs.append(msg)
                break
            elif msg['command'] == 'version':
                msg.update({'payload':self.serializer.deserialize_version_payload(payload)})
                msgs.append(msg)
                self.socket.sendall(self.serializer.create_message('verack', b''))
            elif msg['command'] == 'verack':
                msgs.append(msg)

            length -= (HEADER_LEN + msg['length'])

        return msgs
