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
            duration_of_connection (float): duration of connection
    """
    conn = Connection((address[0], int(address[1])))
    received_addr = ''
    received_getaddr = ''
    duration_of_connection = 0

    try:
        # TODO you can set time frame PER NODE here (in minutes)
        timeout = calculate_timeout(3)
        conn.open(timeout)
        conn.handshake(timeout)
        beginning_time = time.time()
        # TODO you can set interval for sending addr/getaddr messages here
        a, b = conn.communicate(timeout, content_addr_msg, lock, -1, -1)
        end_time = time.time()

        duration_of_connection = end_time - beginning_time

        received_addr += a
        received_getaddr += b
    # these errors only occur when no connection was made in the first place
    except (ConnectionError, socket.error) as err:
        logging.error("Error occurred in connection with bitcoin node {},{}: {}".format(address[0], address[1], err))

    conn.close()

    return address[0], duration_of_connection


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

