# bitScan

This program communicates with the bitcoin network on network level. It consists of three sub-programs:
- Send getaddr message and receiving the corresponding addr message.
- Listening for addr messages for a specific amount of time.
- Send addr messages to other nodes in the network.

To start the scanner run the file `main.py` in `bitScan/bitScan`.