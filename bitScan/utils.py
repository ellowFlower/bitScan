import hashlib
import struct
from bitScan.exception import *
import csv
import logging

ONION_PREFIX = "\xFD\x87\xD8\x7E\xEB\x43"  # ipv6 prefix for .onion address
HEADER_LEN = 24
MIN_PROTOCOL_VERSION = 70001
SOCKET_BUFFER = 8192
MAGIC_NUMBER_COMPARE = b'\xf9\xbe\xb4\xd9'
ADDRESSES_GETADDR = '../input_output/getaddr.csv'
ADDR_RECEIVED = '../input_output/addr_received.csv'
GETADDR_RECEIVED = '../input_output/getaddr_received.csv'
CONTENT_ADDR_SEND = '../input_output/send_addr.csv'
LOG_MAIN = '../logs/log_main.txt'



def create_sub_version():
    """Binary encode the sub-version.

    Notes:
        Has length 16

    Returns:
        bytes: Binary encodes sub-version as bytes
    """
    logging.info('UTIL Create sub version.')

    sub_version = "/Satoshi:0.7.2/"
    return b'\x0F' + sub_version.encode()


def sha256_util(data):
    logging.info('UTIL Sha256.')

    return hashlib.sha256(data).digest()


def unpack_util(fmt, data):
    """Wraps problematic struct.unpack() in a try statement

    Args:
        fmt (str): The form which is used for unpacking
        data (bytes): The string which is unpacked.

    Returns:
        Unpacked data, which should be readable.
    """
    logging.info('UTIL Unpack bytes.')

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
    logging.info('UTIL Appoend to file.')

    with open(file_location, 'a') as f:
        f.write(data)


def read_file_csv(file_location):
    """Read csv file and return the content as list.

    Note: First row is the header, therefore we not append it to the returned list.

    Args:
        file_location (str): The path to the file we want to read

    Returns:
        content (list): The content we read from the file. The element in the list are lists also.
    """
    logging.info('UTIL Read csv file.')

    content = []
    with open(file_location, 'r') as data:
        csv_reader = csv.reader(data, delimiter=',')
        for idx, row in enumerate(csv_reader):
            if idx != 0 and row != []:
                content.append(row)

    return content
