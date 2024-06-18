import logging

# logger to be used
logger = logging.getLogger("stmp")

# some configs/consts
STMP_MADDR = "224.0.0.109"
STMP_PORT = 57000  # UDP port
TCP_PORT = 57001  # certainly TCP port

TCP_TIMEOUT = 5  # in seconds

# peer cleanup intervel (check for TTL)
PEER_CLEANUP_INTERVEL = 10  # in seconds

# if a new peer is added ( and unfortunately missed its update) time taken for its auto discovery
PEER_DISCOVERY_INTERVEL = 3 * 60  # in seconds

# time for a peer object to live in memory even if didn't appeared again
PEER_TTL = PEER_DISCOVERY_INTERVEL + 60  # in seconds
