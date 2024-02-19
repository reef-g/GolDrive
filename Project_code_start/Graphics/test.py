import wx


class PasswordFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(PasswordFrame, self).__init__(*args, **kw)

        self.panel = wx.Panel(self)
        self.password_label = wx.StaticText(self.panel, label="Password:")
        self.password_textctrl = wx.TextCtrl(self.panel, style=wx.TE_PASSWORD)
        self.show_password_checkbox = wx.CheckBox(self.panel, label="Show Password")

        # Bind the event handler for checkbox
        self.show_password_checkbox.Bind(wx.EVT_CHECKBOX, self.on_checkbox_checked)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.password_label, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(self.password_textctrl, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(self.show_password_checkbox, 0, wx.ALL, 5)

        self.panel.SetSizerAndFit(sizer)
        self.Show()

    def on_checkbox_checked(self, event):
        show_password = self.show_password_checkbox.GetValue()

        # Get the current position and size of the existing text control
        position = self.password_textctrl.GetPosition()
        size = self.password_textctrl.GetSize()

        # Create a new text control with the updated style
        new_style = wx.TE_PASSWORD if not show_password else 0
        new_textctrl = wx.TextCtrl(self.panel, pos=position, size=size, style=new_style)

        # Copy the text from the existing text control to the new one
        new_textctrl.SetValue(self.password_textctrl.GetValue())

        # Replace the existing text control with the new one
        self.panel.GetSizer().Replace(self.password_textctrl, new_textctrl)
        self.password_textctrl.Destroy()

        # Update the reference to the new text control
        self.password_textctrl = new_textctrl


if __name__ == '__main__':
    app = wx.App(False)
    frame = PasswordFrame(None, title="Password Visibility Toggle", size=(300, 150))
    app.MainLoop()
