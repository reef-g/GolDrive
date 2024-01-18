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
    recv_commands = {"01": _handle_registration, "02": _handle_login, "13": _handle_files_list}
    client_socket = clientComm.ClientComm(Settings.SERVERIP, Settings.SERVERPORT, msg_q, 2)

    app = graphics.wx.App()
    graphics.MyFrame(client_socket)

    threading.Thread(target=_handle_messages, args=(msg_q, recv_commands, )).start()

    app.MainLoop()


def _handle_messages(msg_q, recv_commands):
    while True:
        data = msg_q.get()
        protocol_num, params = clientProtocol.unpack_message(data)
        if protocol_num == "13" and params == []:
            print("You currently have no files.")
        else:
            recv_commands[protocol_num](*params)


def _handle_registration(status):
    if status == "0":
        wx.CallAfter(pub.sendMessage, "registerOk")
    else:
        print(status)
        wx.CallAfter(pub.sendMessage, "registerNotOk")


def _handle_login(status):
    if status == "0":
        print("Logged in")
        wx.CallAfter(pub.sendMessage, "loginOk")

    else:
        wx.CallAfter(pub.sendMessage, "loginNotOk")


def _handle_files_list(branches):
    print(branches)


if __name__ == '__main__':
    main_loop()
