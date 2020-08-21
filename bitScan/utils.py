import hashlib
import struct
from bitScan.exception import *

ONION_PREFIX = "\xFD\x87\xD8\x7E\xEB\x43"  # ipv6 prefix for .onion address
HEADER_LEN = 24
MIN_PROTOCOL_VERSION = 70001
SOCKET_BUFFER = 8192
MAGIC_NUMBER_COMPARE = b'\xf9\xbe\xb4\xd9'


def create_sub_version():
    """Binary encode the sub-version.

    Notes:
        Has length 16

    Returns:
        bytes: Binary encodes sub-version as bytes
    """
    sub_version = "/Satoshi:0.7.2/"
    return b'\x0F' + sub_version.encode()


def sha256_util(data):
    return hashlib.sha256(data).digest()


def unpack_util(fmt, data, str = ''):
    """Wraps problematic struct.unpack() in a try statement

    Args:
        fmt (str): The form which is used for unpacking
        data (bytes): The string which is unpacked.

    Returns:
        Unpacked data, which should be readable.
    """
    try:
        return struct.unpack(fmt, data)[0]
    except struct.error as err:
        raise MessageContentError(err)


def append_to_file(file_location, data):
    """Append content to a file.

    Notes:
        When appending addresses we got from addr messages the file should already exist with a proper header.

    Args:
        file_location (str): The path to the file we want to append
        data (str): Data we append
    """
    with open(file_location, 'a') as f:
        f.write(data)
