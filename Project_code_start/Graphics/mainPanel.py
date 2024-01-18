import wx
from Graphics import LoginPanel, RegistrationPanel, FilesPanel


class MyFrame(wx.Frame):
    def __init__(self, comm, parent=None):
        super(MyFrame, self).__init__(parent, title="GolDrive")
        self.comm = comm
        self.Maximize()

        # create status bar
        self.CreateStatusBar(1)
        self.SetStatusText("GolDrive by Reef Gold - 2024")
        # create main panel - to put on the others panels
        self.main_panel = MainPanel(self, self.comm)
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.main_panel, 1, wx.EXPAND)
        # arrange the frame
        self.SetSizer(box)
        self.Layout()
        self.Show()


class MainPanel(wx.Panel):
    def __init__(self, parent, comm):
        wx.Panel.__init__(self, parent)
        self.frame = parent
        self.comm = comm
        self.SetBackgroundColour(wx.LIGHT_GREY)
        v_box = wx.BoxSizer()
        # create object for each panel
        self.login = LoginPanel(self, self.frame, self.comm)
        self.register = RegistrationPanel(self, self.frame, comm)
        self.files = FilesPanel(self, self.frame, self.comm)

        v_box.Add(self.login)
        v_box.Add(self.register)
        v_box.Add(self.files)
        # The first panel to show
        self.login.Show()
        self.SetSizer(v_box)
        self.Layout()

    def change_screen(self, curScreen, screen):
        curScreen.Hide()
        screen.Show()

        self.Layout()
        self.Refresh()
        self.Update()

    def show_pop_up(self, text, title):
        dlg = wx.MessageDialog(self, text, title, wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

