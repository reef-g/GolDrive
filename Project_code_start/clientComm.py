import socket
import threading
import sys
import queue
import encryption
import Settings
import clientProtocol
import wx
from pubsub import pub


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
                opcode, params = clientProtocol.unpack_message(decrypted_data)
                if opcode == "11" or opcode == "20":
                    if params[0] == "0":
                        params = (opcode, *params[1:])
                        self._recv_file(params)
                    else:
                        self.recvQ.put(decrypted_data)
                else:
                    self.recvQ.put(decrypted_data)

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

    def _recv_file(self, params):
        opcode = params[0]
        path, selected_path, Type = "", "", ""
        if opcode == "11":
            file_len, path, selected_path = params[1:]
            path = '/'.join(path.split('/')[1::]).lstrip('/')
        else:
            file_len, Type = params[1:]

        data = bytearray()
        file_len = int(file_len)

        try:
            while len(data) < file_len:
                slices = file_len - len(data)

                if slices > 1024:
                    data.extend(self.socket.recv(1024))
                    wx.CallAfter(pub.sendMessage, "changeStatus", name=path, percent=int((len(data) / file_len)*100))
                else:
                    data.extend(self.socket.recv(slices))
                    wx.CallAfter(pub.sendMessage, "changeStatus", name=path, percent=int((len(data) / file_len)*100))
                    break

        except Exception as e:
            if opcode == "11":
                self.recvQ.put(("11", '1', path, selected_path, None))
            else:
                self.recvQ.put(("20", '1', Type, None))

            print("main server in recv file comm ", str(e))
            self._close()
        else:
            if opcode == "11":
                self.recvQ.put(("11", '0', path, selected_path, self.enc_obj.dec_msg(data)))
            else:
                self.recvQ.put(("20", '0', Type, self.enc_obj.dec_msg(data)))

    def send_file(self, path, currPath):
        try:
            with open(path, 'rb') as f:
                data = f.read()
        except Exception as e:
            print(str(e))

        else:
            cryptFile = self.enc_obj.enc_msg(data)
            msg = clientProtocol.pack_upload_file_request(f"{currPath}/{path.split('/')[-1]}".lstrip('/'), len(cryptFile))
            self.send(msg)
            try:
                self.socket.send(cryptFile)
            except Exception as e:
                print(str(e))


if __name__ == "__main__":
    msgQ = queue.Queue()
    server = ClientComm(Settings.SERVERIP, Settings.SERVERPORT, msgQ, 2)

    while not server.enc_obj:
        pass

    server.send(clientProtocol.pack_register_request("lior123", "check123", "reefg19@gmail.com"))

    while True:
        data = msgQ.get()
        print(data)

