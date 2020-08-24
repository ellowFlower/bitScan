from bitScan.utils import *
from bitScan.connection import *
import logging
import time

"""Send getaddr messages to open connections and then receive a addr message.

Note:
    The csv file must only contain the addresses delimited by ','. No newline character or space in between.
"""

logging.basicConfig(level=logging.DEBUG)

addresses = read_file_csv(ADDRESSES_GETADDR)

count = 5

for address in addresses:
    conn = Connection((address[0], int(address[1])))

    while count > 0:
        try:
            conn.open()
            conn.handshake()
            received_addr = conn.getaddr_addr()

            append_to_file(GETADDR_RECEIVED, received_addr)

        except (ConnectionError, RemoteHostClosedConnection, MessageContentError, socket.error) as err:
            logging.error("Error occured: {}".format(err))

        time.sleep(240)
        count -= 1

    conn.close()
