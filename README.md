# bitScan

This program communicates with the bitcoin network. It performs three tasks:
- Sending getaddr messages.
- Listening for addr messages.
- Sending addr messages.

To start the scanner run the file `main.py` in `bitScan/bitScan`.

A list of the node's addresses, where a connection should be initiated, has to be written into `bitScan/bitScan/input_output/getaddr.csv`. First line is the header. Starting with the second line the addresses have to be in the format `<host>,<port>`, e.g. `34.121.191.59,8333`.

A list of the node's addresses, which should be sent to our peers, has to be written into `bitScan/bitScan/input_output/send_addr.csv`. First line is the header. Starting with the second line the addresses have to be in the format `timestamp,service,host,port`, e.g. `1606475361,0,2001:db8::8a2e:370:7334,8333`.

Three output files will be generated:
- `bitScan/bitScan/input_output/output_addr.csv`: Contains voluntarily sent addresses. `host` and `port` are the received address.
- `bitScan/bitScan/input_output/output_getaddr.csv`: Contains sent addresses as response to a getaddr message. `host` and `port` are the received address.
- `bitScan/bitScan/input_output/output_duration.csv`: Contains the duration of the connection per node.