from typing import Literal


class BasePropertyClass:
    """Base property calss"""

    def __init__(self, strict_parse: bool = False, **kwargs) -> None:
        for key, val in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, val)
            elif key in self.__annotations__:
                setattr(self, key, val)
            else:
                if strict_parse:
                    raise ValueError(f"{self.__class__} doesn't have propery : {key}")


class PacketHeader(BasePropertyClass):
    user: str
    hostname: str
    udpport: int
    tcpport: int
    encrypted: bool = False
    public_key: str = None
    namespace: str = None


class Packet(BasePropertyClass):
    """Interface of message packets"""

    data = None
    headers: PacketHeader
    sender: str
    protocol: Literal["UDP", "TCP"]


class Peer(BasePropertyClass):
    """Interface of Peer object"""

    user: str
    hostname: str
    ip: str
    udpport: int
    tcpport: int
    public_key: str  # public encyption key
    update_time: float
