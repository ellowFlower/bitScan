#!/bin/bash

export PYTHONPATH="${PYTHONPATH}:/home/martin/PycharmProjects/bitScan/bitScan"

python3 ./bitScan/send_getaddr.py &
python3 ./bitScan/receive_addr.py &
python3 ./bitScan/send_addr.py