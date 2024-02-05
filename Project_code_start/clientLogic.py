import queue
import clientComm
import clientProtocol
import Settings
import threading
from Graphics import graphics
from pubsub import pub
import wx


def main_loop():

    msg_q = queue.Queue()

    client_comm = clientComm.ClientComm(Settings.SERVERIP, Settings.SERVERPORT, msg_q, 4)
    threading.Thread(target=_handle_messages, args=(msg_q,)).start()

    app = graphics.wx.App()
    graphics.MyFrame(client_comm)

    app.MainLoop()


def _handle_messages(msg_q):
    recv_commands = {"01": _handle_registration, "02": _handle_login, "03": _handle_send_files,
                     "08": _handle_rename_file, "09": _handle_share_file, "10": _handle_delete_file,
                     "13": _handle_create_dir, "16": _handle_files_port}

    while True:
        data = msg_q.get()
        protocol_num, params = clientProtocol.unpack_message(data)
        # since * breaks the list down and we want the whole list
        if protocol_num == "03":
            _handle_send_files(params)
        else:
            recv_commands[protocol_num](*params)


def _handle_files_port(files_port):
    files_q = queue.Queue()
    files_comm = clientComm.ClientComm(Settings.SERVERIP, int(files_port), files_q, 6)
    threading.Thread(target=_handle_files, args=(files_q,)).start()
    wx.CallAfter(pub.sendMessage, "update_file_comm", filecomm=files_comm)

    # app.filesSocket = files_socket


def _handle_files(files_q):
    recv_commands = {"11": _handle_download_file, "12": _handle_upload_file}

    while True:
        data = files_q.get()
        if data[0] == "11":
            protocol_num, *params = data
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


def _handle_download_file(status, path, selected_path, data):
    file_name = path.split('/')[-1]
    if status == "0":
        try:
            with open(selected_path, 'wb' if type(data) == bytes else 'w') as f:
                f.write(data)

            wx.CallAfter(pub.sendMessage, "showPopUp", text=f"Downloaded {file_name} to {selected_path} successfully.", title="Success")

        except Exception as e:
            wx.CallAfter(pub.sendMessage, "showPopUp", text="Download failed.", title="Error")
            print(str(e))

    else:
        wx.CallAfter(pub.sendMessage, "showPopUp", text="Download failed.", title="Error")


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


def _handle_send_files(branches):
    wx.CallAfter(pub.sendMessage, "filesOk", branches=branches)


if __name__ == '__main__':
    main_loop()
