import base64
from Cryptodome.Cipher import AES
from Cryptodome import Random
import hashlib
import random
import chardet


class Encryption(object):
    def __init__(self, key):
        """
        :param key: w
        """
        self.bs = AES.block_size
        self.key = hashlib.sha256(str(key).encode()).digest()

    def enc_msg(self, message):
        """

        :param message:
        :return:
        """
        if type(message) == str:
            message = message.encode()
        raw = self._pad(message)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def dec_msg(self, encrypt_message):
        """

        :param encrypt_message:
        :return:
        """
        enc = base64.b64decode(encrypt_message)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC,iv)
        a = self._unpad(cipher.decrypt(enc[AES.block_size:]))
        encoding = chardet.detect(a)
        if encoding['encoding'] == "ascii":
            a = a.decode()
        return a

    def _pad(self, message):
        """

        :param message:
        :return:
        """
        return message + (self.bs - len(message) % self.bs) * chr(self.bs - len(message) % self.bs).encode()

    @staticmethod
    def _unpad(message):
        """

        :param message:
        :return:
        """
        return message[:-ord(message[len(message) - 1:])]


def hash_msg(msg):
    return hashlib.sha3_256(msg.encode()).hexdigest()


def get_dh_factor():
    private_key = random.randint(1, p)

    return private_key, (g ** private_key) % p


def create_symmetry_key(private_key, shared_key):
    return Encryption((shared_key ** private_key) % p)


p = 7723
g = 1229


if __name__ == '__main__':
    a, A = get_dh_factor()
    print(len(str(A)))
    b, B = get_dh_factor()

    keyServer = create_symmetry_key(a, B)
    keyClient = create_symmetry_key(b, A)
    print(keyClient.key)
    print(keyServer.key)

    with open(r"T:\public\יב\imri\projectCode\files\cat.jpg", 'rb') as f:
        data = f.read()

    print(len(data))

    encM = keyServer.enc_msg(data)
    print(len(encM), type(encM))

    decM = keyClient.dec_msg(encM)
    print(decM)
