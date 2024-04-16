import os
import socket
import json
from .transport import Transport 
from .transilation import TransilationProtocol
from ..settings import logger, STP_PORT, STP_MADDR

class STPServerBase:
    """The mighty STPServer backend"""

    _callbacks = []

    def __init__(self, user:str=os.getlogin(),
                hostname:str=socket.gethostname(), 
                maddr:str=STP_MADDR, port:int=STP_PORT) -> None:
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
        port        int
            oprtation port to be used
        """
        self._transport = Transport(maddr=maddr, port=port)
        self._t_protocol = TransilationProtocol(recvport=maddr, user=user, hostname=hostname) 
        self._size_bytes_len = self._t_protocol.size()
        self._max_packet_size = self._t_protocol.max_packet_size

    def __del__(self, *args, **kwargs):
        self._transport.__exit__(*args, **kwargs)

    def add_callback(self, callback:callable):
        """Add an on message callback
        
        Parameters
        ----------
        callback    callable
            A callable that will be called with first prameter as STP body second parameter as
            STP header and thrid paramter as UDP sender ip.
        """
        self._callbacks.append(callback)

    def send(self, data, namespace:str="/", enc_key:str=None, to_addr:str=None, 
            to_port:int=None, pass_pub_key:bool=False):
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
        data = self._t_protocol.pack(data, namespace=namespace, enc_key=enc_key,
            pass_pub_key=pass_pub_key)
        self._transport.send(data, addr=to_addr, port=to_port)

    def listen(self):
        """Listen for messages. Blocking!"""
        with self._transport.listen() as session:
            while True:
                data, (sender_id, *_) = session.read(self._max_packet_size)
                header, body = {}, {}

                roi = data[:self._size_bytes_len]
                data = data[self._size_bytes_len:]
                header_s, body_s = self._t_protocol.unpack_size_bytes(roi)
                if (header_s + body_s + self._size_bytes_len) > self._max_packet_size:
                    logger.warning(f"MSG Parsing: packet having illegal buffer length received!")
                    continue
                if header_s is None:
                    continue            # error parsing (retry and self correct)

                header_raw = data[:header_s]
                body_raw = data[header_s:]
                header = self._t_protocol.decode_parts(header_raw, False)
                if header is None:
                    continue            # error parsing (retry and self correct)

                if body_s:
                    body = self._t_protocol.decode_parts(
                        body_raw, decrypt=header.get("encrypted"))
                    if body is None:
                        continue            # error parsing (retry and self correct)
                    body = body.get("msg")

                logger.debug(f"[UDP Pack]: from '{sender_id}' @ {header.get('namespace')}")
                # executing callbacks
                [callback(body, header, sender_id) for callback in self._callbacks]
                
