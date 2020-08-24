import logging
import csv
import socket

from bitScan.connection import Connection
from bitScan.exception import *


def main():
    """Use only for testing purpose."""
    logging.basicConfig(level=logging.DEBUG)

    # read file
    addresses = []
    with open('../getaddr.csv', 'r') as data:
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
