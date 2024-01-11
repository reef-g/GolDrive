import socket
import select
import threading
import queue
import setting
import serverProtocol


class ServerComm:
    def __init__(self, port, recvQ, msgLenBytes):
        """
        :param port
        :param recvQ
        """
        self.port = port
        self.recvQ = recvQ
        self.serverSocket = socket.socket()
        self.openClients = {}  # [socket]:[ip, key]
        self.isRunning = False
        self.msgLenBytes = msgLenBytes

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

                    threading .Thread(target=self._change_key,args=(client, addr[0],)).start()
                    continue

                try:
                    data_len = int(currSocket.recv(self.msgLenBytes).decode())
                    data = currSocket.recv(data_len).decode()
                except Exception as e:
                    print("main server in server comm ", str(e))
                    self._handle_disconnect(currSocket)

                else:
                    if data == "":
                        self._handle_disconnect(currSocket)

                    else:
                        # data = decrypt self.openClients[currSocket][1] (data
                        if self.port == setting.SERVERPORT:
                            self.recvQ.put((self.openClients[currSocket][0], data))

                        # files server
                        else:
                            fileName, fileLen = serverProtocol.unpack_message(data)
                            self._recv_file(currSocket, fileName, fileLen)

    def _recv_file(self,client,fileName,fileLen):
        data = bytearray()
        try:
            while len(data) < fileLen:
                slice = fileLen - len(data)
                if slice > 1024:
                    data.extend(client.recv(1024))
                else:
                    data.extend(client.recv(slice))
                    break
        except Exception as e:
            self.recvQ.put(("fail", self.openClients[client][0], fileName))
            print("main server in recv file comm ", str(e))
            self._handle_disconnect(client)
        else:
            self.recvQ.put(("success", self.openClients[client][0], fileName,data))




    def _change_key(self, client, ip):
        pass
        # get_delf_num
        # build protocol
        # client.send(
        # client.rev
        # crypto - create_sym(a,b)
        #self.openClients[client]=(ip, crypto)

        print(f"{ip} - complete change key")

    def _handle_disconnect(self, sock):
        if sock in self.openClients.keys():
            print(f"{self.openClients[sock]} - Disconnected")
            del self.openClients[sock]
            sock.close()


    def _find_socket_by_ip(self, ip):
        """
        :param ip:
        :return: return socket with IP ip
        """
        sock = None
        for soc in self.openClients.keys():
            if self.openClients[soc] == ip:
                sock = soc
                break
        return sock

    def send(self, ip, msg):
        """
        :param ip:
        :param msg:
        :return: sends msg to the socket with right ip
        """
        if self._running_status():
            client = self._find_socket_by_ip(ip)
            if client:
                # encrypt the msg key = self.openClients[currSocket][1]
                data_len = str(len(encrypt_data)).zfill(self.msgLenBytes).encode()
                try:
                    # send len
                    client.send(data_len + encrypt_data)
                except Exception as e:
                    print("server com - send", str(e))
                    self._handle_disconnect(client)

    # def _change_key(self, client, addr):

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

    # def _recv_file(self, path):
    #     pass

if __name__ == "__main__":
    msgQ = queue.Queue()
    server = ServerComm(1000, msgQ, 2)
