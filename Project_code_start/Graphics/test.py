import wx


class Example(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(Example, self).__init__(*args, **kwargs)

        self.InitUI()

    def InitUI(self):
        panel = wx.Panel(self)
        button = wx.Button(panel, label='Get User Input', pos=(10, 10))
        self.Bind(wx.EVT_BUTTON, self.OnGetUserInput, button)

        self.SetSize((300, 200))
        self.SetTitle('Text Entry Dialog Example')
        self.Centre()

    def OnGetUserInput(self, event):
        dlg = wx.TextEntryDialog(self, 'Enter your input:', 'Input Dialog', wx.YES_NP)
        result = dlg.ShowModal()

        if result == wx.ID_OK:
            user_input = dlg.GetValue()
            print(f"User entered: {user_input}")
            # Perform actions with the user input as needed

        dlg.Destroy()


def main():
    app = wx.App()
    ex = Example(None)
    ex.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()