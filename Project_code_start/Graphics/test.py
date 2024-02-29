import wx


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        super(MyFrame, self).__init__(*args, **kwds)

        panel = wx.Panel(self)

        # Load a sample bitmap for the button (replace with your own)
        bitmap = wx.Bitmap(r"D:\!ReefGold\Project_code_start\UserGraphics\Shared.png", wx.BITMAP_TYPE_PNG)

        # Create a BitmapButton with the loaded bitmap
        bitmap_button = wx.BitmapButton(panel, wx.ID_ANY, bitmap, style=wx.NO_BORDER)

        # Set the tooltip for the BitmapButton
        tooltip = wx.ToolTip("This is a BitmapButton")
        bitmap_button.SetToolTip(tooltip)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(bitmap_button, 0, wx.ALL, 10)

        panel.SetSizer(sizer)


if __name__ == "__main__":
    app = wx.App(False)
    frame = MyFrame(None, wx.ID_ANY, "wxPython BitmapButton Example", size=(300, 150))
    frame.Show()
    app.MainLoop()
