import unittest

from bitScan.connection import Connection


class ConnectionTestCase(unittest.TestCase):
    def setUp(self):
        self.conn = Connection(('127.0.0.1', 18444))

    def test_default_handshake(self):
        """
        Notes:
            Within the function handshake serializer.serialize_version_payload, serialize_network_address,
            serializer.create_message, connection.get_messages, serializer.deserialize_header,
            deserialize_version_payload are called and therefore semi tested within this test.

            The outcome should be:
                [{'magic_number': b'\xfa\xbf\xb5\xda', 'command': 'version', 'length': 102, 'checksum': b'\x13+\x07\xf2', 'payload': {'version': 70015, 'services': 409, 'timestamp': 1596794043, 'to_addr': {'timestamp': None, 'services': 0, 'ipv4': '127.0.0.1', 'ipv6': '', 'onion': '', 'port': 18444}, 'from_addr': {'timestamp': None, 'services': 1033, 'ipv4': '', 'ipv6': '::', 'onion': '', 'port': 0}, 'nonce': 615169444417225228, 'user_agent': '/Satoshi:0.20.0/', 'height': 643071, 'relay': True}}, {'magic_number': b'\xfa\xbf\xb5\xda', 'command': 'verack', 'length': 0, 'checksum': b'\x13+\x07\xf2'}]
        """
        self.assertEqual(self.conn.handshake(), "[{'magic_number': b'\xfa\xbf\xb5\xda', 'command': 'version', 'length': 102, 'checksum': b'\x13+\x07\xf2', 'payload': {'version': 70015, 'services': 409, 'timestamp': 1596794043, 'to_addr': {'timestamp': None, 'services': 0, 'ipv4': '127.0.0.1', 'ipv6': '', 'onion': '', 'port': 18444}, 'from_addr': {'timestamp': None, 'services': 1033, 'ipv4': '', 'ipv6': '::', 'onion': '', 'port': 0}, 'nonce': 615169444417225228, 'user_agent': '/Satoshi:0.20.0/', 'height': 643071, 'relay': True}}, {'magic_number': b'\xfa\xbf\xb5\xda', 'command': 'verack', 'length': 0, 'checksum': b'\x13+\x07\xf2'}]")

    def tearDown(self):
        self.conn.close()
