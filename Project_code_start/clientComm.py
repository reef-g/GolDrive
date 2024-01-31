import socket
import threading
import sys
import queue
import encryption
import Settings
import clientProtocol


class ClientComm:
    def __init__(self, server_ip, port, recv_q, msg_len_bytes):
        self.server_ip = server_ip
        self.port = port
        self.recvQ = recv_q
        self.socket = socket.socket()
        self.msgLenBytes = msg_len_bytes
        self.enc_obj = None

        threading.Thread(target=self._main_loop).start()

    def _main_loop(self):
        try:
            self.socket.connect((self.server_ip, self.port))
        except Exception as e:
            sys.exit("Server is closed try again later")

        self.enc_obj = self._change_key()

        while True:
            try:
                leng = self.socket.recv(self.msgLenBytes).decode()
                data = self.socket.recv(int(leng))
            except Exception as e:
                sys.exit("Server is closed try again later")

            decrypted_data = self.enc_obj.dec_msg(data)

            if self.port == Settings.SERVERPORT:
                self.recvQ.put(decrypted_data)
            else:
                file_name, file_len = clientProtocol.unpack_message(decrypted_data)
                self._recv_file(file_name, file_len)

    def _change_key(self):
        privateA, a = encryption.get_dh_factor()
        try:
            b = int(self.socket.recv(10).decode())
            self.socket.send((str(a).zfill(10)).encode())

        except Exception as e:
            print("in change key ", str(e))

        else:
            crypto = encryption.create_symmetry_key(privateA, b)
            print("completed change key")

            return crypto

    def send(self, msg):
        encrypt_data = self.enc_obj.enc_msg(msg)

        # the length of the encrypted message
        data_len = str(len(encrypt_data)).zfill(self.msgLenBytes).encode()
        try:
            self.socket.send(data_len + encrypt_data)
        except Exception as e:
            sys.exit("Server is closed try again later")

    def _close(self):
        self.socket.close()

    def _recv_file(self, client, file_name, file_len):
        data = bytearray()
        try:
            while len(data) < file_len:
                slices = file_len - len(data)
                if slices > 1024:
                    data.extend(client.recv(1024))
                else:
                    data.extend(client.recv(slices))
                    break
        except Exception as e:
            self.recvQ.put(("fail", file_name))
            print("main server in recv file comm ", str(e))
            self._close()
        else:
            self.recvQ.put(("success", file_name, data))


if __name__ == "__main__":
    msgQ = queue.Queue()
    server = ClientComm(Settings.SERVERIP, Settings.SERVERPORT, msgQ, 2)

    while not server.enc_obj:
        pass

    server.send(clientProtocol.pack_register_request("lior123", "check123", "reefg19@gmail.com"))

    while True:
        data = msgQ.get()
        print(data)

