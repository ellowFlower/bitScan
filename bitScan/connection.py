import re
import socket
import logging
import time

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
        handshake_done (bool): Indicates if the handshake with the bitcoin node was successful.
    """

    def __init__(self, to_addr):
        logging.info(f'CONN Create connection to {to_addr[0]},{to_addr[1]}.')

        self.to_addr = to_addr
        self.from_addr = ('0.0.0.0', 0)
        self.serializer = Serializer()
        self.socket = None
        self.handshake_done = False

    def open(self):
        """Create connection to a bitcoin node.

        Note:
            The address of the bitcoin node is taken from to_addr. The active connection is accesible
            through self.socket.
        """
        logging.info('CONN Open connection.')
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
        logging.info("CONN Make handshake.")

        payload_version = self.serializer.serialize_version_payload(self.to_addr, self.from_addr)
        msg = self.serializer.create_message('version', payload_version)
        self.socket.sendall(msg)

        # <<< [header version 24 bytes][version 102 bytes] [verack 24 bytes]
        return self.get_messages(length=150, commands=['version', 'verack'])

    def send_getaddr(self):
        """Send getaddr message.

        Note:
            A getaddr message has no payload.
        """
        logging.info("CONN Send getaddr.")

        payload = ''

        # getaddr
        logging.info("Send getaddr.")
        msg = self.serializer.create_message('getaddr', b'')
        self.socket.sendall(msg)

    def get_messages(self, length=0, commands=None):
        """Receive data from a bitcoin node.

        Note:
            More than one message can be received. When receiving a verack message there is no payload,
            therefore only the header has to be deserialized.
            If a version message is received, send a verack message immediately.
            Because it is possible, that we receive more than the messages we want to handle further, we
            filter the response in the end.
            Is only used for version/verack

        Args:
            length (int): Number of how many bytes we want to read.
            commands (list): List of the type of the message(s) we want to receive.

        Returns:
            A readable format of all message we got. [msg1, msg2, ...]
            msg = {<headerValues>, <payload>}
        """
        logging.info("CONN Receive data from a bitcoin node.")

        data, current_time = self.recv(length)
        length = len(data)
        data = BytesIO(data)
        msgs = []

        # read until buffer is empty or after addr message is read (because we don't know the size)
        while length > 0:
            msg = self.serializer.deserialize_header(data.read(HEADER_LEN))

            if (length - HEADER_LEN) < msg['length']:
                raise HandshakeContentError(
                    "Payload is to short. Got {} of {} bytes".format(length, HEADER_LEN + msg['length']))

            if MAGIC_NUMBER_COMPARE != msg['magic_number']:
                raise HandshakeContentError(
                    "Wrong magic value. Is {}, should be ".format(msg['magic_number'], MAGIC_NUMBER_COMPARE))

            payload = data.read(msg['length'])
            computed_checksum = sha256_util(sha256_util(payload))[:4]
            if computed_checksum != msg['checksum']:
                raise HandshakeContentError(
                    "Invalid checksum. {} != {}".format(hexlify(computed_checksum), hexlify(msg['checksum'])))

            if msg['command'] == 'version':
                msg.update({'payload': self.serializer.deserialize_version_payload(payload)})
                self.socket.sendall(self.serializer.create_message('verack', b''))
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

        if received.sort() == ['verack', 'version']:
            self.handshake_done = True

        return msgs

    def recv(self, length=0):
        """Receive length data from a socket.

        Args:
            length (int): number of how many bytes we want to read

        Returns:
            The receive data in bytes and the current time when receiving the data
        """
        logging.info("CONN Receive length data from a socket.")

        current_time = -1
        if length > 0:
            data = b''
            # receive until length for wanted message is reached
            while length > 0:
                chunk = self.socket.recv(SOCKET_BUFFER)

                if not chunk:
                    time.sleep(5)
                    chunk = self.socket.recv(SOCKET_BUFFER)
                    if not chunk:
                        raise RemoteHostClosedConnection("{} closed connection".format(self.to_addr))

                data += chunk
                length -= len(chunk)
        else:
            current_time = time.time()
            data = self.socket.recv(SOCKET_BUFFER)

            if not data:
                time.sleep(5)
                data = self.socket.recv(SOCKET_BUFFER)
                if not data:
                    raise RemoteHostClosedConnection("{} closed connection".format(self.to_addr))

        return data, current_time

    def communicate(self, time_minutes, content_addr_msg, interval_getaddr=-1, interval_addr=-1):
        """Send getaddr and addr messages in a time interval and listen permanently for incoming addr messages.

        Note:
            If something went wrong during receiving or reading the data then continue with next while round.

        Args:
            time_minutes (int): The amount of time how long we want to listen on the socket. In minutes.
            content_addr_msg (list): The content of the addr message.
            interval_getaddr (int): Interval in minutes when we send getaddr messages. -1 implies we never want to send.
            interval_addr (int): Interval in minutes when we send addr messages. -1 implies we never want to send.

        Returns:
            (tuple): tuple containing:
                unpacked_addr_msgs (str): The received addresses from voluntary addr messages in a readable format.
                unpacked_getaddr_msgs (str): The received addresses from responses to getaddr messages in a readable format.
        """
        logging.info("CONN Start communication.")

        data_buffer = b''
        unpacked_addr_msgs = ''
        unpacked_getaddr_msgs = ''
        time_begin = time.time()
        timeout = time_begin + 60 * time_minutes
        last_sent_getaddr = -1
        last_sent_addr = -1
        current_time = -1

        while time.time() < timeout:
            try:
                current_time = time.time()
                data = self.socket.recv(8192)
                if not data:
                    time.sleep(5)
                    current_time = time.time()
                    data = self.socket.recv(8192)
                    if not data:
                        break

                data_buffer += data

                # get minutes
                now = time.gmtime()[4]
                if interval_getaddr != -1 and now != last_sent_getaddr and (
                        now - time.gmtime(time_begin)[4]) % interval_getaddr == 0:
                    last_sent_getaddr = now
                    self.send_getaddr()

                if interval_addr != -1 and now != last_sent_addr and (
                        now - time.gmtime(time_begin)[4]) % interval_addr == 0:
                    last_sent_addr = now
                    self.send_addr(content_addr_msg)

                data_split = data_buffer.split(MAGIC_NUMBER_COMPARE)
                length_data_split = len(data_split)
                for idx, msg in enumerate(data_split):
                    if idx != (len(data_split) - 1):
                        # whole message can be read
                        if re.compile(b'^addr').match(msg):
                            response, is_getaddr_response = self.get_deserialized_addr_message(msg, current_time)
                            if is_getaddr_response:
                                unpacked_getaddr_msgs += response
                            else:
                                unpacked_addr_msgs += response
                    else:
                        # last index; message may be continued
                        data_buffer = msg
            except MessageContentError as err:
                data_buffer = b''
                logging.error(
                    "Error occurred in connection with bitcoin node {},{}: {}".format(self.to_addr[0], self.to_addr[1],
                                                                                      err))
                continue

        # deserialize last message received if addr
        if re.compile(b'^addr').match(data_buffer):
            try:
                response, is_getaddr_response = self.get_deserialized_addr_message(data_buffer, current_time)
                if is_getaddr_response:
                    unpacked_getaddr_msgs += response
                else:
                    unpacked_addr_msgs += response
            except MessageContentError as err:
                logging.error(
                    "Error occurred in connection with bitcoin node {},{}: {}".format(self.to_addr[0], self.to_addr[1],
                                                                                     err))
                return unpacked_addr_msgs, unpacked_getaddr_msgs

        return unpacked_addr_msgs, unpacked_getaddr_msgs

    def get_deserialized_addr_message(self, msg, current_time):
        """Calls all functions to deserialize an addr message

        Note:
            the parameter msg contains NO magic number.

        Args:
            msg (bytes): the content of the message.
            current_time (float): The time when the message was received.

        Returns:
            addr messages in a readable format
        """
        logging.info("CONN Get deserialized addr message.")

        if msg != b'':
            msg = BytesIO(msg)
            header = self.serializer.deserialize_header(MAGIC_NUMBER_COMPARE + msg.read(HEADER_LEN - 4))
            payload_addr = msg.read(header['length'])
            return self.serializer.deserialize_addr_payload(payload_addr, current_time, self.to_addr[0],
                                                            str(self.to_addr[1]))

        return ''

    def send_addr(self, addresses):
        """Send addr message.

        Args:
            addresses (list): The content of the addr message.
        """
        logging.info("CONN Send addr.")
        payload_addr = self.serializer.serialize_addr_payload(addresses)
        msg = self.serializer.create_message('addr', payload_addr)
        self.socket.sendall(msg)
