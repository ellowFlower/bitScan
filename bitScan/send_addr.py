import multiprocessing

from bitScan.utils import *
from bitScan.connection import *
import logging
import time

"""Send addr messages to open connections.

Note:
    The csv file must only contain the addresses delimited by ','. No newline character or space in between.
"""
logging.basicConfig(filename=LOG_SEND_ADDR, level=logging.ERROR)


def start(address):
    count = 3
    conn = Connection((address[0], int(address[1])))
    while count > 0:
        try:
            conn.open()
            conn.handshake()
            conn.send_addr(content_addr_msg)

            time.sleep(240)
            count -= 1
        except (ConnectionError, RemoteHostClosedConnection, MessageContentError, socket.error) as err:
            logging.error("Error occured in connection with bitcoin node {},{}: {}".format(address[0], address[1], err))

    conn.close()


addresses = read_file_csv(ADDRESSES_GETADDR)
content_addr_msg = read_file_csv(ADDR_SEND)
p = multiprocessing.Pool()
p.map(start, addresses)
p.close()

