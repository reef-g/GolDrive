import wx
from pubsub import pub
from ClientFiles import clientProtocol


class RegistrationPanel(wx.Panel):
    def __init__(self, parent, frame, comm):
        wx.Panel.__init__(self, parent, pos=wx.DefaultPosition, size=(1920, 1080), style=wx.SIMPLE_BORDER)
        self.frame = frame
        self.comm = comm
        self.parent = parent
        self.SetBackgroundColour(wx.LIGHT_GREY)

        title = wx.StaticText(self, -1, label="Register panel", pos=(0, 0))
        titlefont = wx.Font(22, wx.DECORATIVE, wx.NORMAL, wx.NORMAL)
        title.SetForegroundColour(wx.BLACK)
        title.SetFont(titlefont)

        login_button = wx.Button(self, label="BACK TO LOGIN", pos=(10, 190))
        self.Bind(wx.EVT_BUTTON, self.login_control, login_button)

        name_text = wx.StaticText(self, 1, label="UserName: ", pos=(10, 40))
        self.nameField = wx.TextCtrl(self, -1, name="username", pos=(10, 60), size=(150, -1))

        pass_text = wx.StaticText(self, 1, pos=(10, 90), label="Password: ")
        self.passField = wx.TextCtrl(self, -1, name="password", pos=(10, 110), size=(150, -1), style=wx.TE_PASSWORD)

        email_text = wx.StaticText(self, 1, pos=(10, 140), label="Email: ")
        self.emailField = wx.TextCtrl(self, -1, name="email", pos=(10, 160), size=(150, -1))

        pub.subscribe(self.register_ok, "registerOk")

        register_button = wx.Button(self, label="REGISTER", pos=(120, 190))
        self.Bind(wx.EVT_BUTTON, self.on_register, register_button)

        self.Hide()

    def login_control(self, event):
        self.parent.change_screen(self, self.parent.login)

    def on_register(self, event):
        username_input = self.nameField.GetValue()
        password_input = self.passField.GetValue()
        email_input = self.emailField.GetValue()

        self.nameField.SetValue("")
        self.passField.SetValue("")
        self.emailField.SetValue("")

        msg2send = clientProtocol.pack_register_request(username_input, password_input, email_input)
        self.comm.send(msg2send)

    def register_ok(self):
        self.parent.change_screen(self, self.parent.login)
        self.parent.show_pop_up("User created successfully.", "Message")