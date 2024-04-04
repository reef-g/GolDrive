import os.path
import queue
import threading
import portsHandler
import serverComm
import serverProtocol
from settings import CurrentSettings as Settings
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
    user_by_ip = {}
    code_dic = {}

    recv_commands = {"01": _handle_registration, "02": _handle_login, "05": _handle_change_email,
                     "06": _handle_change_password, "07": _send_email, "08": _handle_rename_file,
                     "09": _handle_share_file, "10": _handle_delete_file, "13": _handle_create_dir,
                     "17": _handle_send_email, "18": _handle_move_file, "19": _handle_paste_file,
                     "23": _handle_email_login, "24": _handle_email_register, "25": _handle_check_email,
                     "26": _handle_forgot_password, "27": _handle_zip_folder}

    while True:
        ip, data = msg_q.get()
        protocol_num, params = serverProtocol.unpack_message(data)
        if protocol_num == "01" or protocol_num == "05" or protocol_num == "07" or protocol_num == "02" or \
                protocol_num == "17" or protocol_num == "23" or protocol_num == "24" or protocol_num == "25":
            params.insert(0, code_dic)

        if protocol_num == "02" or protocol_num == "09" or protocol_num == "23":
            params.insert(0, user_by_ip)

        if protocol_num in recv_commands.keys():
            recv_commands[protocol_num](main_server, my_db, ip, *params)
        else:
            print(f"{protocol_num} not in recv commands.")


def _handle_registration(main_server, db, client_ip, code_dic, username, password, email):
    """
    :param main_server: the server object
    :param db: the database
    :param client_ip: the clients ip
    :param username: the username of user
    :param password: the password of user
    :param email: the email of user
    :return: adds the user to the database and return 0 or 1 if it managed to add the user
    """
    status = 2

    if 10 >= len(username) >= 4 and len(password) >= 4:
        if not db.username_exist(username):
            status = 0
            _send_email(main_server, db, client_ip, code_dic, email)
        else:
            status = 1

    msg = serverProtocol.pack_register_response(status, username, password, email)
    main_server.send(client_ip, msg)


def _handle_email_register(main_server, db, client_ip, code_dic, username, password, email, code, dont_ask_again):
    """
    :param main_server: the server object
    :param db: the database
    :param client_ip: the clients ip
    :param code_dic: dictionary containing the code sent to an email
    :param username: the username of the client
    :param password: the password of the client
    :param email: the email of the client
    :param code: the code entered
    :param dont_ask_again: does the user want to verify his email in his computer
    :return: try's adding the user to the database and sends response to the client
    """
    ans = 2

    if email in code_dic:
        if code_dic[email] == code:
            if 4 <= len(username) <= 10 and len(password) >= 4:
                ans = db.add_user(username, password, email)

            if ans == 0 and dont_ask_again == "True":
                db.add_remembered_ip(username, client_ip)

    msg = serverProtocol.pack_register_verify_response(ans)
    main_server.send(client_ip, msg)

    if ans == 0:
        if not os.path.isdir(f"{Settings.SERVER_FILES_PATH}/{username}"):
            os.mkdir(f"{Settings.SERVER_FILES_PATH}/{username}")
            os.mkdir(f"{Settings.SERVER_FILES_PATH}/{username}/@#$SHAREDFILES$#@")


def _handle_login(main_server, db, client_ip, users_by_ip, code_dic, username, password):
    """
    :param main_server: the server object
    :param db: the database
    :param client_ip: the clients ip
    :param username: the username of user
    :param password: the password of user
    :return: adds the user to the database and return 0 or 1 if the username and password matched an existing user
    """
    status = 1
    email = db.get_email(username)

    if encryption.hash_msg(password) == db.get_password(username):
        status = 0

    msg = serverProtocol.pack_login_response(status, email)

    if status == 0:
        remembered_ips = db.get_ips_of_user(username)

        if client_ip in remembered_ips:
            _create_files_thread(main_server, db, client_ip, users_by_ip, username)
            msg = serverProtocol.pack_login_verify_response(status)
        else:
            _send_email(main_server, db, client_ip, code_dic, email)

    main_server.send(client_ip, msg)


