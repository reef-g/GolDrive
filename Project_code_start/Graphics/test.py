import wx

class MyFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(MyFrame, self).__init__(*args, **kw)

        # Create a panel
        panel = wx.Panel(self)

        # Create a box sizer
        boxSizer = wx.BoxSizer(wx.HORIZONTAL)

        # Add a static text on the left
        left_text = wx.StaticText(panel, label="Left Text")
        boxSizer.Add(left_text, 0, wx.ALL, 5)

        # Add a static text on the right aligned to the right
        right_text = wx.StaticText(panel, label="Right Text", style=wx.ALIGN_RIGHT)
        boxSizer.Add(right_text, 1, wx.ALL | wx.EXPAND, 5)

        # Set the sizer for the panel
        panel.SetSizer(boxSizer)

        # Set the frame size and center it
        self.SetSize((300, 100))
        self.Centre()

if __name__ == "__main__":
    app = wx.App(False)
    frame = MyFrame(None, title="Static Text Example")
    frame.Show()
    app.MainLoop()
