import logging

from bitScan.connection import Connection
from bitScan.exception import ConnectionError

def main():
    """Create connection to a bitcoin node and send getaddr message."""

    logging.basicConfig(level=logging.DEBUG)

    conn = Connection(('88.99.167.175', 8333))
    # conn = Connection(('127.0.0.1', 18444))
    try:
        conn.open()
        conn.handshake()
        conn.getaddr_addr()

    except (ConnectionError) as err:
        logging.error("Error occured: {}".format(err))

    conn.close()


if __name__ == '__main__':
    main()
