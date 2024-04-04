import wx
from pubsub import pub
from .loginPanel import LoginPanel
from .registerPanel import RegistrationPanel
from .filesPanel import FilesPanel
from settings import CurrentSettings as Settings


class MainFrame(wx.Frame):
    def __init__(self, comm, parent=None):
        """
        :param comm: client comm object
        :param parent: panel parent
        """
        super(MainFrame, self).__init__(parent, title="GolDrive")
        self.comm = comm
        self.Maximize()

        self.main_panel = MainPanel(self, self.comm)

        self.SetIcon(wx.Icon(f"{Settings.USER_FILES_PATH}/logo.ico"))

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.main_panel, 1, wx.EXPAND)
        # arrange the frame
        self.SetSizer(box)
        self.Layout()
        self.Show()


class MainPanel(wx.Panel):
    def __init__(self, parent, comm):
        """
        :param parent:
        :param comm:
        """
        wx.Panel.__init__(self, parent)
        self.frame = parent
        self.comm = comm
        self.files_comm = None
        self.username = None
        self.email = None
        self.profilePhoto = None

        v_box = wx.BoxSizer()
        # create object for each panel
        self.login = LoginPanel(self, self.frame, self.comm)
        self.register = RegistrationPanel(self, self.frame, self.comm)
        self.files = FilesPanel(self, self.frame, self.comm)

        v_box.Add(self.login)
        v_box.Add(self.register)
        v_box.Add(self.files)

        # The first panel to show
        self.login.Show()
        self.SetSizer(v_box)
        self.Layout()

        pub.subscribe(self.show_pop_up, "showPopUp")
        pub.subscribe(self._files_comm_update, "updateFileComm")

    def change_screen(self, cur_screen, screen):
        """
        :param cur_screen: screen showing panel object
        :param screen: screen to show panel object
        :return: changes screen
        """
        cur_screen.Hide()
        screen.Show()

        self.Layout()
        self.Refresh()
        self.Update()

    def show_pop_up(self, text, title):
        """
        :param text: text to show
        :param title: title of pop up
        :return: shows pop up message dialog
        """
        dlg = wx.MessageDialog(self, text, title, wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def _files_comm_update(self, file_comm):
        """
        :param file_comm: client file comm object
        :return:
        """
        self.files_comm = file_comm
