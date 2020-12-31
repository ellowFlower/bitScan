import hashlib
import struct
import time

from bitScan.exception import *
import csv
import logging

ONION_PREFIX = "\xFD\x87\xD8\x7E\xEB\x43"  # ipv6 prefix for .onion address
HEADER_LEN = 24
MIN_PROTOCOL_VERSION = 70001
SOCKET_BUFFER = 8192
MAGIC_NUMBER_COMPARE = b'\xf9\xbe\xb4\xd9'
ADDRESSES_GETADDR = '../input_output/getaddr.csv'
CONTENT_ADDR_SEND = '../input_output/send_addr.csv'
LOG_MAIN = '../logs/log_main.txt'
OUTPUT_ADDR = '../input_output/output_addr.csv'
OUTPUT_GETADDR = '../input_output/output_getaddr.csv'
OUTPUT_DURATION = '../input_output/output_duration.csv'


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
        raise MessageContentError(f"Error while unpacking bytes: {err}")


def write_to_file(file_location, data, first_line=''):
    """Write content to a file.

    Note:
        Deletes old file.

    Args:
        file_location (str): The path to the file we want to append
        data (str): Data we append
        first_line (str): A string as first line in the file. E.g. can be a header
    """
    logging.info('UTIL Append to file.')

    with open(file_location, 'w') as f:
        f.write(first_line+'\n')
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


def calculate_timeout(time_minutes):
    """Calculates the time when we have to shutdown the program

    Args:
        time_minutes (int): Time how long we want to measure in minutes.

    Returns:
        The calculated timeout in seconds.
    """
    return time.time() + 60 * time_minutes


def append_to_file(file_location, data):
    """Append content to a file.
    Notes:
        When appending addresses we got from addr messages the file should already exists.
    Args:
        file_location (str): The path to the file we want to append
        data (str): Data we append
    """
    logging.info('UTIL Append to file.')

    with open(file_location, 'a') as f:
        f.write(data)


def update_timestamps(arg):
    """Update the time in the first entry of an item of the list.

    Args:
        arg (list): [[<timestamp>,...],[timestamp,...],...]

    Returns:
        The updated list.
    """
    for x in arg:
        x[0] = str(time.time()).split('.')[0]

    return arg
