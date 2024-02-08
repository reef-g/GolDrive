import wx

class MySizer(wx.BoxSizer):
    def __init__(self, *args, **kwargs):
        super(MySizer, self).__init__(*args, **kwargs)

class MyPanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        super(MyPanel, self).__init__(parent, *args, **kwargs)

        self.SetDropTarget(MyDropTarget(self))
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)

        box_sizer = MySizer(wx.HORIZONTAL)
        box_sizer.Add(wx.Button(self, label="Button 1"), 1, wx.EXPAND)
        self.SetSizer(box_sizer)

    def OnLeftDown(self, event):
        # Handle left mouse button down event
        pass

class MyDropTarget(wx.DropTarget):
    def __init__(self, window):
        super(MyDropTarget, self).__init__()

        self.window = window
        self.data = wx.TextDataObject()

        self.SetDataObject(self.data)

    def OnData(self, x, y, result):
        if self.GetData():
            print("Item dropped successfully")
            return result
        return wx.DragNone

class MyFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(MyFrame, self).__init__(*args, **kw)

        panel = MyPanel(self)

if __name__ == "__main__":
    app = wx.App(False)
    frame = MyFrame(None, title="Drag and Drop Example", size=(400, 300))
    frame.Show()
    app.MainLoop()