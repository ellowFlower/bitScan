import hashlib
import struct
from bitScan.exception import *

BUFFER_SIZE = 1024
ONION_PREFIX = "\xFD\x87\xD8\x7E\xEB\x43"  # ipv6 prefix for .onion address
HEADER_LEN = 24
MIN_PROTOCOL_VERSION = 70001
SOCKET_BUFSIZE = 8192


def create_sub_version():
    """Binary encode the sub-version

    Returns: Binary encodes sub-version as bytes
    """
    sub_version = "/Satoshi:0.7.2/"
    return b'\x0F' + sub_version.encode()


def print_request_and_response(command, request_data, response_data):
    print("")
    print("Command: " + command)
    print("Request:")
    print(request_data)
    print("Response:")
    print(response_data)


def sha256_util(data):
    return hashlib.sha256(data).digest()


def unpack_util(fmt, data, str = ''):
    """Wraps problematic struct.unpack() in a try statement

    Args:
        fmt (str): The form which is used for unpacking
        data (byte): The string which is unpacked.

    Returns: Unpacked data, which should be readable.
    """
    try:
        return struct.unpack(fmt, data)[0]
    except struct.error as err:
        raise ReadError(err)

