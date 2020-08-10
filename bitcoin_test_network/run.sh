
# Change this variables. All paths must be absolute
# Path to bitcoin_test_network/bitcoin.conf
CONF_MAIN=""
# Path to bitcoin_test_network/data
DATA_MAIN=""
# Path to bitcoin_test_network/alice/bitcoin.conf
CONF_ALICE=""
# Path to bitcoin_test_network/alice/data
DATA_ALICE=""
# Path to bitcoin_test_network/bob/bitcoin.conf
CONF_BOB=""
# Path to bitcoin_test_network/alice/data
DATA_BOB=""

# Start the main node. Per default listen for connection on port 18445.
bitcoind -conf=$CONF_MAIN -datadir=$DATA_MAIN -daemon

# node alice
bitcoind -port=18445 -rpcport=8333 -conf=$CONF_ALICE -datadir=$DATA_ALICE -daemon

# node bob
bitcoind -port=18446 -rpcport=8334 -conf=$CONF_BOB -datadir=$DATA_BOB -daemon

# connect alice and bob to the main node
bitcoin-cli addnode "127.0.0.1:18445" add
bitcoin-cli addnode "127.0.0.1:18446" add