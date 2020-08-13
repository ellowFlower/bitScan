import logging
import time
import socket
import random
from io import BytesIO
from base64 import b32encode

from bitScan.utils import *
from bitScan.exception import *

"""Reference for the content of the messages: https://en.bitcoin.it/wiki/Protocol_documentation"""


class Serializer(object):
    """Handles serialization and deserialization.

    Args:
        to_addr (tuple): tuple containing:
            host (str): Host
            port (int): Port

    Attributes:
        magic_number (str): Bitcoin networks magic number.
        protocol_version (int): Bitcoin protocol version.
    """
    def __init__(self):
        logging.info('Create serialize object.')
        # TODO change if running on real network
        self.magic_number = 0xfabfb5da  # 0xd9b4bef9 0xfabfb5da 0x0b110907
        self.protocol_version = 70015
        self.to_services = 1
        self.from_services = 0
        self.user_agent = '/bitnodes.io:0.1/'
        self.height = 478000
        self.relay = 0
        # This is set prior to throwing PayloadTooShortError exception to
        # allow caller to fetch more data over the network.
        self.required_len = 0

    def create_message(self, command, payload, test=False):
        """Create full message which can be send to a bitcoin node.

        Note:
            Using the test argument to used the same checksum for two different calls of this method.
            Therefore we can compare the outcome.

        Args:
            command (str): The command type for the message. E.g: 'version'.
            payload (bytes): Content is the already packed payload of the message
            test (bool): Indicate if the function is used in a test

        Returns:
            bytes: The message as bytes which can be sent to a bitcoin node.
        """
        checksum = sha256_util(sha256_util(payload))[:4]

        if test:
            checksum = b'\x13+\x07\xf2'

        return struct.pack('I', self.magic_number) + str.encode(command + "\x00" * (12 - len(command))) +\
               struct.pack('<I', len(payload)) + checksum + payload

    def serialize_network_address(self, addr):
        """Serialize (pack) a network address.

        Note:
            This function is only used by for sending a version message. Therefore the first entry in
            the returned message is the service number and not a timestamp.

        Args:
            addr (tuple): tuple containing:
                host (str): Host
                port (int): Port

        Returns:
            bytes: The packed address
        """
        if '.' in addr[0]:
            # ipv4; unused (12 bytes) + ipv4 (4 bytes) = ipv4-mapped ipv6 address
            host = bytearray.fromhex("00000000000000000000ffff") + socket.inet_aton(addr[0])
        elif ':' in addr[0] and not addr[0].endswith('.onion'):
            # ipv6; ipv6 (16 bytes)
            host = socket.inet_pton(socket.AF_INET6, addr[0])
        else:
            raise ConnectionError("Host is in the wrong format. Must be ipv4 or ipv6 but is {}".format(addr[0]))

        return struct.pack("<Q", 1) + struct.pack('>16sH', host, addr[1])

    def serialize_version_payload(self, to_addr, from_addr, test=False):
        """Serialize the payload for a version message.

        Args:
            to_addr (tuple): tuple containing:
                host (str): Host
                port (int): Port
            from_addr (tuple): tuple containing:
                host (str): Host
                port (int): Port

        Returns:
            bytes: The packed address
        """
        timestamp = int(time.time())
        source_addr = self.serialize_network_address(from_addr)
        peer_addr = self.serialize_network_address(to_addr)
        nonce = random.getrandbits(64)

        if test:
            timestamp = 1596794043
            nonce = 615169444417225228

        return struct.pack('<iQq26s26sQ16si?', self.protocol_version, self.from_services, timestamp, peer_addr,
                              source_addr, nonce, create_sub_version(), 478000, 0)

    def deserialize_header(self, data):
        """Deserialize header of a message.

        Note:
            Header contains: magic number, command, length of payload, checksum

        Args:
            data (bytes): Header content

        Returns:
            dict: Dictionary with all the content from the header in a readable format.
        """
        data = BytesIO(data)
        return {'magic_number': data.read(4), 'command': data.read(12).strip(b"\x00").decode("latin-1"),
               'length': unpack_util("<I", data.read(4), 'deserialization header length'), 'checksum': data.read(4)}

    def deserialize_version_payload(self, data):
        """Deserialize version payload.

        Note:
            payload contains: version, services, timestamp, to_addr, from_addr, nonce, user agent, height, relay

        Args:
            data (bytes): Payload content

        Returns:
            dict: Dictionary with all the content from the payload in a readable format.
        """
        data = BytesIO(data)
        msg = {}

        msg['version'] = unpack_util("<i", data.read(4))
        if msg['version'] < MIN_PROTOCOL_VERSION:
            raise IncompatibleClientError("{} < {}".format(msg['version'], MIN_PROTOCOL_VERSION))

        msg['services'] = unpack_util("<Q", data.read(8))
        msg['timestamp'] = unpack_util("<q", data.read(8))

        msg['to_addr'] = self.deserialize_network_address(data)
        msg['from_addr'] = self.deserialize_network_address(data)

        msg['nonce'] = unpack_util("<Q", data.read(8))

        msg['user_agent'] = self.deserialize_string(data)

        msg['height'] = unpack_util("<i", data.read(4))

        try:
            msg['relay'] = struct.unpack("<?", data.read(1))[0]
        except struct.error:
            msg['relay'] = False

        return msg

    def deserialize_addr_payload(self, data):
        """Deserialize addr payload.

        Note:
            payload contains: count, one or multiple addresses

        Args:
            data (bytes): Payload content

        Returns:
            dict: Dictionary with all the content from the payload in a readable format.
        """
        data = BytesIO(data)
        msg = {}

        msg['count'] = self.deserialize_int(data)
        msg['addr_list'] = []
        for _ in range(msg['count']):
            msg['addr_list'].append(self.deserialize_network_address(data, has_timestamp=True))

        return msg

    def deserialize_network_address(self, data, has_timestamp=False):
        """Deserialize network address.

        Note:
            Network address contains: timestamp, services, ipv4, ipv6, onion, port.
            One of ipv4, ipv6 and onion has a value.

        Args:
            data (bytes): Network address content.
            has_timestamp (bool): Indicates if a timestamp exists.

        Returns:
            dict: Dictionary with all the content from the network address in a readable format.
        """
        timestamp = None
        if has_timestamp:
            timestamp = unpack_util("<I", data.read(4))

        services = unpack_util("<Q", data.read(8))

        _ipv6 = data.read(12)
        _ipv4 = data.read(4)
        port = unpack_util(">H", data.read(2))
        _ipv6 += _ipv4

        ipv4 = ""
        ipv6 = ""
        onion = ""

        if _ipv6[:6] == ONION_PREFIX:
            onion = b32encode(_ipv6[6:]).lower() + b".onion"  # use .onion
        else:
            ipv6 = socket.inet_ntop(socket.AF_INET6, _ipv6)
            ipv4 = socket.inet_ntop(socket.AF_INET, _ipv4)
            if ipv4 in ipv6:
                ipv6 = ""  # use ipv4
            else:
                ipv4 = ""  # use ipv6

        return {'timestamp': timestamp, 'services': services, 'ipv4': ipv4, 'ipv6': ipv6, 'onion': onion, 'port': port}

    def deserialize_string(self, data):
        """Deserialize a string.

        Args:
            data (bytes): Network address content.

        Returns:
            dict: Dictionary with all the content from the network address in a readable format.
        """
        length = self.deserialize_int(data)
        return data.read(length).decode('utf-8')

    def deserialize_int(self, data):
        """
        Args:
            data (bytes): Network address content.

        Returns:
            int: Length of given data
        """
        length = unpack_util("<B", data.read(1))
        if length == 0xFD:
            length = unpack_util("<H", data.read(2))
        elif length == 0xFE:
            length = unpack_util("<I", data.read(4))
        elif length == 0xFF:
            length = unpack_util("<Q", data.read(8))
        return length

