from bitScan.utils import *
from bitScan.connection import *
import logging
import multiprocessing

"""Receive addr messages from open connections.

Note:
    The csv file must only contain the addresses delimited by ','. No newline character or space in between.
"""
logging.basicConfig(filename=LOG_RECEIVE_ADDR, level=logging.ERROR)


def start(address):
    conn = Connection((address[0], int(address[1])))
    received_addr = ''
    try:
        conn.open()
        conn.handshake()
        received_addr += conn.recv_permanent(15)

    except (ConnectionError, RemoteHostClosedConnection, MessageContentError, socket.error) as err:
        logging.error("Error occured in connection with bitcoin node {},{}: {}".format(address[0], address[1], err))
        return ''

    conn.close()
    return received_addr


addresses = read_file_csv(ADDRESSES_GETADDR)
p = multiprocessing.Pool()
data = p.map(start, addresses)
p.close()
append_to_file(ADDR_RECEIVED, ''.join(data))

