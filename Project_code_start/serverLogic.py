import os.path
import queue
import threading
import portsHandler
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
    msg_q = queue.Queue()

    main_server = serverComm.ServerComm(Settings.SERVERPORT, msg_q, 4)
    threading.Thread(target=_handle_messages, args=(main_server, msg_q,)).start()


def _handle_messages(main_server, msg_q):
    """
    :param main_server: the server object
    :param msg_q: the queue of messages to handle
    :return: takes the message out the message queue and runs the according function
    """
    my_db = DB.DB()

    recv_commands = {"01": _handle_registration, "02": _handle_login, "08": _handle_rename_file,
                     "10": _handle_delete_file}

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
        port_to_give = portsHandler.PortsHandler.get_next_port()
        files_q = queue.Queue()
        files_server = serverComm.ServerComm(port_to_give, files_q, 6)
        threading.Thread(target=handle_files, args=(files_server, files_q,)).start()
        port_msg = serverProtocol.pack_upload_port(port_to_give)
        main_server.send(client_ip, port_msg)

        main_server.send(client_ip, serverProtocol.pack_files_message(username))


def handle_files(files_server, files_q):
    recv_commands = {"11": _handle_download_file, "12": _handle_upload_file}

    while True:
        ip, data = files_q.get()
        print(ip, data)

        protocol_num, params = serverProtocol.unpack_message(data)

        if protocol_num in recv_commands.keys():
            recv_commands[protocol_num](files_server, ip, *params)


def _handle_delete_file(main_server, db, client_ip, path):
    """
    :param main_server: the server object
    :param db: the database
    :param client_ip: the clients ip
    :param path: the path of the file to delete
    :return: deletes the file and return the message by the protocol
    """

    status = sFileHandler.delete_file(f"{Settings.USER_FILES_PATH}/{path}")
    msg = serverProtocol.pack_delete_response(status)
    main_server.send(client_ip, msg)


def _handle_rename_file(main_server, db, client_ip, path, new_name):
    """
    :param main_server: the server object
    :param db: the database
    :param client_ip: the clients ip
    :param path: the path of the file to rename
    :param new_name: the new name of the file
    :return: renames the file and return the message by the protocol
    """

    status = sFileHandler.rename_file(f"{Settings.USER_FILES_PATH}/{path}", new_name)
    msg = serverProtocol.pack_rename_file_response(status, new_name)
    main_server.send(client_ip, msg)


def _handle_download_file(main_server, client_ip, path):
    """
    :param main_server: the server object
    :param client_ip: the clients ip
    :param path: the path of the file to download
    :return: returns the data of the file
    """
    print("im here")
    main_server.send_file(client_ip, path)


def _handle_upload_file(main_server, client_ip, file_name, file_len):
    main_server.recv_file(client_ip, file_name, file_len)


if __name__ == '__main__':
    main_loop()
