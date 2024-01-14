import queue
import clientComm
import clientProtocol
import Settings
import threading


def main_loop():
    msg_q = queue.Queue()
    recv_commands = {"01": _handle_registration, "02": _handle_login}
    client_socket = clientComm.ClientComm(Settings.SERVERIP, Settings.SERVERPORT, msg_q, 2)

    threading.Thread(target=_handle_messages, args=(client_socket, msg_q, recv_commands, )).start()


def _handle_messages(client_socket, msg_q, recv_commands):
    while True:
        data = msg_q.get()
        protocol_num, params = clientProtocol.unpack_message(data)
        recv_commands[protocol_num](client_socket, *params)



def _handle_registration(clientSocket, status):
    # change graphics
    pass

def _handle_login(clientSocket, status):
    # change graphics
    pass