def _handle_email_login(main_server, db, client_ip, users_by_ip, code_dic, email, code, dont_ask_again, username):
    """
    :param main_server: the server object
    :param db: the database
    :param client_ip: the clients ip
    :param code_dic: dictionary containing the code sent to an email
    :param email: the email of the client
    :param code: the code entered
    :param dont_ask_again: does the user want to verify his email in his computer
    :param username: the username of the client
    :return: checks if user entered the correct code sent to his email and sends response to client
    """
    status = 1

    if email in code_dic:
        if code_dic[email] == code:
            status = 0

            _create_files_thread(main_server, db, client_ip, users_by_ip, username)

            if dont_ask_again == "True":
                db.add_remembered_ip(username, client_ip)

    msg = serverProtocol.pack_login_verify_response(status)
    main_server.send(client_ip, msg)


def _create_files_thread(main_server, db, client_ip, users_by_ip, username):
    """
    :param main_server: the server object
    :param db: the database
    :param client_ip: the client ip
    :param users_by_ip: dictionary containing users by their ips
    :param username: username of client
    :return: gets the next available port which is used to upload and download files
    """
    users_by_ip[client_ip] = username
    port_to_give = portsHandler.PortsHandler.get_next_port()
    files_q = queue.Queue()
    files_server = serverComm.ServerComm(port_to_give, files_q, 10)
    threading.Thread(target=handle_files, args=(files_server, files_q, db,)).start()
    port_msg = serverProtocol.pack_upload_port(port_to_give)
    main_server.send(client_ip, port_msg)

    main_server.send(client_ip, serverProtocol.pack_files_message(username))


