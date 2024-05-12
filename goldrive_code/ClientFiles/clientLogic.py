import os.path
import queue
import clientComm
import clientProtocol
from settings import CurrentSettings as Settings
import threading
from Graphics.mainPanel import MainFrame
from pubsub import pub
import wx
import secrets
import shutil
import monitorFile
import time
import sys


def main_loop():
    """
    main loop of the server
    """
    msg_q = queue.Queue()

    client_comm = clientComm.ClientComm(Settings.SERVERIP, Settings.SERVERPORT, msg_q, 4)

    starting_time = time.time()

    # giving the client 5 seconds to try connecting to the server
    while time.time() - starting_time < 5 and not client_comm.did_change_work():
        pass

    change_keys_success = client_comm.did_change_work()

    if change_keys_success:
        threading.Thread(target=_handle_messages, args=(msg_q,)).start()

        app = wx.App()
        MainFrame(client_comm)

        app.MainLoop()
    else:
        sys.exit("Server is closed ")


def _handle_messages(msg_q):
    """
    handles the messages from queue
    :param msg_q: the queue of the messages to handle
    :return: activates the according function according to the opcode
    """
    recv_commands = {"01": _show_register_dialog, "02": _show_login_dialog, "03": _handle_send_files,
                     "05": _handle_change_email, "06": _handle_change_password, "08": _handle_rename_file,
                     "09": _handle_share_file, "10": _handle_delete_file, "13": _handle_create_dir,
                     "14": _handle_add_shared_file, "16": _handle_files_port, "17": _handle_username_check,
                     "18": _handle_move_file, "19": _handle_paste_file, "23": _handle_login,
                     "24": _handle_register, "25": _handle_code_check, "26": _handle_forgot_password,
                     "27": _handle_zip_file}

    while True:
        data = msg_q.get()
        protocol_num, params = clientProtocol.unpack_message(data)

        if protocol_num == "03":
            # since * breaks the list down and we want the whole list
            _handle_send_files(params)
        else:
            recv_commands[protocol_num](*params)


def _handle_files_port(files_port):
    """
    connects to the files port
    :param files_port: the port of the files port to connect to
    :return: connects to the server to the files port
    """
    files_q = queue.Queue()
    files_comm = clientComm.ClientComm(Settings.SERVERIP, int(files_port), files_q, 10)
    threading.Thread(target=_handle_files, args=(files_comm, files_q,)).start()
    wx.CallAfter(pub.sendMessage, "updateFileComm", file_comm=files_comm)


def _handle_files(files_comm, files_q):
    """
    handles messages from the file q
    :param files_comm: the comm object of the client which handles the uploads, downloads etc.
    :param files_q: the queue of message to handle of the files port
    :return: activates the according function according to the opcode
    """
    recv_commands = {"04": _handle_change_photo, "11": _handle_download_file, "12": _handle_upload_file,
                     "20": _handle_open_file, "21": _handle_get_details}

    while True:
        data = files_q.get()
        if data[0] == "04" or data[0] == "11" or data[0] == "20" or data[0] == "21":
            protocol_num, *params = data
            if data[0] == "20":
                params.insert(0, files_comm)
        else:
            protocol_num, params = clientProtocol.unpack_message(data)

        recv_commands[protocol_num](*params)


def _show_register_dialog(status, username, password, email):
    """
    :param status: was the verify email sent successfully
    :param username: username wanting to register
    :param password: password wanting to register
    :param email: email wanting to register
    :return: either showing the verify code dialog or showing the error message
    """
    if status == "0":
        # show dialog to enter verify code
        wx.CallAfter(pub.sendMessage, "showRegisterDialog", username=username, password=password, email=email)
    elif status == "1":
        wx.CallAfter(pub.sendMessage, "showPopUp", text="User already exists.", title="Error")
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Please enter a valid username and password.", title="Error")


def _handle_register(status):
    """
    :param status: was the register successful
    :return: showing the correct msg to the screen
    """
    if status == "0":
        # registered successfully
        wx.CallAfter(pub.sendMessage, "registerOk")
    elif status == "1":
        wx.CallAfter(pub.sendMessage, "showPopUp", text="User already exists.", title="Error")
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Wrong code entered.", title="Error")


