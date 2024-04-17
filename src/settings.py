import logging

# logger to be used
logger = logging.getLogger("stp")

# some configs/consts
STP_MADDR = "239.192.1.107"
STP_PORT = 57000    # UDP port
TCP_PORT = 57001    # certainly TCP port

TCP_TIMEOUT = 5     # in seconds

# peer cleanup intervel (check for TTL)
PEER_CLEANUP_INTERVEL = 10       # in seconds

# if a new peer is added ( and unfortunately missed its update) time taken for its auto discovery
PEER_DISCOVERY_INTERVEL = 3 * 60    # in seconds

# time for a peer object to live in memory even if didn't appeared again
PEER_TTL = PEER_DISCOVERY_INTERVEL + 60   # in seconds
