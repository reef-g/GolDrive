import socket
import select
import threading
import queue
import Settings
import serverProtocol
import encryption


class ServerComm:
    def __init__(self, port, recv_q, msg_len_bytes):
        """
        :param port
        :param recv_q
        """
        self.port = port
        self.recv_q = recv_q
        self.serverSocket = socket.socket()
        self.openClients = {}  # [socket]:[ip, key]
        self.isRunning = False
        self.msgLenBytes = msg_len_bytes

        threading.Thread(target=self._main_loop).start()

    def _main_loop(self):
        """
        :return: main loop
        """
        self.serverSocket.bind(('0.0.0.0', self.port))
        self.serverSocket.listen(3)
        self.isRunning = True
        while self.isRunning:
            rlist, wlist, xlist = select.select([self.serverSocket] + list(self.openClients.keys()),
                                                list(self.openClients.keys()), [], 0.03)

            for currSocket in rlist:
                if currSocket is self.serverSocket:
                    client, addr = self.serverSocket.accept()
                    print(f"{addr[0]} - Connected")

                    threading.Thread(target=self._change_key, args=(client, addr[0],)).start()
                    continue

                try:
                    data_len = int(currSocket.recv(self.msgLenBytes).decode())
                    data = currSocket.recv(data_len).decode()
                    enc_obj = self.openClients[currSocket][1]

                    decrypted_data = enc_obj.dec_msg(data)
                except Exception as e:
                    print("main server in server comm ", str(e))
                    self._handle_disconnect(currSocket)

                else:
                    if decrypted_data == "":
                        self._handle_disconnect(currSocket)

                    else:
                        if self.port == Settings.SERVERPORT:
                            self.recv_q.put((self.openClients[currSocket][0], decrypted_data))

                        # files server
                        else:
                            file_name, file_len = serverProtocol.unpack_message(decrypted_data)
                            self._recv_file(currSocket, file_name, file_len)

    def _change_key(self, client, ip):
        """
        :param client: client socket
        :param ip: client ip
        :return: exchanges a symmetrical keys in order to get aes key
        """
        privateA, a = encryption.get_dh_factor()
        try:
            client.send((str(a).zfill(10)).encode())
            b = int(client.recv(10).decode())
        except Exception as e:
            print("in change key ", str(e))
            client.close()
        else:
            crypto = encryption.create_symmetry_key(privateA, b)
            self.openClients[client] = [ip, crypto]
            print(f"{ip} - complete change key")

    def _handle_disconnect(self, sock):
        if sock in self.openClients.keys():
            print(f"{self.openClients[sock][0]} - Disconnected")
            del self.openClients[sock]
            sock.close()

    def _find_socket_by_ip(self, ip):
        """
        :param ip:
        :return: return socket with IP ip
        """
        sock = None
        for soc in self.openClients.keys():
            if self.openClients[soc][0] == ip:
                sock = soc
                break
        return sock

    def send(self, ip, data):
        """
        :param ip: ip to send to
        :param data: data of message to send
        :return: sends msg to the socket with right ip
        """
        if self._running_status():
            client = self._find_socket_by_ip(ip)
            if client:
                enc_obj = self.openClients[client][1]
                encrypt_data = enc_obj.enc_msg(data)

                # the length of the encrypted message
                data_len = str(len(encrypt_data)).zfill(self.msgLenBytes).encode()
                try:
                    client.send(data_len + encrypt_data)
                except Exception as e:
                    print("server com - send", str(e))
                    self._handle_disconnect(client)

    def _close_server(self):
        """
        :return: changes server status to close it
        """
        self.isRunning = False

    def _running_status(self):
        """
        :return: is server running
        """
        return self.isRunning

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
            self.recv_q.put(("fail", self.openClients[client][0], file_name))
            print("main server in recv file comm ", str(e))
            self._handle_disconnect(client)
        else:
            self.recv_q.put(("success", self.openClients[client][0], file_name, data))


if __name__ == "__main__":
    msgQ = queue.Queue()
    server = ServerComm(1000, msgQ, 2)
