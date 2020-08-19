import socket
import logging
import time

from collections import deque
from io import BytesIO
from binascii import hexlify

from bitScan.serializer import Serializer
from bitScan.utils import *



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
        time.sleep(1)
        logging.info("Receive addr.")
        return self.get_messages(commands=['addr'])

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
        data, current_time = self.recv(length)
        length = len(data)
        data = BytesIO(data)
        msgs = []

        # read until buffer is empty or after addr message is read (because we don't know the size)
        while length > 0:
            # header
            msg = self.serializer.deserialize_header(data.read(HEADER_LEN))

            # check values (exception handling)
            # TODO maybe put it in a own function bec of readability
            if (length - HEADER_LEN) < msg['length']:
                raise MessageContentError(
                    "Payload is to short. Got {} of {} bytes".format(length, HEADER_LEN + msg['length']))

            if MAGIC_NUMBER_COMPARE != msg['magic_number']:
                raise MessageContentError(
                    "Wrong magic value. Is {}, should be ".format(msg['magic_number'], MAGIC_NUMBER_COMPARE))

            # payload
            payload = data.read(msg['length'])
            computed_checksum = sha256_util(sha256_util(payload))[:4]
            if computed_checksum != msg['checksum']:
                raise MessageContentError("Invalid checksum. {} != {}".format(hexlify(computed_checksum), hexlify(msg['checksum'])))

            if msg['command'] == 'version':
                msg.update({'payload':self.serializer.deserialize_version_payload(payload)})
                self.socket.sendall(self.serializer.create_message('verack', b''))
            elif msg['command'] == 'addr':
                # we get a string here
                msg.update({'payload':self.serializer.deserialize_addr_payload(payload, current_time)})
            else:
                unused_chunk = payload

            msgs.append(msg)
            length -= (HEADER_LEN + msg['length'])

        # filter response
        if len(msgs) > 0 and commands:
            msgs[:] = [m for m in msgs if m.get('command') in commands]

        # log output
        received = []
        received[:] = [x.get('command') for x in msgs]
        logging.info('Received messages: {}'.format(received))

        return msgs

    def recv(self, length=0):
        """Receive length data from a socket.

        Args:
            length (int): number of how many bytes we want to read

        Returns:
            The receive data in bytes and the current time when receiving the data
        """
        # TODO save time when receive message
        # maybe this function is unecessary because when we listen for addr messages passively we also receive the messages
        current_time = -1
        if length > 0:
            data = b''
            # receive until length for wanted message is reached
            while length > 0:
                chunk = self.socket.recv(SOCKET_BUFFER)

                if not chunk:
                    raise RemoteHostClosedConnection("{} closed connection".format(self.to_addr))

                data += chunk
                length -= len(chunk)
        else:
            # addr messages go here immediately
            # time in seconds as floating point number; only relevant for addr messages
            current_time = time.time()
            data = self.socket.recv(SOCKET_BUFFER)

            if not data:
                raise RemoteHostClosedConnection("{} closed connection".format(self.to_addr))

        return data, current_time
