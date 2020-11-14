from bitScan.utils import *
from bitScan.connection import *
import logging
import time
import multiprocessing


def main(address):
    """Starting point.
    Note:
        To use the parameter address as a list this function has to be called with multiprocessing (map).
    Args:
        address (list): host,port
    Returns:
        (tuple): tuple containing:
            received_addr (str): The received addresses from voluntary addr messages.
            received_getaddr (str): The received addresses from responses to getaddr messages.
    """
    conn = Connection((address[0], int(address[1])))
    received_addr = ''
    received_getaddr = ''

    try:
        timeout = calculate_timeout(5)
        conn.open()
        conn.handshake(timeout)
        a, b = conn.communicate(timeout, content_addr_msg, 1, 1)
        received_addr += a
        received_getaddr += b
    except (ConnectionError, RemoteHostClosedConnection, socket.error) as err:
        logging.error("Error occurred in connection with bitcoin node {},{}: {}".format(address[0], address[1], err))

    conn.close()

    # # write output to files
    # log_header = 'connectedToHost,connectedToPort,host,port,timestamp,currentTime'
    # # received addresses from voluntarily addr messages
    # write_to_file('../input_output/addr_received_' + address[0] + '.csv', received_addr, log_header)
    # # received addresses as response to getaddr
    # write_to_file('../input_output/getaddr_received_' + address[0] + '.csv', received_getaddr, log_header)

    return received_addr, received_getaddr


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, filename=LOG_MAIN)
    append_addr = ''
    append_getaddr = ''
    addresses = read_file_csv(ADDRESSES_GETADDR)
    content_addr_msg = read_file_csv(CONTENT_ADDR_SEND)
    # number of threads = number of CPUs in the system
    p = multiprocessing.Pool()
    data = p.map(main, addresses)
    p.close()

    for x in data:
        append_addr += x[0]
        append_getaddr += x[1]

    log_header = 'connectedToHost,connectedToPort,host,port,timestamp,currentTime'
    write_to_file('../input_output/addr_received.csv', append_addr, log_header)
    write_to_file('../input_output/getaddr_received.csv', append_getaddr, log_header)

