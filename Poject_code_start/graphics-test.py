import wx

class LoginWindow(wx.Frame):
    def __init__(self, frame, title):
        self.frame = frame
        super(LoginWindow, self).__init__(parent, title=title, size=(1920, 1080))

        # self.png = wx.StaticBitmap(self, -1, wx.Bitmap(r"C:\Users\talmid\Pictures\login.png", wx.BITMAP_TYPE_ANY))
        # self.png.Show(False)
        panel = wx.Panel(self)

        # Static text to display instructions
        username_text = wx.StaticText(panel, label="Enter Username:", pos=(10, 10))
        # Text entry control
        self.login_ctrl = wx.TextCtrl(panel, pos=(10, 30), size=(200, -1))

        username_text = wx.StaticText(panel, label="Enter Password:", pos=(10, 60))
        # Text entry control
        self.password_ctrl = wx.TextCtrl(panel, pos=(10, 80), size=(200, -1), style=wx.TE_PASSWORD)

        # OK and Cancel buttons
        ok_button = wx.Button(panel, label="OK", pos=(10, 120))
        cancel_button = wx.Button(panel, label="Cancel", pos=(120, 120))

        self.Bind(wx.EVT_BUTTON, self.on_ok, ok_button)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, cancel_button)

        self.Show()

    def on_ok(self, event):
        username_input = self.login_ctrl.GetValue()
        password_input = self.password_ctrl.GetValue()

        print(f"Username is: {username_input}")
        print(f"Password is: {password_input}")

        self.login_ctrl.SetValue("")
        self.password_ctrl.SetValue("")

    def on_cancel(self, event):
        self.Close()

if __name__ == "__main__":
    app = wx.App(False)
    frame = LoginWindow(None, "Input Window Example")
    app.MainLoop()