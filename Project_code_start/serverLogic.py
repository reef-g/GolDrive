import os.path
import queue
import threading
import serverComm
import serverProtocol
import Settings
import DB
import encryption
import sFileHandler


def main_loop():
    """
    :return: the main loop of the server
    """
    # will be the database object later
    msg_q = queue.Queue()
    recv_commands = {"01": _handle_registration, "02": _handle_login, "08": _handle_rename_file, "10": _handle_delete_file}
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
    :param db: the database
    :param client_ip: the clients ip
    :param username: the username of user
    :param password: the password of user
    :param mail: the mail of user
    :return: adds the user to the database and return 0 or 1 if it managed to add the user
    """
    ans = db.add_user(username, password, mail)
    msg = serverProtocol.pack_register_response(ans)
    main_server.send(client_ip, msg)

    if ans == 0:
        print(f"Added user - {username}")


def _handle_login(main_server, db, client_ip, username, password):
    """
    :param main_server: the server object
    :param db: the database
    :param client_ip: the clients ip
    :param username: the username of user
    :param password: the password of user
    :return: adds the user to the database and return 0 or 1 if the username and password matched an existing user
    """
    status = 1
    if encryption.hash_msg(password) == db.get_password(username):
        status = 0

    msg = serverProtocol.pack_login_response(status)
    main_server.send(client_ip, msg)

    if status == 0:
        main_server.send(client_ip, serverProtocol.pack_files_message(username))


def _handle_delete_file(main_server, db, client_ip, path):
    """
    :param main_server:
    :param db:
    :param client_ip:
    :param path:
    :return:
    """

    path_to_send = ""

    status = sFileHandler.delete_file(f"{Settings.USER_FILES_PATH}/{path}")
    if status == 0:
        path_to_send = path

    msg = serverProtocol.pack_delete_response(status, path_to_send)
    main_server.send(client_ip, msg)


def _handle_rename_file(main_server, db, client_ip, path, new_name):
    """
    :param main_server:
    :param db:
    :param client_ip:
    :param name:
    :param new_name:
    :return:
    """

    status = sFileHandler.rename_file(f"{Settings.USER_FILES_PATH}/{path}", new_name)
    what_to_send = ()
    if status == 0:
        what_to_send = (path, new_name)

    msg = serverProtocol.pack_delete_response(status, what_to_send)
    main_server.send(client_ip, msg)


if __name__ == '__main__':
    main_loop()
