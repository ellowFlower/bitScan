import multiprocessing

from bitScan.utils import *
from bitScan.connection import *
import logging
import time

"""Send getaddr messages to open connections and then receive a addr message.

Note:
    The csv file must only contain the addresses delimited by ','. No newline character or space in between.
"""
logging.basicConfig(filename=LOG_SEND_GETADDR, level=logging.ERROR)


def start(address):
    count = 3
    conn = Connection((address[0], int(address[1])))
    received_data = ''

    while count > 0:
        try:
            conn.open()
            conn.handshake()
            received_data += conn.getaddr_addr()

            time.sleep(240)
            count -= 1
        except (ConnectionError, RemoteHostClosedConnection, MessageContentError, socket.error) as err:
            logging.error("Error occured in connection with bitcoin node {},{}: {}".format(address[0], address[1], err))
            return ''

    conn.close()
    return received_data


addresses = read_file_csv(ADDRESSES_GETADDR)
p = multiprocessing.Pool()
data = p.map(start, addresses)
p.close()
append_to_file(GETADDR_RECEIVED, ''.join(data))
