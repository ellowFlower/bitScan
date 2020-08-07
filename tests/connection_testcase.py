import unittest

class ConnectionTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def test_default_handshake(self):
        """
        Notes:
            Within the function handshake serializer.serialize_version_payload, serialize_network_address,
            serializer.create_message, connection.get_messages, serializer.deserialize_header,
            deserialize_version_payload are called and therefore semi tested within this test.

            -- Test format of the outcome which should be: [{<message1>}, {<message2>}, ...]
            -- Test the outcome. (Maybe with a own created local bitcoin regtestnet)
        """
        pass

