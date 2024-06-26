# TODO : Admit it proper test cases needs to be added

import os
import sys
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from stmp import STMPServer

# configure the logger
# only for testing
stp_logger = logging.getLogger("stmp")
handler = logging.StreamHandler(sys.stdout)
stp_logger.addHandler(handler)
stp_logger.setLevel(logging.DEBUG)

session = STMPServer()

if len(sys.argv) > 1:
    session.send_udp(
        " ".join(sys.argv[1:]),
    )
    session.send_tcp(" ".join(sys.argv[1:]), "127.0.0.0")
else:
    session.run()