def handle_files(files_server, files_q, db):
    """
    :param files_server: the files server object
    :param files_q: queue with messages waiting for handle
    :param db: the database
    :return: starts the correct function according to the opcode
    """
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
    path_on_server = f"{Settings.SERVER_FILES_PATH}/{path}"
    status = 0

    if os.path.isdir(path_on_server):
        try:
            shutil.rmtree(path_on_server)
        except Exception as e:
            print(f"in delete file - {str(e)}")
            status = 1

    elif os.path.isfile(path_on_server):
        try:
            os.remove(path_on_server)
        except Exception as e:
            print(f"in delete file - {str(e)}")
            status = 1
    else:
        status = 1

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
    status = sFileHandler.rename_file(f"{Settings.SERVER_FILES_PATH}/{path}", new_name)
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
    :param main_server: the server object
    :param client_ip: the clients ip
    :param path: the path of the fle uploaded
    :param data: the data of the file
    :return: uploads the file and sends response to the client
    """
    status = 0
    try:
        with open(f"{Settings.SERVER_FILES_PATH}/{path}", 'wb' if type(data) == bytes else 'w') as f:
            f.write(data)
    except Exception as e:
        print(str(e))
        status = 1

    msg = serverProtocol.pack_file_upload_response(status, path)
    main_server.send(client_ip, msg)


def _handle_create_dir(main_server, db, client_ip, path):
    """
    :param main_server: server object
    :param db: the database
    :param client_ip: the clients ip
    :param path: the path of the directory to create
    :return: creates dir and sends response to the client
    """
    status = 0
    try:
        os.mkdir(f"{Settings.SERVER_FILES_PATH}/{path}")
    except Exception as e:
        print(str(e))
        status = 1
    msg = serverProtocol.pack_create_folder_response(status)
    main_server.send(client_ip, msg)


def _handle_share_file(main_server, db, client_ip, users_by_ip, path, username):
    """
    :param main_server: the server object
    :param db: the database
    :param client_ip: the clients ip
    :param users_by_ip: dictionary of the user logged in according to the ip
    :param path: path of the file to share
    :param username: the username of the to share
    :return: shares the file and sends response to the user
    """
    status = 0
    user_who_shared = path.split('/')[0]
    path_to_add = f"{Settings.SERVER_FILES_PATH}/{username}/@#$SHAREDFILES$#@/{user_who_shared}"

    if db.username_exist(username):
        if not os.path.isdir(path_to_add):
            try:
                os.mkdir(path_to_add)
            except Exception as e:
                print(str(e))

        try:
            shutil.copy(f"{Settings.SERVER_FILES_PATH}/{path}",
                        f"{Settings.SERVER_FILES_PATH}/{username}/@#$SHAREDFILES$#@/"
                        f"{user_who_shared}")
        except Exception as e:
            print(str(e))
            status = 1

    else:
        status = 1

    msg = serverProtocol.pack_share_response(status)
    main_server.send(client_ip, msg)

    ips_to_share = [key for key, value in users_by_ip.items() if value == username]

    # sends an update to all the computer logged on to the user shared
    for ip in ips_to_share:
        msg = serverProtocol.pack_add_shared_file(path)
        main_server.send(ip, msg)


def _handle_move_file(main_server, db, client_ip, src, dst):
    """
    :param main_server: the server object
    :param db: the database
    :param client_ip: the clients ip
    :param src: the src path
    :param dst: the dst path
    :return: moves the file from src to dst and sends response to the client
    """
    status = 0
    try:
        shutil.move(f"{Settings.SERVER_FILES_PATH}/{src}", f"{Settings.SERVER_FILES_PATH}/{dst}")
    except Exception as e:
        print(str(e))
        status = 1

    msg = serverProtocol.pack_move_file_response(status, dst)
    main_server.send(client_ip, msg)


def _handle_paste_file(main_server, db, client_ip, src, dst):
    """
    :param main_server: the server object
    :param db: the database
    :param client_ip: the clients ip
    :param src: the src path
    :param dst: the dst path
    :return: sends paste file request from src to dst according to the protocol
    """
    status = 0
    full_src_path = f"{Settings.SERVER_FILES_PATH}/{src}"
    full_dst_path = f"{Settings.SERVER_FILES_PATH}/{dst}"

    try:
        shutil.copy(full_src_path, full_dst_path)
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
    """
    :param main_server: the server object
    :param my_db: the database
    :param client_ip: the clients ip
    :param code_dic: dictionary with the code sent and the email sent to
    :param email: the email the code was sent to
    :return: sends verify code email to the email
    """

    # email to send from
    sender_email = "goldriveauth@gmail.com"
    receiver_email = email
    password = "pukb pfll qplp gukh"

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Verify email"

    # the verify code
    verify_code = random.randint(100000, 999999)
    code_dic[email] = str(verify_code)
    body = f"The code to verify is {verify_code}."
    message.attach(MIMEText(body, "plain"))

    if receiver_email:
        # connect to the SMTP server
        try:
            smtp_server = smtplib.SMTP("smtp.gmail.com", 587)
            smtp_server.starttls()
            smtp_server.login(sender_email, password)

            # send the email
            smtp_server.sendmail(sender_email, receiver_email, message.as_string())

        except smtplib.SMTPException as e:
            print(f"Error: {e}")

        else:
            # disconnect from the SMTP server
            smtp_server.quit()


def _handle_change_email(main_server, db, client_ip, code_dic, username, email, code):
    """
    :param main_server: the server object
    :param db: the database
    :param client_ip: the clients ip
    :param code_dic: dictionary with the code sent to the email and the mail as key
    :param username: the username of the client
    :param email: the email of the client
    :param code: the code entered
    :return: changes the email in the database and sends response to the client
    """
    status = 1
    if email in code_dic:
        if code_dic[email] == code:
            status = db.change_email(username, email)
            del code_dic[email]

    msg = serverProtocol.pack_change_email_response(status, email)
    main_server.send(client_ip, msg)


def _handle_change_password(main_server, db, client_ip, username, old_pass, new_pass, confirmed_pass):
    """
        :param main_server: the server object
        :param db: the database
        :param client_ip: the clients ip
        :param username: the username of the client
        :param old_pass: the old password
        :param new_pass: the new password entered
        :param confirmed_pass: confirmation of the new password entered
        :return: changes password and sends response to the client
        """
    status = 1
    if new_pass == confirmed_pass and db.get_password(username) == encryption.hash_msg(old_pass) and len(new_pass) >= 4:
        status = db.change_password(username, encryption.hash_msg(new_pass))

    msg = serverProtocol.pack_change_password_response(status)
    main_server.send(client_ip, msg)


def _handle_change_photo(files_server, client_ip, username, photo_data):
    """
    :param files_server: the files server object
    :param client_ip: the clients ip
    :param username: the client username
    :param photo_data: the data of the photo
    :return: changes photo and sends response to the client
    """
    try:
        with open(f"{Settings.USER_PROFILE_PHOTOS}/{username}.png", 'wb' if type(photo_data) is bytes else 'w') as f:
            f.write(photo_data)
    except Exception as e:
        print(str(e))

    params = ("04", username)
    files_server.send_file(client_ip, params)


def _handle_delete_profile_photo(files_server, client_ip, username):
    """
    :param files_server: the files server
    :param client_ip: the clients ip
    :param username: the clients username
    :return: deletes profile photo and sends response to the client
    """
    status = sFileHandler.delete_file(f"{Settings.USER_PROFILE_PHOTOS}/{username}.png")
    if status == 0:
        params = ("04", 'd')
        files_server.send_file(client_ip, params)


def _handle_send_email(main_server, db, client_ip, code_dic, username):
    """
    :param main_server: the server object
    :param db: the database
    :param client_ip: the clients ip
    :param code_dic: dictionary with email and the code that was sent to it
    :param username: the username of the user
    :return: sends email to the user and sends response to the user
    """
    email = db.get_email(username)
    _send_email(main_server, db, client_ip, code_dic, email)

    if email:
        status = 0
    else:
        status = 1

    msg = serverProtocol.pack_send_email_response(status, email)
    main_server.send(client_ip, msg)


def _handle_check_email(main_server, db, client_ip, code_dic, email, code):
    """
    :param main_server: the server object
    :param db: the database
    :param client_ip: the clients ip
    :param code_dic: dictionary built by email and the code that was sent to it
    :param email: the clients email
    :param code: the code entered
    :return: checks if the code entered is the same one that was send and sends response to the client
    """
    status = 1

    if email in code_dic:
        if code_dic[email] == code:
            status = 0

    msg = serverProtocol.pack_check_code_response(status)
    main_server.send(client_ip, msg)


def _handle_forgot_password(main_server, db, client_ip, username, password, confirmed_password):
    """
    :param main_server: the server object
    :param db: the database
    :param client_ip: the clients ip
    :param username: the username of the client
    :param password: the password of the client
    :param confirmed_password: the confirmation of the password
    :return: changed the password and sends response to the client
    """
    status = 1

    if password == confirmed_password and len(password) >= 4:
        status = db.change_password(username, encryption.hash_msg(password))

    msg = serverProtocol.pack_forgot_password_response(status)
    main_server.send(client_ip, msg)


def _handle_zip_folder(main_server, db, client_ip, folder_path):
    """
    :param main_server: the server object
    :param db: the database
    :param client_ip: the clients ip
    :param folder_path: the path of the folder
    :return: zips the folder and sends response to the client
    """
    status, folder_name = sFileHandler.create_zip(f"{Settings.SERVER_FILES_PATH}/{folder_path}")
    msg = serverProtocol.pack_zip_folder_response(status, folder_name)
    main_server.send(client_ip, msg)


if __name__ == '__main__':
    main_loop()
