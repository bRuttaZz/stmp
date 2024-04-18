import time
import asyncio
import inspect
from typing import List, Dict
from .stp_server import STPServerBase
from .interfaces import PacketHeader, Packet, Peer
from .exceptions import InvalidImplementation, UsageError
from .settings import logger, PEER_DISCOVERY_INTERVEL, PEER_TTL, PEER_CLEANUP_INTERVEL


class STPServer(STPServerBase):
    """Advanced server interface for STPServerBase!"""

    _peers: Dict[str, Peer] = {}  # ip -> Peer
    _peer_list_update_callbacks = []

    # public attr
    PEER_DISCOVERY_INTERVEL = PEER_DISCOVERY_INTERVEL
    PEER_TTL = PEER_TTL
    PEER_CLEANUP_INTERVEL = PEER_CLEANUP_INTERVEL

    # propertis
    @property
    def peers(self) -> List[Peer]:
        """Get the list of peers list[dict[]]"""
        return self._peers.values()

    @property
    def username(self):
        """username used in the connection context!"""
        return self._t_protocol.default_header["user"]

    @username.setter
    def username(self, dat: str):
        self._t_protocol.default_header["user"] = dat

    @property
    def hostname(self):
        self._t_protocol.decode_parts["hostname"]

    def __init__(self, *args, **kwargs) -> None:
        """STPServer!

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
        super().__init__(*args, **kwargs)
        self.__bind_private_callbacks()

    # decorators
    def route(self, namespace: str):
        """Provide with a routing decorator, can be used for adding namespace
        the callback will be called with instance of `Packet` as the first argument

        Parameters
        ----------
        namespace:  str
            message routing namespace
        """

        def inner(func: callable):
            # validate function from the begining
            num_args = len(inspect.signature(func).parameters)
            if num_args != 1:
                InvalidImplementation(
                    "Route function for '{}' accepts excatly 1 arg. {} were given!".format(
                        namespace, num_args
                    )
                )

            def namespace_callback(
                body: dict, header: dict, sender_id: str, protocol: str
            ):
                packet = Packet(
                    data=body,
                    headers=PacketHeader(**header),
                    sender=sender_id,
                    protocol=protocol,
                )
                func(packet)

            self.add_callback(namespace=namespace, callback=namespace_callback)

            def modified(*args):
                raise UsageError(
                    "The Route function is not intented to be called outside!"
                )

            return modified

        return inner

    def on_peer_list_update(self, func: callable):
        """PeerJoin Event decorator, called whenever a new peer is joined
        the callback will be called with instance of `Peer` as the first argument (`new_peer`) and
        instance of `list[Peer]` as second arugument (`removed_peers`)
        """
        num_args = len(inspect.signature(func).parameters)
        if num_args != 2:
            InvalidImplementation(
                "peer_list_update event handler accepts exactly 2 arg. {} were given!".format(
                    num_args
                )
            )

        def callback(new_peer, removed_peers):
            func(new_peer, removed_peers)

        self._peer_list_update_callbacks.append(callback)

        def modified(*args):
            raise UsageError("The Event handler is not intented to be called outside!")

        return modified

    # private routes
    def __bind_private_callbacks(self):
        """Bind private routes and other callbacks"""

        # middlewares
        def peer_check(body: dict, header: dict, sender_id: str, protocol: str):
            # automated peer addition
            peer = Peer(update_time=time.time(), ip=sender_id, **header)
            if sender_id not in self._peers:
                logger.debug("new peer added : {}@{}".format(peer.user, sender_id))
                [
                    callback(new_peer=peer, removed_peers=[])
                    for callback in self._peer_list_update_callbacks
                ]
            self._peers[sender_id] = peer

        self.add_middleware(peer_check)

        # routes
        def peer_join(body: dict, header: dict, sender_id: str, protcol: str):
            if protcol.upper() == "UDP":
                # considering the peer request to be included
                self.send_tcp(
                    "iamheredude",
                    to_addr=sender_id,
                    to_port=header["tcpport"],
                    namespace="/peer-join",
                    enc_key=False,
                    pass_pub_key=True,
                )

        self.add_callback(namespace="/peer-join", callback=peer_join)

    # coroutines
    async def cleanup_peers(self):
        """Clean up old peer data"""
        while True:
            await asyncio.sleep(self.PEER_CLEANUP_INTERVEL)
            removed_peers = {}
            now = time.time()
            for key, peer in self._peers.items():
                if (now - peer.update_time) > self.PEER_TTL:
                    removed_peers[key] = peer
                    logger.debug(f"peer removed : {peer.user}@{peer.ip}")
            if removed_peers:
                for key in removed_peers.keys():
                    del self._peers[key]
                [
                    callback(new_peer=None, removed_peers=removed_peers.values())
                    for callback in self._peer_list_update_callbacks
                ]
            removed_peers = {}

    async def ping_for_address_update(self):
        """Request other peers to send their address"""
        await asyncio.sleep(5)  # give some time for the TCP recievers to readyup
        while True:
            self.request_sync()
            await asyncio.sleep(self.PEER_DISCOVERY_INTERVEL)

    # methods
    def request_sync(self):
        """Request other peers to send their address"""
        self.send_udp(
            "gimmeurnumberdude", "/peer-join", enc_key=False, pass_pub_key=True
        )

    def send_to_peer(
        self, namespace: str, data, peer_ip: str, encrypt: bool = True
    ) -> bool:
        """Send TCP message to discovered peer

        Parameters
        ----------
        namespace:  str
            Namespace to which send the data
        data:   Any
            JSON serialisable data to be send
        peer_ip:    str
            ip of peer
        encrypt:    bool
            whether to encyrpt the body or not

        """
        peer = self._peers.get(peer_ip)
        if not peer:
            return None

        return self.send_tcp(
            data,
            namespace=namespace,
            to_addr=peer_ip,
            to_port=peer.tcpport,
            enc_key=peer.public_key,
            pass_pub_key=True,
        )

    def broadcast(self, namespace: str, data, port: int = None):
        """Send a UDP multicast message to all the connected peers

        Parameters
        ----------
        namespace:  str
            namespace to which route the packets
        data:       Any
            data to be sent
        port:       int
            port to which send the data
        """
        return self.send_udp(data, namespace=namespace, to_port=port, pass_pub_key=True)

    # overrides
    async def listen(self):
        """Prepare server asyncio task."""
        return await asyncio.gather(
            self.listen_udp_async(),
            self.listen_tcp_async(),
            self.cleanup_peers(),
            self.ping_for_address_update(),
        )
