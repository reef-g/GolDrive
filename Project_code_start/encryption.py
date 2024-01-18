import base64
import random
from Cryptodome.Cipher import AES
from Cryptodome import Random
import hashlib


class Encryption:
    def __init__(self, key):
        self.bs = AES.block_size
        self.key = hashlib.sha256(str(key).encode()).digest()

    def enc_msg(self, msg):
        msg = self._pad(msg)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(msg.encode()))

    def dec_msg(self, msg):
        enc = base64.b64decode(msg)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return Encryption._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]


def hash_msg(msg):
    return hashlib.sha3_256(msg.encode()).hexdigest()


def get_dh_factor():
    private_key = random.randint(1, p)

    return private_key, (g ** private_key) % p


def create_symmetry_key(private_key, shared_key):
    return Encryption((shared_key ** private_key) % p)


p = 7591
g = 1307


if __name__ == '__main__':
    privateA, a = get_dh_factor()
    privateB, b = get_dh_factor()

    cryptoA = create_symmetry_key(b, privateA)
    cryptoB = create_symmetry_key(a, privateB)
    msgToCrypt = "Geleo world"
    enc1 = cryptoA.enc_msg(msgToCrypt)

    print(msgToCrypt, cryptoB.dec_msg(enc1))
