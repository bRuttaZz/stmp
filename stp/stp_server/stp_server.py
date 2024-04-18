import os
import asyncio
import socket
from uuid import uuid4
from .transport import UDPTransport, TCPTransport
from .transport.interfaces import ListenSession
from .transilation import TransilationProtocol
from ..settings import logger, STP_PORT, STP_MADDR, TCP_PORT


class STPServerBase:
    """The mighty STPServer backend"""

    # callbacks will be stored over here (namespaces-> list[callbacks])
    _callbacks = {}
    _middlewares = []  # custom middle wares to be called

    def __init__(
        self,
        user: str = os.getlogin(),
        hostname: str = socket.gethostname(),
        maddr: str = STP_MADDR,
        udpport: int = STP_PORT,
        tcpport: int = TCP_PORT,
    ) -> None:
        """STPServer backend.

        Parameters
        ----------
        user        str
            username of the user. The current system user will be considered
            otherwise
        hostname    str
            hostname of the system
        maddr       str
            multicasing address to be used. If not provided the defdault value will be used
        udpport        int
            oprtation port to be used
        tcpport
            tcp port used for full featured communication
        """
        self._t_protocol = TransilationProtocol(
            udp_port=udpport, tcp_port=tcpport, user=user, hostname=hostname
        )
        self._size_bytes_len = self._t_protocol.size()
        self._max_packet_size = self._t_protocol.max_packet_size

        self.udp_transport = UDPTransport(maddr=maddr, port=udpport)
        self.tcp_transport = TCPTransport(baddr="", port=tcpport)

        self._udp_session_id = str(uuid4())

    def __del__(self, *args, **kwargs):
        self.udp_transport.__exit__(*args, **kwargs)

    def add_callback(self, namespace: str, callback: callable):
        """Add an on message callback

        Parameters
        ----------
        callback    callable
            A callable that will be called with first prameter as STP body, second parameter as
            STP header, thrid paramter as UDP sender ip and fourth param as protocol being used.
        """
        if namespace not in self._callbacks:
            self._callbacks[namespace] = []
        self._callbacks[namespace].append(callback)

    def add_middleware(self, callback: callable):
        """Middle wares will be called for all requests came to the server

        Parameters
        ----------
        callback    callable
            A callable that will be called with first prameter as STP body, second parameter as
            STP header, thrid paramter as UDP sender ip and fourth param as protocol being used.
        """
        self._middlewares.append(callback)

    def send_udp(
        self,
        data,
        namespace: str = "/",
        enc_key: str = None,
        to_addr: str = None,
        to_port: int = None,
        pass_pub_key: bool = True,
    ):
        """Send UDP packet to peer(s)

        Parameters
        ----------
        data:    Any
            JSON serialisable data to be send via the wire
        namespace:  str
            namespace to which the data to be send
        enc_key:    str
            if an rsa public key is provided, the provided data will be encrypted using it
        to_addr:    str
            to address to be used (peer address)
        to_port:    int
            port to which the message to be send
        pass_pub_key:   bool
            Whether or not to use pass public key with the reeuest header
        """
        data = {"msg": data}
        data = self._t_protocol.pack(
            data,
            namespace=namespace,
            enc_key=enc_key,
            pass_pub_key=pass_pub_key,
            extra_headers={"udp_session": self._udp_session_id},
        )
        self.udp_transport.send(data, addr=to_addr, port=to_port)

    def send_tcp(
        self,
        data,
        to_addr: str,
        to_port: int = TCP_PORT,
        namespace: str = "/",
        enc_key: str = None,
        pass_pub_key: bool = True,
    ) -> bool:
        """Send TCP packet to peer(s)

        Parameters
        ----------
        data:    Any
            JSON serialisable data to be send via the wire
        to_addr:    str
            TCP to address to be used (peer address)
        to_port:    int
            TCP port to which the message to be send
        namespace:  str
            namespace to which the data to be send
        enc_key:    str
            if an rsa public key is provided, the provided data will be encrypted using it
        pass_pub_key:   bool
            Whether or not to use pass public key with the reeuest header
        """
        data = {"msg": data}
        data = self._t_protocol.pack(
            data, namespace=namespace, enc_key=enc_key, pass_pub_key=pass_pub_key
        )
        return self.tcp_transport.send(data, addr=to_addr, port=to_port)

    async def __listen_session_manaer(self, session: ListenSession):
        """Manage listen session!"""
        event_loop = asyncio.get_running_loop()
        logger.info(f"[{session.protocol}] listening for connection..")
        while True:
            data, (sender_id, *_) = await session.read(
                self._max_packet_size, loop=event_loop
            )
            header, body = {}, {}

            roi = data[: self._size_bytes_len]
            data = data[self._size_bytes_len :]
            header_s, body_s = self._t_protocol.unpack_size_bytes(roi)
            if (header_s + body_s + self._size_bytes_len) > self._max_packet_size:
                logger.warning(
                    "MSG Parsing: packet having illegal buffer length received!"
                )
                continue
            if header_s is None:
                continue  # error parsing (retry and self correct)

            header_raw = data[:header_s]
            body_raw = data[header_s:]
            header: dict = self._t_protocol.decode_parts(header_raw, False)
            if header is None:
                continue  # error parsing (retry and self correct)
            if header.get("udp_session") == self._udp_session_id:
                continue  # self message  ignoring

            if body_s:
                body = self._t_protocol.decode_parts(
                    body_raw, decrypt=header.get("encrypted")
                )
                if body is None:
                    continue  # error parsing (retry and self correct)
                body: dict = body.get("msg")

            logger.debug(
                f"[{session.protocol} Pack]: from '{sender_id}' @ {header.get('namespace')}"
            )

            # executing middlewares
            [
                callback(body, header, sender_id, session.protocol)
                for callback in self._middlewares
            ]

            # executing callbacks by namespace
            [
                callback(body, header, sender_id, session.protocol)
                for callback in self._callbacks.get(header.get("namespace"), [])
            ]

    async def listen_udp_async(self):
        """Listen for UDP packets"""
        session = None
        try:
            session = self.udp_transport.listen()
            await self.__listen_session_manaer(session=session)
        finally:
            print("UDP garbage collecting..")
            if session:
                session.close()

    async def listen_tcp_async(self):
        """Listen for tcp packets"""
        session = None
        try:
            session = self.tcp_transport.listen()
            await self.__listen_session_manaer(session=session)
        finally:
            print("TCP garbage collecting..")
            if session:
                session.close()

    async def listen(self):
        """Listen for UDP and TCP packets"""
        return await asyncio.gather(
            self.listen_udp_async(),
            self.listen_tcp_async(),
        )

    def run(self):
        """Start the STP server"""
        try:
            asyncio.run(self.listen())
        except KeyboardInterrupt:
            logger.error("STPServer Shutdown : KeyboardInterrupt")
