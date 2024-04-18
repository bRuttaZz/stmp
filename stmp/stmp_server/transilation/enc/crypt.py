from typing import Union
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP


class Encryption:
    """For the sake of simplicity we are going with RSA :)"""

    _encoding = "utf-8"
    _key_size = 1024  # min 1024, should be multiple of 256

    pub_key = None
    _cipher = None

    def __init__(self):
        """Create new encryption key pairs"""
        self.key = RSA.generate(1024)
        self.pub_key = self.key.exportKey("DER").hex()
        self._cipher = PKCS1_OAEP.new(key=self.key)

    @classmethod
    def encrypt(cls, msg: Union[str, bytes], pub_key: str) -> bytes:
        """Encrypt a message using an identical public key

        Parameters
        ----------
        msg:    str | bytes
            message to be encypted
        pub_key: str
            DIR formatted rsa public key

        Returns
        -------
        bytes
            encypted bytes
        """
        if isinstance(msg, str):
            msg = msg.encode(cls._encoding)
        key = RSA.importKey(bytes.fromhex(pub_key))
        cipher = PKCS1_OAEP.new(key=key)
        return cipher.encrypt(msg)

    def decypt(self, ciphertext: Union[str, bytes]) -> bytes:
        """Decypt using the creted secret key

        Parameters
        ----------
        ciphertext: str | bytes
            The data encypted using public key of 'self'

        Returns
        -------
        bytes
            Decrypted bytes
        """
        if isinstance(ciphertext, str):
            ciphertext = ciphertext.encode(self._encoding)
        return self._cipher.decrypt(ciphertext)