def _show_login_dialog(status, email):
    """
    :param status: was the verify email sent successfully
    :param email: the email sent the verify code to
    :return: either showing the verify code dialog or showing the error message
    """
    if status == "0":
        # show verify code dialog
        wx.CallAfter(pub.sendMessage, "showLoginDialog", email=email)
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Wrong username or password entered", title="Error")


def _handle_login(status):
    """
    :param status: was the login successful
    :return: either showing the files of the user or showing error message
    """
    if status == "0":
        wx.CallAfter(pub.sendMessage, "loginOk")
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Wrong verification code.", title="Error")


def _handle_delete_file(status):
    """
    :param status: was the file deleted successfully
    :return: tells graphic if to delete from the files of the user or to show error message
    """
    if status == "0":
        wx.CallAfter(pub.sendMessage, "deleteOk")
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Couldn't delete file.", title="Error")


def _handle_rename_file(status, new_name):
    """
    :param status: was the rename successful
    :param new_name: new name of the file
    :return: tells graphic if to rename the file from the files of the user or to show error message
    """
    if status == "0":
        wx.CallAfter(pub.sendMessage, "renameOk", new_name=new_name)
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Couldn't rename file.", title="Error")


def _handle_download_file(status, path, selected_path, data):
    """
    :param status: was the download successful
    :param path: path to download to
    :param selected_path: path of file in the server
    :param data: data of the file downloaded
    :return: downloads the file
    """
    file_name = path.split('/')[-1]

    if status == "0":
        try:
            # writing the file
            with open(selected_path, 'wb' if type(data) is bytes else 'w') as f:
                f.write(data)

            # showing successfully download message
            wx.CallAfter(pub.sendMessage, "showPopUp", text=f"Downloaded {file_name} to {selected_path} successfully.",
                         title="Success")

        except Exception as e:
            # showing error in download message
            wx.CallAfter(pub.sendMessage, "showPopUp", text="Download failed.", title="Error")
            print(str(e))

    else:
        # showing error in download message
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Download failed.", title="Error")


def _handle_open_file(file_comm, status, server_path, data):
    """
    :param file_comm: the file comm object
    :param status: was the download successful
    :param server_path: path of the file in the server
    :param data: data of the file
    :return: opens the file for edit
    """
    file_name = server_path.split('/')[-1]
    server_path = '/'.join(server_path.split('/')[:-1])

    if status == "0":
        # creating random name
        ascii_values = list(range(65, 91)) + list(range(97, 123)) + list(range(48, 58))

        cwd = os.getcwd().replace('\\', '/')
        while True:
            random_name = ''.join(chr(secrets.choice(ascii_values)) for _ in range(16))
            path = f"{cwd}/{random_name}"
            if not os.path.isdir(path):
                break

        try:
            # creating temp file
            os.mkdir(path)
            file_path = f"{path}/{file_name}"
            with open(file_path, 'wb' if type(data) is bytes else 'w') as f:
                f.write(data)

        except Exception as e:
            wx.CallAfter(pub.sendMessage, "showPopUp", text="Couldn't open file.", title="Error")
            print(str(e))
        else:
            change_flag = False
            monitor_q = queue.Queue()

            # has the file been closed yet
            is_alive_thread = threading.Thread(target=monitorFile.wait_until, args=(file_path, monitor_q))
            is_alive_thread.start()

            # were there any changes made to the file
            monitor_thread = threading.Thread(target=monitorFile.monitor, args=(path, monitor_q))
            monitor_thread.start()

            while True:
                data = monitor_q.get()
                # if closed the file
                if data == "Finished":
                    break
                # if made changed to the file
                elif data == "Changed":
                    change_flag = True

            # if any changes were made update the server to change the file
            if change_flag:
                file_comm.send_file(12, file_path, server_path)

            # deleting the temp file
            try:
                shutil.rmtree(path)
            except Exception as e:
                print(str(e))

    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Couldn't open file.", title="Error")


