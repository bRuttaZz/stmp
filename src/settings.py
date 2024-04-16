
import logging

# logger to be used
logger = logging.getLogger("stp")

# only for testing
import sys
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

# some configs/consts
STP_PORT = 57000
STP_MADDR = "239.192.1.107"
