from bitScan.utils import *
from bitScan.connection import *
import logging

"""Receive addr messages from open connections.

Note:
    The csv file must only contain the addresses delimited by ','. No newline character or space in between.
"""

logging.basicConfig(level=logging.DEBUG)

addresses = read_file_csv(ADDRESSES_GETADDR)

for address in addresses:
    conn = Connection((address[0], int(address[1])))
    try:
        conn.open()
        conn.handshake()
        received_addr = conn.recv_permanent(25)
        append_to_file(ADDR_RECEIVED, received_addr)

    except (ConnectionError, RemoteHostClosedConnection, MessageContentError, socket.error) as err:
        logging.error("Error occured: {}".format(err))

    conn.close()