def _handle_upload_file(status, path):
    """
    :param status: was the upload successful
    :param path: path of the file uploaded
    :return: tells graphics to add the file to the user files or shows error message
    """
    if status == "0":
        wx.CallAfter(pub.sendMessage, "uploadOk", path=path)
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Couldn't upload file.", title="Error")


def _handle_create_dir(status):
    """
    :param status: was the creating of the directory successful
    :return: tells graphics to add the older to the user files or shows error message
    """
    if status == "0":
        wx.CallAfter(pub.sendMessage, "createOk")
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Couldn't create folder.", title="Error")


def _handle_share_file(status):
    """
    :param status: was the share successful
    :return: tells graphics to show wether the share was successful or not
    """
    if status == "0":
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Shared file successfully.", title="Success")
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="User doesn't exist.", title="Error")


def _handle_add_shared_file(path):
    """
    :param path: path of file shared
    :return: adding the file shared
    """
    wx.CallAfter(pub.sendMessage, "addFile", path=path)


def _handle_move_file(status, path):
    """
    :param status: was the move successful
    :param path: where to move the file to
    :return: tells graphics to move file in the user files or show error message
    """
    if status == "0":
        wx.CallAfter(pub.sendMessage, "moveFile", path=path)
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Couldn't move file.", title="Error")


def _handle_paste_file(status):
    """
    :param status: was the paste successful
    :return: tells graphics to update user files or show error message
    """
    if status == "0":
        wx.CallAfter(pub.sendMessage, "pasteFile")
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Couldn't paste file", title="Error")


def _handle_get_details(email, photo):
    """
    :param email: email of user
    :param photo: data of photo of user
    :return:
    """
    if email:
        wx.CallAfter(pub.sendMessage, "detailsOk", email=email, photo=photo)


def _handle_change_email(status, email):
    """
    :param status: was the email change successful
    :param email: email to change to
    :return: changes email in graphics or showing error message
    """
    if status == "0":
        wx.CallAfter(pub.sendMessage, "changeEmailOk", email=email)
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Couldn't change email, try again.", title="Error")


def _handle_change_password(status):
    """
    :param status: was the password change successful
    :return: show message whether the change was successful or not
    """
    if status == "0":
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Password changed successfully.", title="Success")
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Couldn't change password, try again.", title="Error")


def _handle_change_photo(data):
    """
    :param data: data of photo to change to
    :return: changing the photo data in the graphics or showing error message
    """
    if data:
        wx.CallAfter(pub.sendMessage, "changePhotoOk", data=data)
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Couldn't change photo, try again.", title="Error")


def _handle_username_check(status, email):
    """
    :param status: does the user exist
    :param email: email of user if he exists None if not
    :return: showing code verify dialog or showing error message
    """
    if status == "0":
        wx.CallAfter(pub.sendMessage, "forgotPassEmailOk", email=email)
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="User doesn't exist.", title="Error")


def _handle_code_check(status):
    """
    :param status: was the code entered correct
    :return: showing forgot password dialog or showing error message
    """
    if status == "0":
        wx.CallAfter(pub.sendMessage, "showForgotPassDialog")
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Wrong code entered.", title="Error")


def _handle_forgot_password(status):
    """
    :param status: was the password changed successfully
    :return: showing message whether it was successful or not
    """
    if status == "0":
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Password changed successfully.", title="Success")
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Couldn't change password.", title="Error")


def _handle_zip_file(status, zip_name):
    """
    :param status: was the zip file created successfully or not
    :param zip_name: the name of the zip file created
    :return: telling graphics to add the zip to the user files or show error message
    """
    if status == "0":
        wx.CallAfter(pub.sendMessage, "zipFileOk", path=zip_name)
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Couldn't zip file.", title="Error")


def _handle_send_files(branches):
    """
    :param branches: files of the user
    :return: updating the files of the user
    """
    wx.CallAfter(pub.sendMessage, "filesOk", branches=branches)


if __name__ == '__main__':
    main_loop()
