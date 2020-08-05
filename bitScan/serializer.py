import logging
import struct
import time
import socket
import random
import hashlib

from bitScan.utils import create_sub_version


class Serializer(object):
    """Handles serialization and deserialization.

    Args:
        to_addr ((str, int)): Address of the bitcoin node we connect to in the form (ip, port).

    Attributes:
        magic_number (str): Bitcoin networks magic number.
        protocol_version (int): Bitcoin protocol version.
    """
    def __init__(self):
        logging.info('Create serialize object.')
        self.magic_number = 0xd9b4bef9
        self.protocol_version = 70015
        self.to_services = 1
        self.from_services = 0

    def create_message(self, command, payload):
        """Create full message which can be send to a bitcoin node.

        Args:
            command (str): The command type for the message. E.g: 'version'.
            payload (struct.pack): Content is the already packed payload of the message

        Returns:
            The message as bytes which can be sent to a bitcoin node.
        """
        checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[0:4]
        return struct.pack('L12sL4s', self.magic_number, command.encode(), len(payload), checksum) + payload

    def serialize_network_address(self, addr):
        """Serialize (pack) a network address.

        Args:
            addr ((str, int)): The address which is to be packed

        Returns:
            The packed address
        """
        network_address = struct.pack('>8s16sH', b'\x01',
                                      bytearray.fromhex("00000000000000000000ffff") + socket.inet_aton(addr[0]),
                                      addr[1])
        return network_address

    def serialize_version_payload(self, to_addr, from_addr):
        """Serialize the payload for a version message.

        Args:
            to_addr ((str, int)): Source address
            from_addr ((str, int)): Address of a bitcoin node

        Returns:
            The packed address
        """
        timestamp = int(time.time())
        source_addr = self.serialize_network_address(from_addr)
        peer_addr = self.serialize_network_address(to_addr)
        nonce = random.getrandbits(64)

        payload = struct.pack('<LQQ26s26sQ16sL', self.protocol_version, self.to_services, timestamp, peer_addr,
                              source_addr, nonce, create_sub_version(), 0)

        return payload


