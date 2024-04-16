import socket

from .interfaces import ListenSession
from ...settings import logger, STP_MADDR, STP_PORT

class Transport:
    """Not that fancy! It's a transilational layer of the actual application layer :)"""

    def __init__(self, maddr:str=STP_MADDR, port:int=STP_PORT) -> None:
        """TransilationLayer! Feel Free to change the port and multicast address.
        
        Parameters
        ----------
        maddr:  str
            multicast address to be used
        port:   int
            port to be used 
        
        """
        self.addr = maddr
        self.port = port

        # socket
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 20) 

    def __enter__(self, *args, **kwargs):
        return self

    def __exit__(self, *args, **kwargs):
        # closing the port
        try:
            self._sock.close()
        except:
            ...
        
    def send(self, data:bytes, addr:str=None, port:int=None) -> None:
        """multicasts a UDP datagram.
        Parameters
        ----------
        data:   bytes
            data to be send over the socket

        addr:   str
            send message to custom address
        
        port:   int
            send message to custom port
        """
        self._sock.sendto(data, (
                    addr if addr else self.addr, 
                    port if port else self.port,
                )
        )

    def listen(self) -> "ListenSession":
        """Listen for a datagram and returns the data.
        Returns
        -------
        ListenSession
            listen session object
        """

        # Set some options to make it multicast-friendly
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
            logger.warning(f"It seems like the system is not supporting socket.SO_REUSEPORT option!"
                        +  " (never mind, it makes no sense, most of the time)")
        self._sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_LOOP, 1)

        # Bind to the port
        self._sock.bind(('', self.port))

        # Set some more multicast options
        intf = socket.gethostbyname(socket.gethostname())
        self._sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(intf))
        self._sock.setsockopt(socket.SOL_IP, 
                        socket.IP_ADD_MEMBERSHIP, 
                        socket.inet_aton(self.addr) + socket.inet_aton(intf)
        )

        return ListenSession(self._sock, self.addr)
