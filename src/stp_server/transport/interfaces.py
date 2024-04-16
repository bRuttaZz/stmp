import socket
from typing import Tuple

# transilation layer
class ListenSession:
    """A simple socket listen session"""

    def __init__(self, socket: socket.socket, inet_addr:str) -> None:
        self.socket = socket
        self.inet_addr = inet_addr

    def __enter__(self, *args, **kwargs):
        return self
    
    def __exit__(self, *args, **kwargs):
        # unregister multicast receive membership
        self.socket.setsockopt(
            socket.SOL_IP, 
            socket.IP_DROP_MEMBERSHIP, 
            socket.inet_aton(self.inet_addr) + socket.inet_aton('0.0.0.0')
        )
    
    def read(self, buff_size:int=1024) -> Tuple[bytes, tuple]:
        """read buffer_sized data from the system
        
        Parameters
        ----------
        buff_size:  int
            buffer size to be read from socket.

        Returns
        -------
        bytes
            that gibrish read from the wire
        """
        return self.socket.recvfrom(buff_size)
