import socket
import threading
import sys
import queue


class ClientComm:
    def __init__(self, serverIp, port, recvQ, msgLenBytes):
        self.serverIp = serverIp
        self.port = port
        self.recvQ = recvQ
        self.socket = socket.socket()
        self.msgLenBytes = msgLenBytes

        threading.Thread(target=self._main_loop).start()

    def _main_loop(self):
        try:
            self.socket.connect((self.serverIp, self.port))
        except Exception as e:
            sys.exit("Server is closed try again later")

        while True:
            try:
                data = self.socket.recv(1024).decode()
            except Exception as e:
                sys.exit("Server is closed try again later")

            self.recvQ.put(data)

    def _change_key(self):
        pass

    def send(self, msg):
        try:
            self.socket.send(msg.encode())
        except Exception as e:
            sys.exit("Server is closed try again later")

    def _close(self):
        self.socket.close()


if __name__ == "__main__":
    msgQ = queue.Queue()
    server = ClientComm("127.0.0.1", 1000, msgQ, 2)
