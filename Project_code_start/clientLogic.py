import os.path
import queue
import clientComm
import clientProtocol
from settings import Settings
import threading
from Graphics import graphics
from pubsub import pub
import wx
import secrets
import shutil
import monitorFile


def main_loop():
    msg_q = queue.Queue()

    client_comm = clientComm.ClientComm(Settings.SERVERIP, Settings.SERVERPORT, msg_q, 4)
    threading.Thread(target=_handle_messages, args=(msg_q,)).start()

    app = graphics.wx.App()
    graphics.MyFrame(client_comm)

    app.MainLoop()


def _handle_messages(msg_q):
    recv_commands = {"01": _handle_registration, "02": _handle_login, "03": _handle_send_files,
                     "05": _handle_change_email, "06": _handle_change_password, "08": _handle_rename_file,
                     "09": _handle_share_file, "10": _handle_delete_file, "13": _handle_create_dir,
                     "14": _handle_add_shared_file, "16": _handle_files_port, "18": _handle_move_file,
                     "19": _handle_paste_file, "21": _handle_get_details}

    while True:
        data = msg_q.get()
        protocol_num, params = clientProtocol.unpack_message(data)
        if protocol_num == "03":
            # since * breaks the list down and we want the whole list
            _handle_send_files(params)
        else:
            recv_commands[protocol_num](*params)


def _handle_files_port(files_port):
    files_q = queue.Queue()
    files_comm = clientComm.ClientComm(Settings.SERVERIP, int(files_port), files_q, 10)
    threading.Thread(target=_handle_files, args=(files_comm, files_q,)).start()
    wx.CallAfter(pub.sendMessage, "updateFileComm", filecomm=files_comm)


def _handle_files(files_comm, files_q):
    recv_commands = {"11": _handle_download_file, "12": _handle_upload_file, "20": _handle_open_file}

    while True:
        data = files_q.get()
        if data[0] == "11" or data[0] == "20":
            protocol_num, *params = data
            params.insert(0, files_comm)
        else:
            protocol_num, params = clientProtocol.unpack_message(data)

        recv_commands[protocol_num](*params)


def _handle_registration(status):
    if status == "0":
        wx.CallAfter(pub.sendMessage, "registerOk")
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="User already exists.", title="Error")


def _handle_login(status):
    if status == "0":
        wx.CallAfter(pub.sendMessage, "loginOk")
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Wrong username or password entered.", title="Error")


def _handle_delete_file(status):
    if status == "0":
        wx.CallAfter(pub.sendMessage, "deleteOk")
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Couldn't delete file.", title="Error")


def _handle_rename_file(status, new_name):
    if status == "0":
        wx.CallAfter(pub.sendMessage, "renameOk", new_name=new_name)
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Couldn't rename file.", title="Error")


def _handle_download_file(file_comm, status, path, selected_path, data):
    file_name = path.split('/')[-1]

    if status == "0":
        try:
            with open(selected_path, 'wb' if type(data) == bytes else 'w') as f:
                f.write(data)

            wx.CallAfter(pub.sendMessage, "showPopUp", text=f"Downloaded {file_name} to {selected_path} successfully.",
                         title="Success")

        except Exception as e:
            wx.CallAfter(pub.sendMessage, "showPopUp", text="Download failed.", title="Error")
            print(str(e))

    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Download failed.", title="Error")


def _handle_open_file(file_comm, status, server_path, data):
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
            os.mkdir(path)
            file_path = f"{path}/{file_name}"
            with open(file_path, 'wb' if type(data) == bytes else 'w') as f:
                f.write(data)

        except Exception as e:
            wx.CallAfter(pub.sendMessage, "showPopUp", text="Couldn't open file.", title="Error")
            print(str(e))
        else:
            change_flag = False
            monitor_q = queue.Queue()

            is_alive_thread = threading.Thread(target=monitorFile.wait_until, args=(file_path, monitor_q))
            is_alive_thread.start()
            monitor_thread = threading.Thread(target=monitorFile.monitor, args=(path, monitor_q))
            monitor_thread.start()

            while True:
                data = monitor_q.get()
                if data == "Finished":
                    break
                elif data == "Changed":
                    change_flag = True

            if change_flag:
                file_comm.send_file(file_path, server_path)

            try:
                shutil.rmtree(path)
            except Exception as e:
                print(str(e))

    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Couldn't open file.", title="Error")


def _handle_upload_file(status, path):
    if status == "0":
        wx.CallAfter(pub.sendMessage, "uploadOk", path=path)
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Couldn't upload file.", title="Error")


def _handle_create_dir(status):
    if status == "0":
        wx.CallAfter(pub.sendMessage, "createOk")
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Couldn't create folder.", title="Error")


def _handle_share_file(status):
    if status == "0":
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Shared file successfully.", title="Success")
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="User doesn't exist.", title="Error")


def _handle_add_shared_file(path):
    wx.CallAfter(pub.sendMessage, "addFile", path=path)


def _handle_move_file(status, path):
    if status == "0":
        wx.CallAfter(pub.sendMessage, "moveFile", path=path)
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Couldn't move file.", title="Error")


def _handle_paste_file(status):
    if status == "0":
        wx.CallAfter(pub.sendMessage, "pasteFile")
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Couldn't paste file", title="Error")


def _handle_get_details(email):
    if email:
        wx.CallAfter(pub.sendMessage, "detailsOk", email=email)


def _handle_change_email(status, email):
    if status == "0":
        wx.CallAfter(pub.sendMessage, "changeEmailOk", email=email)
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Couldn't change email, try again.", title="Error")


def _handle_change_password(status):
    if status == "0":
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Password changed successfully.", title="Success")
    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Couldn't change password, try again.", title="Error")


def _handle_send_files(branches):
    wx.CallAfter(pub.sendMessage, "filesOk", branches=branches)


if __name__ == '__main__':
    main_loop()
