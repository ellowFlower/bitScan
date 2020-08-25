from bitScan.utils import *
from bitScan.connection import *
import logging
import multiprocessing

"""Receive addr messages from open connections.

Note:
    The csv file must only contain the addresses delimited by ','. No newline character or space in between.
"""
logging.basicConfig(level=logging.DEBUG)


def start(address):
    conn = Connection((address[0], int(address[1])))
    received_addr = ''
    try:
        conn.open()
        conn.handshake()
        received_addr += conn.recv_permanent(15)

    except (ConnectionError, RemoteHostClosedConnection, MessageContentError, socket.error) as err:
        logging.error("Error occured: {}".format(err))

    conn.close()
    return received_addr


addresses = read_file_csv(ADDRESSES_GETADDR)
p = multiprocessing.Pool()
data = p.map(start, addresses)
p.close()
append_to_file(ADDR_RECEIVED, ''.join(data))


# for address in addresses:
#     conn = Connection((address[0], int(address[1])))
#     try:
#         conn.open()
#         conn.handshake()
#         received_addr = conn.recv_permanent(25)
#         append_to_file(ADDR_RECEIVED, received_addr)
#
#     except (ConnectionError, RemoteHostClosedConnection, MessageContentError, socket.error) as err:
#         logging.error("Error occured: {}".format(err))
#
#     conn.close()
