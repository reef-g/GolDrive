import wx


class CircularBitmapButton(wx.Panel):
    def __init__(self, parent, bitmap, size=(50, 50)):
        super(CircularBitmapButton, self).__init__(parent, size=size)
        self.SetBackgroundColour(wx.WHITE)  # Set background color to white

        # Load bitmap
        self.bitmap = wx.Bitmap(bitmap)

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_button_click)

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        dc.Clear()
        dc.DrawBitmap(self.bitmap, 0, 0, True)

        # Get the circular region
        region = wx.Region(self.GetSize(), self.GetSize())
        region.Offset(self.GetPosition())
        dc.SetClippingRegionAsRegion(region)

    def on_button_click(self, event):
        print("Button Clicked!")


class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        super(MyFrame, self).__init__(parent, title=title, size=(300, 200))

        panel = wx.Panel(self)

        # Load a circular image (replace 'your_circular_image.png' with your image file)
        circular_image_path = r"C:\Users\reefg\OneDrive\Desktop\test.png"

        circular_button = CircularBitmapButton(panel, bitmap=circular_image_path, size=(60, 60))

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(circular_button, 0, wx.ALL, 10)
        panel.SetSizerAndFit(sizer)

        self.Centre()
        self.Show(True)


app = wx.App(False)
frame = MyFrame(None, "Circular BitmapButton Example")
app.MainLoop()

