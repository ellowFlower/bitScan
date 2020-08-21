import logging
import csv
import socket

from bitScan.connection import Connection
from bitScan.exception import *


def main():
    """Create a connection and send getaddr message to the bitcoin nodes which address is read from a csv file.

    Note:
        The csv file must only contain the addresses delimited by ','. No newline character or space in between.
    """
    logging.basicConfig(level=logging.DEBUG)

    # read file
    addresses = []
    with open('../addresses_bitcoin_nodes.csv', 'r') as data:
        csv_reader = csv.reader(data, delimiter=',')
        for row in csv_reader:
            addresses.extend(row)

    for address in addresses:
        conn = Connection((address, 8333))
        try:
            conn.open()
            conn.handshake()
            # addr_msgs = conn.getaddr_addr()
            conn.recv_permanent(5)

        except (ConnectionError, RemoteHostClosedConnection, MessageContentError, socket.error) as err:
            logging.error("Error occured: {}".format(err))

        conn.close()


if __name__ == '__main__':
    main()
