import queue
import clientComm
import clientProtocol
import Settings
import threading


def main_loop():
    msg_q = queue.Queue()
    recv_commands = {"01": _handle_registration, "02": _handle_login, "13": _handle_files_list}
    client_socket = clientComm.ClientComm(Settings.SERVERIP, Settings.SERVERPORT, msg_q, 2)

    threading.Thread(target=_handle_messages, args=(msg_q, recv_commands, )).start()

    while not client_socket.enc_obj:
        pass

    client_socket.send(clientProtocol.pack_login_request("reef", "check123"))


def _handle_messages(msg_q, recv_commands):
    while True:
        data = msg_q.get()
        protocol_num, params = clientProtocol.unpack_message(data)
        if protocol_num == "13" and params == []:
            _handle_files_list([123])
        else:
            recv_commands[protocol_num](*params)


def _handle_registration(status):
    if status == "0":
        print("Registered")
    else:
        print("Didn't work", status)
    pass


def _handle_login(status):
    if status == "0":
        print("Logged in")
    if status == "1":
        print("Didn't work", status)
    pass


def _handle_files_list(branches):
    print(branches)


if __name__ == '__main__':
    main_loop()
