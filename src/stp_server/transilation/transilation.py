import os
import struct
import socket
import json
from typing import Union, Tuple
from .enc import Encryption
from ...settings import STP_PORT, logger

class TransilationProtocol:
    """The protocol struct
    
    As usual the request got two part 'header bytes' and 'payload'
    
    'size_bytes' -> represent size of remaing payload
    'header' -> of json strucutre (TBH, I like protobuf as well)
    'body' -> again of json structure for convenience

    size_bytes : "!HI"                          # not encypted
    header : {                                  # not encrypted
        "user": "<user name>",
        "hostname": <hostname>,
        "recvport": <recving port>,
        "encrypted": <boolean : if the body encrypted or not>,
        "public_key": <private-key>,            # optional
        "namespace": <target namespace>,
    }    
    body : <data provided by the application>   # can be encrypted
    """
    # going with network byte order (happens to be big-endiannes) & unsigned short & unsigned Int  
    # the integer is supposed to denote the size of following header and payload
    # -> apparently the max payload size is restricted to 4GB, and that of header is about 65KB 
    _size_bytes_format = "!HI"  

    encoding = 'utf-8'              # default encoding
    max_packet_size =  4 * 1000 * 1024    # limiting the packet max size to 4 MB 

    def __init__(self, 
            recvport:int=STP_PORT,
            user:str=os.getlogin(),
            hostname:str=socket.gethostname(),
        ) -> None:
        """Create a transilational instance
        Parameters
        ----------
        recvport    int
            self listening port (sending as part of an etiquette) 
        user        str
            user name of sender
        hostname    str
            host name of sender
        """
        self.encyption = Encryption()
        self.default_header = {
            "user": user,
            "hostname": hostname,
            "recvport": recvport,
            "encrypted": False,
        }

    @classmethod
    def size(cls)->int:
        """Return the size of size_bytes sequence"""
        return struct.calcsize(cls._size_bytes_format)

    def pack(self, data:Union[str, dict], namespace:str="/", enc_key:str="", pass_pub_key:bool=False) -> bytes:
        """Package given data payload
        
        Parameters
        ----------
        data:       str
            data to be packed (should be JSON serialisable)
        enc_key:    str
            if provided the body will be encrypted with the given public key
        pass_pub_key:   bool
            if True public_key will be sent with header (increase payload size)
        
        Returns
        -------
        bytes
            packed bytes data
        """
        header = { "namespace": namespace,  **self.default_header}
        if pass_pub_key:
            header["public_key"] = self.encyption.pub_key
        
        body = json.dumps(data, separators=(',', ':')).encode(self.encoding)
        if enc_key:
            body = self.encyption.encrypt(data, enc_key)
            header["encrypted"] = True
        header = json.dumps(header, separators=(',', ':')).encode(self.encoding)
        size_bytes = struct.pack(self._size_bytes_format, len(header), len(body))
    
        return size_bytes + header + body
    

    def decode_parts(self, data:bytes, decrypt:bool=False) :
        """Decode header or body part into python objects
        
        Parameters
        ----------
        data:   bytes
            data to be decoded into object
        decrypt:    bool
            weather or not to decrypt the data before parsing or not
            
        """
        try:
            if decrypt:
                data = self.encyption.decypt(data)
            data = json.loads(data.decode(self.encoding))
            return data
        except Exception as exp:
            logger.error(f"MSG decode error : {exp}")
            return None
        


    @classmethod
    def unpack_size_bytes(cls, size_bytes:bytes) -> Tuple[int]:
        """Unpack the size_bytes to decode the header and body size
        
        Parameters
        ----------
        size_bytes:     bytes
            bytes to be decoded with size_bytes_format
        
        Returns
        -------
        int, int
            size of header and size of body

        """
        try:
            return struct.unpack(cls._size_bytes_format, size_bytes)
        except:
            logger.warning(f"SIZE Bytes decode error! : junk data recieved!")
            return (None, None)