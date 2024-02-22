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
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


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
    code_dic = {}

    recv_commands = {"01": _handle_registration, "02": _handle_login, "05": _handle_change_email,
                     "06": _handle_change_password, "07": _send_email, "08": _handle_rename_file,
                     "09": _handle_share_file, "10": _handle_delete_file, "13": _handle_create_dir,
                     "18": _handle_move_file, "19": _handle_paste_file}

    while True:
        ip, data = msg_q.get()
        protocol_num, params = serverProtocol.unpack_message(data)
        if protocol_num == "02" or protocol_num == "09":
            params.insert(0, ip_by_username)
        elif protocol_num == "05" or protocol_num == "07":
            params.insert(0, code_dic)

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
    :param password: the password of userf
    :param mail: the mail of user
    :return: adds the user to the database and return 0 or 1 if it managed to add the user
    """
    ans = 2

    if 4 <= len(username) <= 10 and len(password) >= 4:
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

    if status == 0:
        ip_by_users[username] = client_ip
        port_to_give = portsHandler.PortsHandler.get_next_port()
        files_q = queue.Queue()
        files_server = serverComm.ServerComm(port_to_give, files_q, 10)
        threading.Thread(target=handle_files, args=(files_server, files_q, db,)).start()
        port_msg = serverProtocol.pack_upload_port(port_to_give)
        main_server.send(client_ip, port_msg)

        main_server.send(client_ip, serverProtocol.pack_files_message(username))

    msg = serverProtocol.pack_login_response(status)
    main_server.send(client_ip, msg)


def handle_files(files_server, files_q, db):
    recv_commands = {"04": _handle_change_photo, "11": _handle_download_file, "12": _handle_upload_file,
                     "20": _handle_open_file, "21": _handle_get_details, "22": _handle_delete_profile_photo}

    while True:
        ip, data = files_q.get()

        if len(data) != 0:
            if data[0] == "12" or data[0] == "04":
                protocol_num, *params = data
            else:
                protocol_num, params = serverProtocol.unpack_message(data)

            if protocol_num == "21":
                params.insert(0, db)

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
            shutil.copy(f"{Settings.USER_FILES_PATH}/{path}",
                        f"{Settings.USER_FILES_PATH}/{username}/@#$SHAREDFILES$#@/"
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


def _handle_get_details(main_server, client_ip, db, username):
    email = db.get_email(username)

    params = ('21', username, email)
    main_server.send_file(client_ip, params)


def _send_email(main_server, my_db, client_ip, code_dic, email):
    # Email credentials
    sender_email = "goldriveauth@gmail.com"
    receiver_email = email
    password = "pukb pfll qplp gukh"

    # Create the MIME object
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Verify email"

    verify_code = random.randint(100000, 999999)
    code_dic[email] = str(verify_code)
    # Add the email body
    body = f"The code to verify is {verify_code}."
    message.attach(MIMEText(body, "plain"))

    # Connect to the SMTP server
    try:
        smtp_server = smtplib.SMTP("smtp.gmail.com", 587)
        smtp_server.starttls()
        smtp_server.login(sender_email, password)

        # Send the email
        smtp_server.sendmail(sender_email, receiver_email, message.as_string())

    except smtplib.SMTPException as e:
        print(f"Error: {e}")

    else:
        # Disconnect from the SMTP server
        smtp_server.quit()


def _handle_change_email(main_server, db, client_ip, code_dic, username, email, code):
    status = 1
    if email in code_dic:
        if code_dic[email] == code:
            status = db.change_email(username, email)
            del code_dic[email]

    msg = serverProtocol.pack_change_email_response(status, email)
    main_server.send(client_ip, msg)


def _handle_change_password(main_server, db, client_ip, username, old_pass, new_pass, confirmed_pass):
    status = 1
    if new_pass == confirmed_pass and db.get_password(username) == encryption.hash_msg(old_pass):
        status = db.change_password(username, encryption.hash_msg(new_pass))

    msg = serverProtocol.pack_change_password_response(status)
    main_server.send(client_ip, msg)


def _handle_change_photo(files_server, client_ip, username, photo_data):
    try:
        with open(f"{Settings.USER_PROFILE_PHOTOS}/{username}.png", 'wb' if type(photo_data) is bytes else 'w') as f:
            f.write(photo_data)
    except Exception as e:
        print(str(e))

    params = ("04", username)
    files_server.send_file(client_ip, params)


def _handle_delete_profile_photo(files_server, client_ip, username):
    status = sFileHandler.delete_file(f"{Settings.USER_PROFILE_PHOTOS}/{username}.png")
    if status == 0:
        params = ("04", 'd')
        files_server.send_file(client_ip, params)


if __name__ == '__main__':
    main_loop()
