import queue
import threading
import serverComm
import serverProtocol
import Settings
import DB
import encryption


def main_loop():
    """
    :return: the main loop of the server
    """
    # will be the database object later
    msg_q = queue.Queue()
    recv_commands = {"01": _handle_registration, "02": _handle_login}
    # used_port = []

    main_server = serverComm.ServerComm(Settings.SERVERPORT, msg_q, 3)
    threading.Thread(target=_handle_messages, args=(main_server, msg_q, recv_commands, )).start()


def _handle_messages(main_server, msg_q, recv_commands):
    """
    :param main_server: the server object
    :param msg_q: the queue of messages to handle
    :param recv_commands: dictionary of functions according to their opcode
    :return: takes the message out the message queue and runs the according function
    """
    my_db = DB.DB()

    while True:
        ip, data = msg_q.get()
        protocol_num, params = serverProtocol.unpack_message(data)

        if protocol_num in recv_commands.keys():
            recv_commands[protocol_num](main_server, my_db, ip, *params)


def _handle_registration(main_server, db, client_ip, username, password, mail):
    """
    :param main_server: the server object
    :param username: username
    :param password: password
    :param mail: email
    :param db: data base
    :param client_ip: clients ip
    :return: adds user to the data base and send message by protocol
    """
    ans = db.add_user(username, password, mail)
    msg = serverProtocol.pack_register_response(ans)
    main_server.send(client_ip, msg)

    if ans == 0:
        print(f"Added user - {username}")


def _handle_login(main_server, db, client_ip, username, password):
    status = 1
    if encryption.hash_msg(password) == db.get_password(username):
        status = 0

    msg = serverProtocol.pack_login_response(status)
    main_server.send(client_ip, msg)

    if status == 0:
        main_server.send(client_ip, serverProtocol.pack_files_message(username))


if __name__ == '__main__':
    main_loop()
