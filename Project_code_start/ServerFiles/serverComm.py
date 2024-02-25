import os.path
import socket
import select
import threading
import queue
from settings import HomeSettings as Settings
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
                    data = currSocket.recv(data_len)
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
                            opcode, params = serverProtocol.unpack_message(decrypted_data)

                            if opcode == "12" or opcode == "04":
                                self.recv_file(opcode, currSocket, *params)
                            else:
                                self.recv_q.put((self.openClients[currSocket][0], decrypted_data))

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

    def recv_file(self, opcode, client, file_path, file_len):
        data = bytearray()
        file_len = int(file_len)
        ip = self.openClients[client][0]

        try:
            while len(data) < file_len:
                slices = file_len - len(data)
                if slices > 1024:
                    data.extend(client.recv(1024))
                else:
                    data.extend(client.recv(slices))
                    break
        except Exception as e:
            if opcode == "12":
                self.recv_q.put((ip, ("12", file_path, None)))
            else:
                self.recv_q.put((ip, ("04", file_path, None)))
            print("main server in recv file comm ", str(e))
            self._handle_disconnect(client)
        else:
            decData = self.openClients[client][1].dec_msg(data)
            if opcode == "12":
                self.recv_q.put((ip, ("12", file_path, decData)))
            else:
                self.recv_q.put((ip, ("04", file_path, decData)))

    def send_file(self, client_ip, params):
        client_socket = self._find_socket_by_ip(client_ip)

        try:
            opcode = params[0]
        except Exception as e:
            print("in send file - ", str(e))

        else:
            if client_socket:
                status = 0

                # applying correct variables according to the opcode
                username = "" if opcode != "04" and opcode != "21" else params[1]
                path = "" if opcode != "11" and opcode != "20" else params[1]
                selected_path = "" if opcode != "11" else params[2]
                email = "" if opcode != "21" else params[2]

                # if the user doesn't have a profile photo we give him the default photo.
                # its d since username cant be 1 char long
                if not os.path.isfile(f"{Settings.USER_PROFILE_PHOTOS}/{username}.png"):
                    username = 'd'

                path_to_read = f"{Settings.USER_FILES_PATH}/{path}" if opcode != "21" and opcode != "04" else \
                    f"{Settings.USER_PROFILE_PHOTOS}/{username}.png"

                try:
                    with open(path_to_read, 'rb') as f:
                        data = f.read()
                except Exception as e:
                    print(str(e))
                    status = 1
                    if opcode == "04":
                        msg = serverProtocol.pack_change_photo_response(status, 0)
                    elif opcode == "11":
                        msg = serverProtocol.pack_file_download_response(status, 0, path, selected_path)
                    elif opcode == "21":
                        msg = serverProtocol.pack_get_details_response(status, None, 0)
                    else:
                        msg = serverProtocol.pack_open_file_response(status, path, 0)
                    self.send(client_ip, msg)

                else:
                    cryptFile = self.openClients[client_socket][1].enc_msg(data)
                    if opcode == "04":
                        msg = serverProtocol.pack_change_photo_response(status, len(cryptFile))
                    elif opcode == "11":
                        msg = serverProtocol.pack_file_download_response(status, len(cryptFile), path, selected_path)
                    elif opcode == "21":
                        msg = serverProtocol.pack_get_details_response(status, len(cryptFile), email)
                    else:
                        msg = serverProtocol.pack_open_file_response(status, path, len(cryptFile))

                    self.send(client_ip, msg)
                    try:
                        client_socket.send(cryptFile)
                    except Exception as e:
                        print(str(e))
                        self._handle_disconnect(client_socket)



if __name__ == "__main__":
    msgQ = queue.Queue()
    server = ServerComm(1000, msgQ, 2)
