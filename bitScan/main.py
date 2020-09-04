from bitScan.utils import *
from bitScan.connection import *
import logging
import time
import multiprocessing


def main(address):
    """Starting point.
    Note:
        To use the parameter address as a list this function has to be called with multiprocessing (map).
    Args:
        address (list): host,port
    Returns:
        (tuple): tuple containing:
            received_addr (str): The received addresses from voluntary addr messages.
            received_getaddr (str): The received addresses from responses to getaddr messages.
    """
    conn = Connection((address[0], int(address[1])))
    received_addr = ''
    received_getaddr = ''

    try:
        conn.open()
        conn.handshake()
        a, b = conn.communicate(5, content_addr_msg, 3, 3)
        received_addr += a
        received_getaddr += b
    except (ConnectionError, RemoteHostClosedConnection, HandshakeContentError, socket.error) as err:
        logging.error("Error occurred in connection with bitcoin node {},{}: {}".format(address[0], address[1], err))
        return received_addr + '\n', received_getaddr

    conn.close()
    return received_addr, received_getaddr


if __name__ == "__main__":
    logging.basicConfig(filename=LOG_MAIN, level=logging.ERROR)
    append_addr = ''
    append_getaddr = ''
    addresses = read_file_csv(ADDRESSES_GETADDR)
    content_addr_msg = read_file_csv(CONTENT_ADDR_SEND)
    p = multiprocessing.Pool()
    data = p.map(main, addresses)
    p.close()

    for x in data:
        append_addr += x[0]
        append_getaddr += x[1]

    append_to_file(ADDR_RECEIVED, append_addr)
    append_to_file(GETADDR_RECEIVED, append_getaddr)