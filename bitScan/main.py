from bitScan.utils import *
from bitScan.connection import *
import logging
import time
import multiprocessing
import sys


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
            duration_of_connection (float): duration of connection
    """
    conn = Connection((address[0], int(address[1])))
    received_addr = ''
    received_getaddr = ''
    duration_of_connection = 0

    try:
        timeout = calculate_timeout(30)
        conn.open(timeout)
        conn.handshake(timeout)
        beginning_time = time.time()
        a, b = conn.communicate(timeout, content_addr_msg, lock, 1, -1)
        end_time = time.time()

        duration_of_connection = end_time - beginning_time

        received_addr += a
        received_getaddr += b
    # these errors only occur when no connection was made in the first place
    except (ConnectionError, socket.error) as err:
        logging.error("Error occurred in connection with bitcoin node {},{}: {}".format(address[0], address[1], err))

    conn.close()

    # # write output to files
    # log_header = 'connectedToHost,connectedToPort,host,port,timestamp,currentTime'
    # # received addresses from voluntarily addr messages
    # write_to_file('../input_output/addr_received_' + address[0] + '.csv', received_addr, log_header)
    # # received addresses as response to getaddr
    # write_to_file('../input_output/getaddr_received_' + address[0] + '.csv', received_getaddr, log_header)

    return address[0], duration_of_connection


def handle_cmd_args(count_args, file1, file2, time, send_addr=-1, send_getaddr=-1):
    """Handles the command line arguments

    Args:
        count_args (int): Number of arguments.
        file1 (str): File with addresses of nodes we want to connect.
        file2 (str): File with addresses of nodes we want to send a addr message.
        time (int): How long we want to measure in minutes.
        send_addr (int): Number how often we want to send an addr message. E.g. 2 => every two minutes.
        send_getaddr (int): Number how often we want to send an getaddr message. E.g. 2 => every two minutes.
    """
    # if len(count_args):
    pass


def write_durations_of_connections_to_file(durations_of_connections):
    """
    Args:
        durations_of_connections (list): List of the node address and the duration of the connection
    """
    write_to_file(OUTPUT_DURATION, '', 'Node,Duration in seconds')

    data = ''
    for node_info in durations_of_connections:
        data += f'{node_info[0]},{node_info[1]}\n'

    append_to_file(OUTPUT_DURATION, data)


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, filename=LOG_MAIN)
    lock = multiprocessing.Lock()

    # create output files
    log_header = 'connectedToHost,connectedToPort,host,port,timestamp,currentTime'
    write_to_file(OUTPUT_ADDR, '', log_header)
    write_to_file(OUTPUT_GETADDR, '', log_header)

    thread_arguments = read_file_csv(ADDRESSES_GETADDR)
    content_addr_msg = read_file_csv(CONTENT_ADDR_SEND)

    # number of threads = number of available CPUs in the system
    p = multiprocessing.Pool()
    durations_of_connections = p.map(main, thread_arguments)
    p.close()

    write_durations_of_connections_to_file(durations_of_connections)

