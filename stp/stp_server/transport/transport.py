import socket

from .interfaces import ListenSession, UDPListenSession, TCPListenSession
from ...settings import logger, STP_MADDR, STP_PORT, TCP_PORT, TCP_TIMEOUT


class Transport:
    """Base class of a Transport session
    It's that transilational layer of the actual application layer :)"""

    _sock = None  # socket session

    def _prepare_sock(self):
        """Common socket settings"""
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
            logger.warning(
                "It seems like the system is not supporting socket.SO_REUSEPORT option!"
                + " (never mind, it makes no sense, most of the time)"
            )
        self._sock.setblocking(False)

    def __del__(self):
        try:
            self._sock.close()
        except:
            ...

    def send(self, data: bytes, addr: str = None, port: int = None) -> None:
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

    def listen(self) -> "ListenSession":
        """Listen for a datagram and returns the data.
        Returns
        -------
        ListenSession
            listen session object
        """


class UDPTransport(Transport):
    """A simple UDP transport."""

    def __init__(self, maddr: str = STP_MADDR, port: int = STP_PORT) -> None:
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

    def send(self, data: bytes, addr: str = None, port: int = None) -> bool:
        if not addr:
            addr = self.addr
        if not port:
            port = self.port
        self._sock.sendto(data, (addr, port))
        logger.debug(f"Multicasted message : {addr}:{port}")
        return True

    def listen(self) -> "ListenSession":
        self._prepare_sock()
        # Set some options to make it multicast-friendly
        self._sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_LOOP, 1)

        # Bind to the port
        self._sock.bind(("", self.port))

        # Set some more multicast options
        intf = socket.gethostbyname(socket.gethostname())
        self._sock.setsockopt(
            socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(intf)
        )
        self._sock.setsockopt(
            socket.SOL_IP,
            socket.IP_ADD_MEMBERSHIP,
            socket.inet_aton(self.addr) + socket.inet_aton(intf),
        )

        return UDPListenSession(self._sock, self.addr)


class TCPTransport(Transport):
    """A simple TCP transport. Now we got the read reciepts"""

    def __init__(self, baddr: str = "", port: int = TCP_PORT) -> None:
        """TransilationLayer! Feel Free to change the port and multicast address.

        Parameters
        ----------
        baddr:  str
            bind address to be used
        port:   int
            port to be used

        """
        self.addr = baddr
        self.port = port

        # socket
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __enter__(self, *args, **kwargs):
        return self

    def __exit__(self, *args, **kwargs):
        # closing the port
        try:
            self._sock.close()
        except:
            ...

    def send(self, data: bytes, addr: str, port: int = TCP_PORT) -> bool:
        """Send a message using TCP, will return with True if all went ok, otherwise False"""
        try:
            self._sock.connect((addr, port))
            self._sock.sendall(data)

            # confirm reciept
            self._sock.settimeout(TCP_TIMEOUT)
            self._sock.recv(1024)
            logger.debug(f"Sent message to server: {addr}:{port}")
            return True
        except TimeoutError:
            logger.warning(
                f"peer takes too much time to respond: {addr}:{port} (is he a hacker!)"
            )
            return False
        except ConnectionError:
            logger.warning(f"peer is unawailable: {addr}:{port} ")
            return False
        except Exception as exp:
            logger.warning(f"connection reset by peer : {exp}")
            return False
        finally:
            try:
                self._sock.close()
            except:
                ...

    def listen(self) -> "ListenSession":
        """Create a TCP listenerSession"""
        self._prepare_sock()
        self._sock.bind((self.addr, self.port))
        self._sock.listen(5)  # TODO: adjust the backlog

        return TCPListenSession(self._sock)
