import wx
import clientProtocol
from pubsub import pub

class MyFrame(wx.Frame):
    def __init__(self, comm, parent=None):
        super(MyFrame, self).__init__(parent, title="GolDrive")
        self.comm = comm
        self.Maximize()

        # create status bar
        self.CreateStatusBar(1)
        self.SetStatusText("GolDrive by Reef Gold - 2024")
        # create main panel - to put on the others panels
        self.main_panel = MainPanel(self, self.comm)
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.main_panel, 1, wx.EXPAND)
        # arrange the frame
        self.SetSizer(box)
        self.Layout()
        self.Show()


class MainPanel(wx.Panel):
    def __init__(self, parent, comm):
        wx.Panel.__init__(self, parent)
        self.frame = parent
        self.comm = comm
        self.SetBackgroundColour(wx.LIGHT_GREY)
        v_box = wx.BoxSizer()
        # create object for each panel
        self.login = LoginPanel(self, self.frame, self.comm)
        # self.registration = RegistrationPanel(self, self.frame)
        self.files = FilesPanel(self, self.frame, self.comm)

        v_box.Add(self.login)
        # v_box.Add(self.registration)
        v_box.Add(self.files)
        # The first panel to show
        self.login.Show()
        self.SetSizer(v_box)
        self.Layout()

    def change_screen(self, curScreen, screen):
        curScreen.Hide()
        screen.Show()

        self.Layout()
        self.Refresh()
        self.Update()


class LoginPanel(wx.Panel):
    def __init__(self, parent, frame, comm):
        wx.Panel.__init__(self, parent, pos=wx.DefaultPosition, size=(1920, 1080), style=wx.SIMPLE_BORDER)
        self.frame = frame
        self.comm = comm
        self.parent = parent
        self.SetBackgroundColour(wx.LIGHT_GREY)

        title = wx.StaticText(self, -1, label="LOG IN", pos=(0, 0))
        font = wx.Font(25, wx.DECORATIVE, wx.NORMAL, wx.NORMAL, False, "High Tower Text")
        title.SetForegroundColour(wx.BLACK)
        title.SetFont(font)

        nameBox = wx.BoxSizer(wx.HORIZONTAL)

        nameText = wx.StaticText(self, 1, label="UserName: ", pos=(10, 40))

        self.nameField = wx.TextCtrl(self, -1, name="username", pos=(10, 60), size=(150, -1))
        nameBox.Add(nameText, 0, wx.ALL, 5)
        nameBox.Add(self.nameField, 0, wx.ALL, 5)

        passBox = wx.BoxSizer(wx.HORIZONTAL)

        passText = wx.StaticText(self, 1, pos=(10, 90), label="Password: ")

        self.passField = wx.TextCtrl(self, -1, name="password", pos=(10, 110), size=(150, -1), style=wx.TE_PASSWORD)
        passBox.Add(passText, 0, wx.ALL, 5)
        passBox.Add(self.passField, 0, wx.ALL, 5)

        pub.subscribe("loginOk", self.login_ok)
        pub.subscribe("loginNotOk", self.login_notOk)

        ok_button = wx.Button(self, label="OK", pos=(30, 140))
        self.Bind(wx.EVT_BUTTON, self.on_ok, ok_button)


    def login_ok(self):
        self.parent.change_screen(self, self.parent.files)

    def login_notOk(self):
        self.show_pop_up("Wrong username or password entered.", "Error")

    def on_ok(self, event):
        username_input = self.nameField.GetValue()
        password_input = self.passField.GetValue()

        self.nameField.SetValue("")
        self.passField.SetValue("")

        if not 0 < len(username_input) <= 10 or not 0 < len(username_input) <= 10:
            self.show_pop_up("Please enter a valid username and password.", "Error")
        else:
            msg2send = clientProtocol.pack_login_request(username_input, password_input)
            self.comm.send(msg2send)

    def show_pop_up(self, text, title):
        dlg = wx.MessageDialog(self, text, title, wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()


class FilesPanel(wx.Panel):
    def __init__(self, parent, frame, comm):
        wx.Panel.__init__(self, parent, pos=wx.DefaultPosition, size=(1920, 1080), style=wx.SIMPLE_BORDER)
        self.frame = frame
        self.comm = comm
        self.parent = parent
        self.SetBackgroundColour(wx.LIGHT_GREY)

        title = wx.StaticText(self, -1, label="Files panel", pos=(0, 0))
        titlefont = wx.Font(22, wx.DECORATIVE, wx.NORMAL, wx.NORMAL)
        title.SetForegroundColour(wx.BLACK)
        title.SetFont(titlefont)

        ok_button = wx.Button(self, label="BACK TO LOGIN", pos=(30, 140))
        self.Bind(wx.EVT_BUTTON, self.login_control, ok_button)

    def login_control(self, event):
        self.parent.change_screen(self, self.parent.login)


if __name__ == '__main__':
    app = wx.App()
    frame = MyFrame()
    app.MainLoop()
