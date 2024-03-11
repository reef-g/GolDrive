import socket
import threading
import sys
import queue
import encryption
from settings import CurrentSettings as Settings
import clientProtocol
import wx
from pubsub import pub


class ClientComm:
    def __init__(self, server_ip, port, recv_q, msg_len_bytes):
        """
        init of clientComm object
        :param server_ip: ip of the server
        :param port: port of the server
        :param recv_q: msgs queue
        :param msg_len_bytes: how many bytes to fill to
        """
        self.server_ip = server_ip
        self.port = port
        self.recvQ = recv_q
        self.socket = socket.socket()
        self.msgLenBytes = msg_len_bytes
        self.enc_obj = None

        threading.Thread(target=self._main_loop).start()

    def _main_loop(self):
        """
        main loop of the server
        :return: receives data and puts in the q
        """
        try:
            self.socket.connect((self.server_ip, self.port))
        except Exception as e:
            sys.exit("Server is closed try again later, " + str(e))

        else:
            # changing key
            self.enc_obj = self._change_key()

            while True:
                try:
                    leng = self.socket.recv(self.msgLenBytes).decode()
                    data = self.socket.recv(int(leng))
                except Exception as e:
                    sys.exit("Server is closed try again later")

                decrypted_data = self.enc_obj.dec_msg(data)

                # is it the default port
                if self.port == Settings.SERVERPORT:
                    self.recvQ.put(decrypted_data)
                else:
                    opcode, params = clientProtocol.unpack_message(decrypted_data)

                    if opcode == "04" or opcode == "11" or opcode == "20" or opcode == "21":
                        if params[0] == "0":
                            params = (opcode, *params[1:])
                            self._recv_file(params)
                        else:
                            self.recvQ.put(decrypted_data)
                    else:
                        self.recvQ.put(decrypted_data)

    def _change_key(self):
        """
        swaps symmetric key with server
        """
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
        """
        :param msg: msg to send
        :return: sends the message to the server
        """
        encrypt_data = self.enc_obj.enc_msg(msg)

        # the length of the encrypted message
        data_len = str(len(encrypt_data)).zfill(self.msgLenBytes).encode()
        try:
            self.socket.send(data_len + encrypt_data)
        except Exception as e:
            sys.exit("Server is closed try again later")

    def _close(self):
        """
        closes the client socket
        """
        self.socket.close()

    def _recv_file(self, params):
        """
        :param params: the params to use
        :return: receives file and put in the q accordingly
        """
        opcode = params[0]
        path, selected_path, Type, email = "", "", "", ""
        if opcode == "04":
            file_len = params[1]
            wx.CallAfter(pub.sendMessage, "startBar", name=path.split('/')[-1], opcode=opcode)
        elif opcode == "11":
            file_len, path, selected_path = params[1:]
            wx.CallAfter(pub.sendMessage, "startBar", name=path.split('/')[-1], opcode=opcode)
        elif opcode == "21":
            file_len, email = params[1:]
        else:
            file_len, Type = params[1:]

        data = bytearray()
        file_len = int(file_len)

        try:
            while len(data) < file_len:
                slices = file_len - len(data)

                if slices > 1024:
                    if opcode == "11" or opcode == "04":
                        wx.CallAfter(pub.sendMessage, "changeProgress",
                                     percent=int((len(data) / file_len) * 100), opcode=opcode)
                    data.extend(self.socket.recv(1024))
                else:
                    data.extend(self.socket.recv(slices))
                    break

        except Exception as e:
            if opcode == "04":
                self.recvQ.put(("04", '1', None))
            elif opcode == "11":
                self.recvQ.put(("11", '1', path, selected_path, None))
            elif opcode == "21":
                self.recvQ.put(("21", None, None))
            else:
                self.recvQ.put(("20", '1', Type, None))

            print("main server in recv file comm ", str(e))
            self._close()
        else:
            if opcode == "04":
                wx.CallAfter(pub.sendMessage, "changeProgress",
                             percent=int((len(data) / file_len) * 100), opcode=opcode)
                self.recvQ.put(("04", self.enc_obj.dec_msg(data)))
            elif opcode == "11":
                wx.CallAfter(pub.sendMessage, "changeProgress",
                             percent=int((len(data) / file_len) * 100), opcode=opcode)
                self.recvQ.put(("11", '0', path, selected_path, self.enc_obj.dec_msg(data)))
            elif opcode == "21":
                self.recvQ.put(("21", email, self.enc_obj.dec_msg(data)))

            else:
                self.recvQ.put(("20", '0', Type, self.enc_obj.dec_msg(data)))

    def send_file(self, opcode, path, currPath):
        """
        :param opcode: opcode of msg to send
        :param path: path of file to send
        :param currPath: path in the server
        :return: sends file to the server
        """
        try:
            with open(path, 'rb') as f:
                data = f.read()
        except Exception as e:
            print(str(e))

        else:
            cryptFile = self.enc_obj.enc_msg(data)
            if opcode == 12:
                msg = clientProtocol.pack_upload_file_request(f"{currPath}/{path.split('/')[-1]}".lstrip('/'),
                                                              len(cryptFile))
            else:
                msg = clientProtocol.pack_change_photo_request(currPath, len(cryptFile))

            self.send(msg)
            try:
                self.socket.send(cryptFile)
            except Exception as e:
                print(str(e))

    def did_change_work(self):
        """
        :return: did the change key work
        """
        return self.enc_obj is not None


if __name__ == "__main__":
    msgQ = queue.Queue()
    server = ClientComm(Settings.SERVERIP, Settings.SERVERPORT, msgQ, 2)

    while not server.enc_obj:
        pass

    server.send(clientProtocol.pack_register_request("lior123", "check123", "reefg19@gmail.com"))

    while True:
        data = msgQ.get()
        print(data)
