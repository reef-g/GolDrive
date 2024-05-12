import base64
from Cryptodome.Cipher import AES
from Cryptodome import Random
import hashlib
import secrets
import chardet


class Encryption(object):
    def __init__(self, key):
        """
        :param key: the encryption key
        """
        self.bs = AES.block_size
        self.key = hashlib.sha256(str(key).encode()).digest()

    def enc_msg(self, message):
        """
        :param message: the message to encrypt
        :return: the encrypted message
        """
        if type(message) == str:
            message = message.encode()
        raw = self._pad(message)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def dec_msg(self, encrypt_message):
        """

        :param encrypt_message: the encrypted message to decrypt
        :return: the decrypted message
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
        :param message: message
        :return: the message with the padding
        """
        return message + (self.bs - len(message) % self.bs) * chr(self.bs - len(message) % self.bs).encode()

    @staticmethod
    def _unpad(message):
        """
        :param message: encrypted message
        :return: the encrypted message without the padding
        """
        return message[:-ord(message[len(message) - 1:])]


def hash_msg(msg):
    """
    :param msg: the msg to hash
    :return: the hash of the msg
    """
    return hashlib.sha3_256(msg.encode()).hexdigest()


def get_dh_factor():
    """
    :return: creates the dh factor
    """

    private_key = secrets.SystemRandom().randint(1, p)

    return private_key, (g ** private_key) % p


def create_symmetry_key(private_key, shared_key):
    """
    :param private_key: the personal key
    :param shared_key: the key i got from the server
    :return: returns the symmetrical encryption object from the dh key change
    """
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
