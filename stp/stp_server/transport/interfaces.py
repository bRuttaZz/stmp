import asyncio
import socket
from typing import Tuple, Literal
from ...settings import logger, TCP_TIMEOUT


class ListenSession:
    """A simple socket listen session"""

    protocol: Literal["UDP", "TCP"]
    socket: socket.socket

    async def read(
        self, buff_size: int = 1024, loop: asyncio.BaseEventLoop = None
    ) -> Tuple[bytes, tuple]:
        """read buffer_sized data from the system

        Parameters
        ----------
        buff_size:  int
            buffer size to be read from socket.
        loop:       asyncio.BaseEventLoop
            event loop to be used for waiting (optional)

        Returns
        -------
        future
            resolve with the gibrish read from the wire and sender infromation
        """

    def close(self):
        """To close the  ports"""
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
            try:
                self.socket.recv(400_000_000)
            except:
                ...
            self.socket.close()
            self.socket = None
        except Exception as exp:
            print("got error on socket shut", exp)


# transilation layer
class UDPListenSession(ListenSession):
    """A simple socket listen session"""

    protocol = "UDP"

    def __init__(self, socket: socket.socket, inet_addr: str) -> None:
        """

        Parameters
        ----------
        socket:     socket.socket
            udp socket session to be used
        inet_addr:  str
            inetaddress to be drop membership on session close

        """
        self.socket = socket
        self.inet_addr = inet_addr

    def __enter__(self, *args, **kwargs):
        return self

    def __exit__(self, *args, **kwargs):
        # unregister multicast receive membership
        self.close()

    def close(self):
        try:
            self.socket.setsockopt(
                socket.SOL_IP,
                socket.IP_DROP_MEMBERSHIP,
                socket.inet_aton(self.inet_addr) + socket.inet_aton("0.0.0.0"),
            )
            self.socket.close()
        except:
            ...

    async def read(
        self, buff_size: int = 1024, loop: asyncio.BaseEventLoop = None
    ) -> Tuple[bytes, tuple]:
        if not loop:
            loop = asyncio.get_running_loop()

        # older method using an executor
        # return await loop.run_in_executor(None, self.socket.recvfrom, buff_size)   # available from py3.5

        return await loop.sock_recvfrom(
            self.socket, buff_size
        )  # the feautre available from py3.11


class TCPListenSession(ListenSession):
    """A simple socket listen session"""

    protocol = "TCP"

    def __init__(self, socket: socket.socket) -> None:
        self.socket = socket

    def __enter__(self, *args, **kwargs):
        return self

    def __exit__(self, *args, **kwargs):
        self.close()

    async def read(
        self, buff_size: int = 1024, loop: asyncio.BaseEventLoop = None
    ) -> Tuple[bytes, tuple]:
        if not loop:
            loop = asyncio.get_running_loop()

        # yeah our protocol is too simple
        data, address = None, None

        client_socket, address = await loop.sock_accept(self.socket)
        try:
            client_socket.settimeout(TCP_TIMEOUT)
            # data = await loop.run_in_executor(None, client_socket.recv, buff_size)    # available from py3.7
            data = await loop.sock_recv(
                client_socket, buff_size
            )  # avialble from py3.11
        except TimeoutError:
            logger.warning(f"Client Takes too much time : {address} [is he a hacker!]")
        except OSError:
            logger.warning(f"Client disconnected in between!")
        finally:
            try:
                client_socket.shutdown(socket.SHUT_RDWR)
                try:
                    client_socket.recv(400_000_000)
                except:
                    ...
                client_socket.close()
                client_socket = None
            except:
                ...
        return data, address
