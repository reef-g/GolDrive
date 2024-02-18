import os.path
import queue
import threading
import portsHandler
import serverComm
import serverProtocol
from settings import Settings
import DB
import encryption
import sFileHandler
import shutil
import smtplib
import random


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
    ip_by_username = {}

    recv_commands = {"01": _handle_registration, "02": _handle_login, "05": _handle_change_email,
                     "08": _handle_rename_file, "09": _handle_share_file, "10": _handle_delete_file,
                     "13": _handle_create_dir, "18": _handle_move_file, "19": _handle_paste_file,
                     "21": _handle_get_details}

    while True:
        ip, data = msg_q.get()
        protocol_num, params = serverProtocol.unpack_message(data)
        if protocol_num == "02" or protocol_num == "09":
            params.insert(0, ip_by_username)

        if protocol_num in recv_commands.keys():
            recv_commands[protocol_num](main_server, my_db, ip, *params)
        else:
            print(f"{protocol_num} not in recv commands.")


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
        if not os.path.isdir(f"{Settings.USER_FILES_PATH}/{username}"):
            os.mkdir(f"{Settings.USER_FILES_PATH}/{username}")
            os.mkdir(f"{Settings.USER_FILES_PATH}/{username}/@#$SHAREDFILES$#@")


def _handle_login(main_server, db, client_ip, ip_by_users, username, password):
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
        ip_by_users[username] = client_ip
        port_to_give = portsHandler.PortsHandler.get_next_port()
        files_q = queue.Queue()
        files_server = serverComm.ServerComm(port_to_give, files_q, 10)
        threading.Thread(target=handle_files, args=(files_server, files_q,)).start()
        port_msg = serverProtocol.pack_upload_port(port_to_give)
        main_server.send(client_ip, port_msg)

        main_server.send(client_ip, serverProtocol.pack_files_message(username))


def handle_files(files_server, files_q):
    recv_commands = {"11": _handle_download_file, "12": _handle_upload_file, "20": _handle_open_file}

    while True:
        ip, data = files_q.get()

        if data[0] == "12":
            protocol_num, *params = data
        else:
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


def _handle_download_file(main_server, client_ip, path, selected_path):
    """
    :param main_server: the server object
    :param client_ip: the clients ip
    :param path: the path of the file to download
    :return: returns the data of the file
    """
    params = ("11", path, selected_path)
    main_server.send_file(client_ip, params)


def _handle_open_file(main_server, client_ip, path):
    """
    :param main_server: the server object
    :param client_ip: the clients ip
    :param path: the path of the file to download
    :return: returns the data of the file
    """
    params = ("20", path)
    main_server.send_file(client_ip, params)


def _handle_upload_file(main_server, client_ip, path, data):
    """
    :param main_server:
    :param client_ip:
    :param path:
    :param data:
    :return:
    """
    status = 0
    try:
        with open(f"{Settings.USER_FILES_PATH}/{path}", 'wb' if type(data) == bytes else 'w') as f:
            f.write(data)
    except Exception as e:
        print(str(e))
        status = 1

    msg = serverProtocol.pack_file_upload_response(status, path)
    main_server.send(client_ip, msg)


def _handle_create_dir(main_server, db, client_ip, path):
    status = 0
    try:
        os.mkdir(f"{Settings.USER_FILES_PATH}/{path}")
    except Exception as e:
        print(str(e))
        status = 1
    msg = serverProtocol.pack_create_folder_response(status)
    main_server.send(client_ip, msg)


def _handle_share_file(main_server, db, client_ip, ip_by_users, path, username):
    status = 0
    user_who_shared = path.split('/')[0]
    path_to_add = f"{Settings.USER_FILES_PATH}/{username}/@#$SHAREDFILES$#@/{user_who_shared}"

    if db.username_exist(username):
        if not os.path.isdir(path_to_add):
            try:
                os.mkdir(path_to_add)
            except Exception as e:
                print(str(e))

        try:
            shutil.copy(f"{Settings.USER_FILES_PATH}/{path}", f"{Settings.USER_FILES_PATH}/{username}/@#$SHAREDFILES$#@/"
                                                              f"{user_who_shared}")
        except Exception as e:
            print(str(e))
            status = 1

    else:
        status = 1

    msg = serverProtocol.pack_share_response(status)
    main_server.send(client_ip, msg)

    if username in ip_by_users:
        msg = serverProtocol.pack_add_shared_file(path)
        main_server.send(ip_by_users[username], msg)


def _handle_move_file(main_server, db, client_ip, src, dst):
    status = 0
    try:
        shutil.move(f"{Settings.USER_FILES_PATH}/{src}", f"{Settings.USER_FILES_PATH}/{dst}")
    except Exception as e:
        print(str(e))
        status = 1

    msg = serverProtocol.pack_move_file_response(status, dst)
    main_server.send(client_ip, msg)


def _handle_paste_file(main_server, db, client_ip, src, dst):
    status = 0
    try:
        shutil.copy(f"{Settings.USER_FILES_PATH}/{src}", f"{Settings.USER_FILES_PATH}/{dst}")
    except Exception as e:
        print(str(e))
        status = 1

    msg = serverProtocol.pack_paste_file_response(status)
    main_server.send(client_ip, msg)


def _handle_get_details(main_server, db, client_ip, username):
    email = db.get_email(username)

    msg = serverProtocol.pack_get_details_response(email)
    main_server.send(client_ip, msg)


def _handle_change_email(main_server, db, client_ip, username, email):
    # Set your email and password
    sender_email = 'cybercheck818@gmail.com'
    sender_password = '!reef7333'

    # Set the recipient email address
    recipient_email = email

    # Create the email content
    subject = 'Verify email'
    num_to_verify = random.randint(100000, 1000000)
    body = f'The number to verify is: {num_to_verify}'
    email_message = f"Subject: {subject}\n\n{body}"

    # Set up the SMTP server
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587

    # Establish a connection to the SMTP server
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()

    # Login to your email account
    server.login(sender_email, sender_password)

    # Send the email
    try:
        server.sendmail(sender_email, recipient_email, email_message)
    except Exception as e:
        print(str(e))
        status = 1

    # Quit the SMTP server
    server.quit()

    if '@' in email:
        status = db.change_email(username, email)
    else:
        status = 1

    msg = serverProtocol.pack_change_email_response(status, email)
    main_server.send(client_ip, msg)



if __name__ == '__main__':
    main_loop()
