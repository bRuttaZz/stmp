import sys
from src import STPServerBase

session = STPServerBase()

if len(sys.argv) > 1:
    session.send(" ".join(sys.argv[1:]))
else:
    session.listen()