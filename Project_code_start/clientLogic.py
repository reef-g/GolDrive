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
    recv_commands = {"01": _handle_registration, "02": _handle_login, "08": _handle_rename_file,
                     "10": _handle_delete_file, "11": _handle_download_file, "13": _handle_send_files}
    client_socket = clientComm.ClientComm(Settings.SERVERIP, Settings.SERVERPORT, msg_q, 4)

    app = graphics.wx.App()
    graphics.MyFrame(client_socket)

    threading.Thread(target=_handle_messages, args=(msg_q, recv_commands,)).start()

    app.MainLoop()


def _handle_messages(msg_q, recv_commands):
    while True:
        data = msg_q.get()
        protocol_num, params = clientProtocol.unpack_message(data)
        print(protocol_num)
        if protocol_num == "13":
            if params:
                branches = params
                _handle_send_files(branches)
            else:
                _handle_send_files([])

        else:
            print(params)
            recv_commands[protocol_num](*params)


def _handle_registration(status):
    if status == "0":
        wx.CallAfter(pub.sendMessage, "registerOk")
    else:
        wx.CallAfter(pub.sendMessage, "registerNotOk")


def _handle_login(status):
    if status == "0":
        wx.CallAfter(pub.sendMessage, "loginOk")

    else:
        wx.CallAfter(pub.sendMessage, "loginNotOk")


def _handle_delete_file(status):
    if status == "0":
        wx.CallAfter(pub.sendMessage, "deleteOk")


def _handle_rename_file(status, new_name):
    if status == "0":
        wx.CallAfter(pub.sendMessage, "renameOk", new_name=new_name)


def _handle_download_file(status, data):
    if status == "0":
        wx.CallAfter(pub.sendMessage, "downloadOk", data=data)


def _handle_send_files(branches):
    wx.CallAfter(pub.sendMessage, "filesOk", branches=branches)


if __name__ == '__main__':
    main_loop()
