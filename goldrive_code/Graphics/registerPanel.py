import wx
from pubsub import pub
from ClientFiles import clientProtocol
from .customMenusAndDialogs import ConfirmMailDialog, TransparentText
from settings import CurrentSettings as Settings


class RegistrationPanel(wx.Panel):
    def __init__(self, parent, frame, comm):
        wx.Panel.__init__(self, parent, pos=wx.DefaultPosition, size=(1920, 1080), style=wx.SIMPLE_BORDER)
        self.frame = frame
        self.comm = comm
        self.parent = parent

        self.username = None
        self.password = None
        self.email = None

        title_font = wx.Font(68, wx.DECORATIVE, wx.NORMAL, wx.NORMAL, False, "High Tower Text")
        text_font = wx.Font(30, wx.DECORATIVE, wx.NORMAL, wx.NORMAL, False)
        self.entry_font = wx.Font(20, wx.DECORATIVE, wx.NORMAL, wx.NORMAL, False)
        button_font = wx.Font(15, wx.DEFAULT, wx.NORMAL, wx.BOLD)

        hidden_path = f"{Settings.USER_FILES_PATH}\\hidden-eye.png"
        open_path = f"{Settings.USER_FILES_PATH}\\open-eye.png"

        self.is_showing_password = False
        self.hidden_bitmap = wx.Bitmap(hidden_path, wx.BITMAP_TYPE_ANY)
        self.shown_bitmap = wx.Bitmap(open_path, wx.BITMAP_TYPE_ANY)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        entries = wx.BoxSizer(wx.VERTICAL)

        self.sizer.AddSpacer(235)
        title = TransparentText(self, -1, label="REGISTER", style=wx.TRANSPARENT_WINDOW)
        title.SetForegroundColour(wx.BLACK)
        title.SetFont(title_font)

        name_sizer = wx.BoxSizer(wx.VERTICAL)
        name_text = TransparentText(self, 1, label="Username: ", style=wx.TRANSPARENT_WINDOW)
        name_text.SetFont(text_font)
        self.nameField = wx.TextCtrl(self, -1, name="username", size=(650, 40))
        self.nameField.SetFont(self.entry_font)

        name_sizer.Add(name_text, 0, wx.Center, 5)
        name_sizer.Add(self.nameField)
        name_sizer.AddSpacer(15)

        self.pass_sizer = wx.BoxSizer(wx.HORIZONTAL)
        pass_text = TransparentText(self, 1, label="Password: ", style=wx.TRANSPARENT_WINDOW)
        pass_text.SetFont(text_font)
        self.passField = wx.TextCtrl(self, -1, name="password", size=(650, 40),
                                     style=wx.TE_PASSWORD | wx.TE_PROCESS_ENTER)
        self.passField.SetFont(self.entry_font)

        name_sizer.Add(pass_text)
        self.pass_sizer.AddSpacer(27)
        self.pass_sizer.Add(self.passField)
        self.eye_bitmap = wx.StaticBitmap(self, wx.ID_ANY, self.hidden_bitmap)
        self.eye_bitmap.Bind(wx.EVT_LEFT_DOWN, self.change_visibility)
        self.pass_sizer.Add(self.eye_bitmap)

        email_sizer = wx.BoxSizer(wx.VERTICAL)
        email_text = TransparentText(self, 1, label="Email: ", style=wx.TRANSPARENT_WINDOW)
        email_text.SetFont(text_font)
        self.emailField = wx.TextCtrl(self, -1, name="email", size=(650, 40))
        self.emailField.SetFont(self.entry_font)

        email_sizer.Add(email_text, 0, wx.Center, 5)
        email_sizer.Add(self.emailField)
        email_sizer.AddSpacer(15)

        entries.Add(name_sizer, 0, wx.CENTER, 5)
        entries.Add(self.pass_sizer, 0, wx.CENTER, 5)
        entries.Add(email_sizer, 0, wx.CENTER, 10)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        login_button = wx.Button(self, label="BACK TO LOGIN")
        login_button.Bind(wx.EVT_BUTTON, self.login_control)
        login_button.SetFont(button_font)

        register_button = wx.Button(self, label="REGISTER")
        register_button.Bind(wx.EVT_BUTTON, self.on_register)
        register_button.SetFont(button_font)

        # self.SetTabOrder([self.nameField, self.passField, login_button, register_button])

        button_sizer.Add(register_button, 0, wx.CENTER, 10)
        button_sizer.AddSpacer(80)
        button_sizer.Add(login_button, 0, wx.CENTER, 10)

        self.sizer.AddMany([(title, 0, wx.CENTER, 10),
                            (entries, 0, wx.CENTER, 5)])

        self.sizer.AddSpacer(20)
        self.sizer.Add(button_sizer, 0, wx.CENTER, 5)

        pub.subscribe(self.register_ok, "showRegisterDialog")
        pub.subscribe(self.verify_ok, "registerOk")

        self.Bind(wx.EVT_PAINT, self.PaintBackgroundImage)

        self.SetSizer(self.sizer)
        self.Layout()

        self.Hide()

    def PaintBackgroundImage(self, evt):
        dc = wx.PaintDC(self)

        bmp = wx.Bitmap(rf"{Settings.USER_FILES_PATH}\bg.png")
        dc.DrawBitmap(bmp, 0, 0)

    def change_visibility(self, event):
        open_or_closed = self.hidden_bitmap if not self.is_showing_password else self.shown_bitmap

        position = self.passField.GetPosition()
        size = self.passField.GetSize()

        # Create a new text control with the updated style
        new_style = wx.TE_PASSWORD if not self.is_showing_password else wx.TE_PROCESS_ENTER
        new_textctrl = wx.TextCtrl(self, pos=position, size=size, style=new_style)
        new_textctrl.SetFont(self.entry_font)

        # Copy the text from the existing text control to the new one
        new_textctrl.SetValue(self.passField.GetValue())

        self.eye_bitmap.SetBitmap(open_or_closed)
        self.pass_sizer.Replace(self.passField, new_textctrl)
        self.passField.Destroy()
        self.passField = new_textctrl

        self.is_showing_password = not self.is_showing_password

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

    def register_ok(self, username, password, email):
        self.username = username
        self.password = password
        self.email = email

        con = ConfirmMailDialog(self, "Verify")
        result = con.ShowModal()

        if result == wx.ID_OK:
            values = con.GetValues()

            msg = clientProtocol.pack_verify_register_email_request(username, password, email, *values)
            self.comm.send(msg)

    def verify_ok(self):
        self.parent.show_pop_up("User created successfully.", "Success")
        self.parent.change_screen(self, self.parent.login)
