import multiprocessing

from bitScan.utils import *
from bitScan.connection import *
import logging
import time

"""Send getaddr messages to open connections and then receive a addr message.

Note:
    The csv file must only contain the addresses delimited by ','. No newline character or space in between.
"""
logging.basicConfig(level=logging.DEBUG)


def start(address):
    count = 3
    conn = Connection((address[0], int(address[1])))
    received_data = ''

    while count > 0:
        try:
            conn.open()
            conn.handshake()
            received_data += conn.getaddr_addr()

        except (ConnectionError, RemoteHostClosedConnection, MessageContentError, socket.error) as err:
            logging.error("Error occured: {}".format(err))

        time.sleep(240)
        count -= 1

    conn.close()
    return received_data


addresses = read_file_csv(ADDRESSES_GETADDR)
p = multiprocessing.Pool()
data = p.map(start, addresses)
p.close()
append_to_file(GETADDR_RECEIVED, ''.join(data))


# count = 5
#
# for address in addresses:
#     conn = Connection((address[0], int(address[1])))
#
#     while count > 0:
#         try:
#             conn.open()
#             conn.handshake()
#             received_addr = conn.getaddr_addr()
#
#             append_to_file(GETADDR_RECEIVED, received_addr)
#
#         except (ConnectionError, RemoteHostClosedConnection, MessageContentError, socket.error) as err:
#             logging.error("Error occured: {}".format(err))
#
#         time.sleep(240)
#         count -= 1
#
#     conn.close()
