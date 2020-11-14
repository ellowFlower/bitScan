import logging
import time
import socket
import random
from io import BytesIO
from base64 import b32encode, b32decode

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
        from_services (int): Services bitcoin node offers.
        height (int): Indicates which block our node is synced up to.
        relay (int): Indicates bitcoin nodes relaying.
    """
    def __init__(self):
        logging.info('SER Create serialize object.')
        self.magic_number = 0xd9b4bef9  # 0xd9b4bef9 0xfabfb5da 0x0b110907
        self.protocol_version = 70015
        self.from_services = 0
        self.height = 0
        self.relay = 0

    def create_message(self, command, payload):
        """Create full message which can be send to a bitcoin node.

        Args:
            command (str): The command type for the message. E.g: 'version'.
            payload (bytes): Content is the already packed payload of the message

        Returns:
            bytes: The message as bytes which can be sent to a bitcoin node.
        """
        checksum = sha256_util(sha256_util(payload))[:4]

        return struct.pack('I', self.magic_number) + str.encode(command + "\x00" * (12 - len(command))) +\
               struct.pack('<I', len(payload)) + checksum + payload

    def serialize_network_address_version(self, addr):
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
        logging.info('SER Serialize network address.')

        if '.' in addr[0]:
            # ipv4; unused (12 bytes) + ipv4 (4 bytes) = ipv4-mapped ipv6 address
            host = bytearray.fromhex("00000000000000000000ffff") + socket.inet_aton(addr[0])
        elif ':' in addr[0] and not addr[0].endswith('.onion'):
            # ipv6; ipv6 (16 bytes)
            host = socket.inet_pton(socket.AF_INET6, addr[0])
        else:
            raise ConnectionError("Host is in the wrong format. Must be ipv4 or ipv6 but is {}".format(addr[0]))

        return struct.pack("<Q", 1) + struct.pack('>16sH', host, addr[1])

    def serialize_version_payload(self, to_addr, from_addr):
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
        logging.info('SER Serialize version payload.')

        timestamp = int(time.time())
        source_addr = self.serialize_network_address_version(from_addr)
        peer_addr = self.serialize_network_address_version(to_addr)
        nonce = random.getrandbits(64)

        return struct.pack('<iQq26s26sQ16si?', self.protocol_version, self.from_services, timestamp, peer_addr,
                              source_addr, nonce, create_sub_version(), self.height, self.relay)

    def serialize_addr_payload(self, addr_list):
        """Serialize the payload for a addr message.

        Notes:
            Addr message consists of count and a list of addresses of the network.

        Args:
            addr_list (list): These addresses are the content for the messages.

        Returns:
            bytes: The packed address
        """
        logging.info('SER Serialize addr payload.')

        packed_addresses = b''
        for x in addr_list:
            packed_addresses += self.serialize_network_address_values_given(x)

        return self.serialize_int(len(addr_list)).encode('latin-1') + packed_addresses

    def serialize_network_address_values_given(self, address):
        """Serialize (pack) a network address when values are given.

        Args:
            address (list): The content of the address.

        Returns:
            bytes: The packed address
        """
        logging.info('SER Serialize network address values given.')

        ip = address[2]
        if '.' in ip:
            # ipv4; unused (12 bytes) + ipv4 (4 bytes) = ipv4-mapped ipv6 address
            host = bytearray.fromhex("00000000000000000000ffff") + socket.inet_aton(ip)
        elif ':' in ip and not ip.endswith('.onion'):
            # ipv6; ipv6 (16 bytes)
            host = socket.inet_pton(socket.AF_INET6, ip)
        elif ip.endswith(".onion"):
            # convert .onion address to its ipv6 equivalent (6 + 10 bytes)
            host = ONION_PREFIX + b32decode(ip[:-6], True)
        else:
            # the address was not in the correct format, therefore return empty bytes
            return b''

        return struct.pack('<I', int(address[0])) + struct.pack("<Q", int(address[1])) + struct.pack('>16sH', host, int(address[3]))

    def deserialize_header(self, data):
        """Deserialize header of a message.

        Note:
            Header contains: magic number, command, length of payload, checksum.
            data.read returns a empty byte object if there is nothing to read.

        Args:
            data (bytes): Header content

        Returns:
            dict: Dictionary with all the content from the header in a readable format.
        """
        logging.info('SER Deserialize header.')

        data = BytesIO(data)
        return {'magic_number': data.read(4), 'command': data.read(12).strip(b"\x00").decode("latin-1"),
               'length': unpack_util("<I", data.read(4)), 'checksum': data.read(4)}

    def deserialize_version_payload(self, data):
        """Deserialize version payload.

        Note:
            payload contains: version, services, timestamp, to_addr, from_addr, nonce, user agent, height, relay

        Args:
            data (bytes): Payload content

        Returns:
            dict: timestamp and the address we receive the version message from
        """
        logging.info('SER Deserialize version payload.')

        data = BytesIO(data)
        msg = {}

        # version; not used
        unpack_util("<i", data.read(4))
        # services; not used
        unpack_util("<Q", data.read(8))
        msg['timestamp'] = unpack_util("<q", data.read(8))
        msg['address'] = self.deserialize_network_address(data)
        # from_addr; not used
        self.deserialize_network_address(data)
        # nonce; not used
        unpack_util("<Q", data.read(8))
        # user agent; not used
        self.deserialize_string(data)
        # height; not used
        unpack_util("<i", data.read(4))

        try:
            # relay; not used
            struct.unpack("<?", data.read(1))[0]
        except struct.error:
            pass

        return msg

    def deserialize_addr_payload(self, data, current_time, connected_host, connected_port):
        """Deserialize addr payload.

        Note:
            The original payload contains: count, one or multiple addresses

        Args:
            data (bytes): Payload content
            current_time (float)
            connected_host (str): Host for current connection
            connected_port (str): ort for current connection

        Returns:
            str: Which contains for every address we got host, port, timestamp, time we received the addr message.
                After each address is a newline.
        """
        logging.info('SER Deserialize addr payload.')

        data = BytesIO(data)
        msg = ''
        is_getaddr_response = False

        count = self.deserialize_int(data)
        if count > 10:
            is_getaddr_response = True
        for _ in range(count):
            msg += connected_host + ',' + connected_port + ',' + self.deserialize_network_address(data, has_timestamp=True) + ',' + str(current_time) + '\n'

        return msg, is_getaddr_response

    def deserialize_network_address(self, data, has_timestamp=False):
        """Deserialize network address.

        Note:
            Network address contains: [timestamp], services, ipv4, ipv6, onion, port.
            One of ipv4, ipv6 and onion has a value.

        Args:
            data (BytesIO): Network address content.
            has_timestamp (bool): Indicates if a timestamp exists.

        Returns:
            str: host, port[, timestamp]
        """
        logging.info('SER Deserialize nerwork address.')

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

        if _ipv6[:6] == ONION_PREFIX:
            host = b32encode(_ipv6[6:]).lower() + b".onion"  # use .onion
        else:
            ipv6 = socket.inet_ntop(socket.AF_INET6, _ipv6)
            ipv4 = socket.inet_ntop(socket.AF_INET, _ipv4)
            if ipv4 in ipv6:
                host = ipv4
            else:
                host = ipv6

        if has_timestamp:
            return '{},{},{}'.format(host, port, timestamp)
        else:
            return '{},{}'.format(host, port)

    def deserialize_string(self, data):
        """Deserialize a string.

        Args:
            data (bytes): Network address content.

        Returns:
            dict: Dictionary with all the content from the network address in a readable format.
        """
        logging.info('SER Deserialize string.')

        length = self.deserialize_int(data)
        return data.read(length).decode('utf-8')

    def deserialize_int(self, data):
        """
        Args:
            data (BytesIO): Network address content.

        Returns:
            int: Length of given data
        """
        logging.info('SER Deserialize int.')

        length = unpack_util("<B", data.read(1))
        if length == 0xFD:
            length = unpack_util("<H", data.read(2))
        elif length == 0xFE:
            length = unpack_util("<I", data.read(4))
        elif length == 0xFF:
            length = unpack_util("<Q", data.read(8))
        return length

    def serialize_int(self, length):
        if length < 0xFD:
            return chr(length)
        elif length <= 0xFFFF:
            return chr(0xFD) + str(struct.pack("<H", length))
        elif length <= 0xFFFFFFFF:
            return chr(0xFE) + str(struct.pack("<I", length))
        return chr(0xFF) + str(struct.pack("<Q", length))


