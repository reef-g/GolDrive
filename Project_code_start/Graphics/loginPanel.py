import wx
from pubsub import pub
from settings import CurrentSettings as Settings
from ClientFiles import clientProtocol
from .customMenusAndDialogs import ConfirmMailDialog, ForgotPasswordDialog


class LoginPanel(wx.Panel):
    def __init__(self, parent, frame, comm):
        wx.Panel.__init__(self, parent, pos=wx.DefaultPosition, size=(1920, 1080), style=wx.SIMPLE_BORDER)
        self.frame = frame
        self.comm = comm
        self.parent = parent
        self.SetBackgroundColour(wx.LIGHT_GREY)

        self.username_input = None

        title_font = wx.Font(65, wx.DECORATIVE, wx.NORMAL, wx.NORMAL, False, "High Tower Text")
        text_font = wx.Font(30, wx.DECORATIVE, wx.NORMAL, wx.NORMAL, False)
        forgot_password_font = wx.Font(15, wx.DECORATIVE, wx.NORMAL, wx.NORMAL, False)
        self.entry_font = wx.Font(20, wx.DECORATIVE, wx.NORMAL, wx.NORMAL, False)

        hidden_path = f"{Settings.USER_IMAGES_PATH}\\hidden-eye.png"
        open_path = f"{Settings.USER_IMAGES_PATH}\\open-eye.png"

        self.is_showing_password = False
        self.hidden_bitmap = wx.Bitmap(hidden_path, wx.BITMAP_TYPE_ANY)
        self.shown_bitmap = wx.Bitmap(open_path, wx.BITMAP_TYPE_ANY)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        entries = wx.BoxSizer(wx.VERTICAL)
        forgot_password_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.sizer.AddSpacer(290)
        title = wx.StaticText(self, -1, label="LOG IN")
        title.SetForegroundColour(wx.BLACK)
        title.SetFont(title_font)

        name_sizer = wx.BoxSizer(wx.VERTICAL)
        name_text = wx.StaticText(self, 1, label="Username: ")
        name_text.SetFont(text_font)
        self.nameField = wx.TextCtrl(self, -1, name="username", size=(650, 40))
        self.nameField.SetFont(self.entry_font)

        name_sizer.Add(name_text, 0, wx.Center, 5)
        name_sizer.Add(self.nameField)
        name_sizer.AddSpacer(15)

        self.pass_sizer = wx.BoxSizer(wx.HORIZONTAL)
        pass_text = wx.StaticText(self, 1, label="Password: ")
        pass_text.SetFont(text_font)
        self.passField = wx.TextCtrl(self, -1, name="password", size=(650, 40), style=wx.TE_PASSWORD)
        self.passField.SetFont(self.entry_font)

        name_sizer.Add(pass_text)
        self.pass_sizer.AddSpacer(27)
        self.pass_sizer.Add(self.passField)
        self.eye_bitmap = wx.StaticBitmap(self, wx.ID_ANY, self.hidden_bitmap)
        self.eye_bitmap.Bind(wx.EVT_LEFT_DOWN, self.change_visibility)
        self.pass_sizer.Add(self.eye_bitmap)

        entries.Add(name_sizer, 0, wx.CENTER, 5)
        entries.Add(self.pass_sizer, 0, wx.CENTER, 10)

        forgot_password_sizer.AddSpacer(28)
        self.forgot_password = wx.StaticText(self, -1, "Forgot password")
        self.forgot_password.SetFont(forgot_password_font)
        self.forgot_password.SetForegroundColour("#87A7AF")
        self.forgot_password.Bind(wx.EVT_LEFT_DOWN, self._get_user_forgot_password)
        forgot_password_sizer.Add(self.forgot_password)
        entries.Add(forgot_password_sizer)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(self, label="LOG IN", size=(90, 40))
        self.Bind(wx.EVT_BUTTON, self.on_ok, ok_button)

        register_button = wx.Button(self, label="REGISTER", size=(90, 40))
        self.Bind(wx.EVT_BUTTON, self.register_control, register_button)

        button_sizer.Add(ok_button, 0, wx.CENTER, 10)
        button_sizer.AddSpacer(80)
        button_sizer.Add(register_button, 0, wx.CENTER, 10)

        self.sizer.AddMany([(title, 0, wx.CENTER, 10),
                            (entries, 0, wx.CENTER, 5)])

        self.sizer.AddSpacer(20)
        self.sizer.Add(button_sizer, 0, wx.CENTER, 5)

        pub.subscribe(self.login_ok, "showLoginDialog")
        pub.subscribe(self.verify_ok, "loginOk")
        pub.subscribe(self._get_details, "detailsOk")
        pub.subscribe(self._email_ok, "forgotPassEmailOk")
        pub.subscribe(self._send_forgot_password_request, "showForgotPassDialog")

        self.SetSizer(self.sizer)
        self.Layout()

        self.Hide()

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

    def register_control(self, event):
        self.parent.change_screen(self, self.parent.register)

    def login_ok(self, email):
        con = ConfirmMailDialog(self, "Verify")
        result = con.ShowModal()

        if result == wx.ID_OK:
            values = con.GetValues()

            msg = clientProtocol.pack_verify_login_email_request(email, *values, self.parent.username)
            self.comm.send(msg)

    def verify_ok(self):
        self.parent.username = self.username_input
        self.parent.files.title.SetLabel(self.parent.username.upper())
        
        msg = clientProtocol.pack_get_details_request(self.parent.username)
        self.parent.files_comm.send(msg)

        self.parent.change_screen(self, self.parent.files)

    def on_ok(self, event):
        self.username_input = self.nameField.GetValue()
        password_input = self.passField.GetValue()

        self.nameField.SetValue("")
        self.passField.SetValue("")

        if not 0 < len(self.username_input) <= 10 or not 0 < len(self.username_input) <= 10:
            self.parent.show_pop_up("Please enter a valid username and password.", "Error")
        else:
            self.parent.username = self.username_input
            msg2send = clientProtocol.pack_login_request(self.username_input, password_input)
            self.comm.send(msg2send)

    def _get_details(self, email, photo):
        self.parent.email = email
        self.parent.profilePhoto = photo
        wx.CallAfter(pub.sendMessage, "changeSettingsToPhoto")

        self.parent.change_screen(self, self.parent.files)

    def _get_user_forgot_password(self, event):
        dlg = wx.TextEntryDialog(self, f'Enter username of user:', 'Verify', '')
        result = dlg.ShowModal()
        dlg.Destroy()

        self.entered_name = dlg.GetValue()

        if result == wx.ID_OK:
            username = dlg.GetValue()

            msg = clientProtocol.pack_send_email_request(username)
            self.comm.send(msg)

    def _email_ok(self, email):
        code_dlg = wx.TextEntryDialog(self, "Enter the 6-digit code sent to your mail:", "Verify", "")
        result = code_dlg.ShowModal()
        code_dlg.Destroy()

        if result == wx.ID_OK:
            code = code_dlg.GetValue()

            msg = clientProtocol.pack_check_code_request(email, code)
            self.comm.send(msg)

    def _send_forgot_password_request(self):
        dlg = ForgotPasswordDialog(self, "Enter new password")
        result = dlg.ShowModal()

        if result == wx.ID_OK:
            values = dlg.GetValues()

            msg = clientProtocol.pack_forgot_password_request(self.entered_name, *values)
            self.comm.send(msg)

        dlg.Destroy()
