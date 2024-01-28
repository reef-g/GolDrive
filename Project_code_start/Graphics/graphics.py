import wx
import wx.lib.scrolledpanel
from pubsub import pub
import clientProtocol


class MyFrame(wx.Frame):
    def __init__(self, comm, parent=None):
        super(MyFrame, self).__init__(parent, title="GolDrive")
        self.comm = comm
        self.Maximize()

        # create status bar
        # self.CreateStatusBar(1)
        # self.SetStatusText("GolDrive by Reef Gold - 2024")
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
        self.username = ""
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

    def change_screen(self, cur_screen, screen):
        cur_screen.Hide()
        screen.Show()

        self.Layout()
        self.Refresh()
        self.Update()

    def show_pop_up(self, text, title):
        dlg = wx.MessageDialog(self, text, title, wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()


class LoginPanel(wx.Panel):
    def __init__(self, parent, frame, comm):
        wx.Panel.__init__(self, parent, pos=wx.DefaultPosition, size=(1920, 1080), style=wx.SIMPLE_BORDER)
        self.frame = frame
        self.comm = comm
        self.parent = parent
        self.SetBackgroundColour(wx.LIGHT_GREY)

        title = wx.StaticText(self, -1, label="LOG IN", pos=(0, 0))
        font = wx.Font(25, wx.DECORATIVE, wx.NORMAL, wx.NORMAL, False, "High Tower Text")
        title.SetForegroundColour(wx.BLACK)
        title.SetFont(font)

        name_text = wx.StaticText(self, 1, label="Username: ", pos=(10, 40))
        self.nameField = wx.TextCtrl(self, -1, name="username", pos=(10, 60), size=(150, -1))

        pass_text = wx.StaticText(self, 1, pos=(10, 90), label="Password: ")
        self.passField = wx.TextCtrl(self, -1, name="password", pos=(10, 110), size=(150, -1), style=wx.TE_PASSWORD)

        pub.subscribe(self.login_ok, "loginOk")
        pub.subscribe(self.login_not_ok, "loginNotOk")

        ok_button = wx.Button(self, label="OK", pos=(15, 140))
        self.Bind(wx.EVT_BUTTON, self.on_ok, ok_button)

        register_button = wx.Button(self, label="REGISTER", pos=(100, 140))
        self.Bind(wx.EVT_BUTTON, self.register_control, register_button)

        self.Hide()

    def register_control(self, event):
        self.parent.change_screen(self, self.parent.register)

    def login_ok(self):
        self.parent.files.title.SetLabel(self.parent.username.upper())
        self.parent.change_screen(self, self.parent.files)

    def login_not_ok(self):
        self.parent.show_pop_up("Wrong username or password entered.", "Error")

    def on_ok(self, event):
        username_input = self.nameField.GetValue()
        password_input = self.passField.GetValue()

        self.nameField.SetValue("")
        self.passField.SetValue("")

        if not 0 < len(username_input) <= 10 or not 0 < len(username_input) <= 10:
            self.parent.show_pop_up("Please enter a valid username and password.", "Error")
        else:
            self.parent.username = username_input
            msg2send = clientProtocol.pack_login_request(username_input, password_input)
            self.comm.send(msg2send)


class FilesPanel(wx.Panel):
    def __init__(self, parent, frame, comm):
        wx.Panel.__init__(self, parent, pos=wx.DefaultPosition, size=(1920, 1080), style=wx.SIMPLE_BORDER)
        self.grid_sizer = None
        self.frame = frame
        self.comm = comm
        self.parent = parent

        # self.png = wx.StaticBitmap(self, -1, wx.Bitmap(r"C:\Users\talmid\Pictures\שקופית1.JPG", wx.BITMAP_TYPE_ANY))
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.title_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.title = wx.StaticText(self, -1)
        titlefont = wx.Font(60, wx.DECORATIVE, wx.NORMAL, wx.NORMAL, 0, "High tower text")
        self.title.SetFont(titlefont)

        self.title_sizer.Add(self.title)

        self.curPath = None

        self.filesObj = {}

        self.scroll_panel = wx.lib.scrolledpanel.ScrolledPanel(self, -1, size=(1670, 800), style=wx.SIMPLE_BORDER)
        self.scroll_panel.SetupScrolling()
        self.scroll_panel.SetBackgroundColour("white")

        self.files_sizer = wx.BoxSizer(wx.VERTICAL)

        self.scroll_panel.SetSizer(self.files_sizer)

        self.login_sizer = wx.BoxSizer(wx.HORIZONTAL)

        login_button = wx.Button(self, label="BACK TO LOGIN")
        self.backButton = wx.Button(self, label="BACK")
        self.Bind(wx.EVT_BUTTON, self.back_dir, self.backButton)
        self.Bind(wx.EVT_BUTTON, self.login_control, login_button)
        self.login_sizer.Add(login_button)
        self.login_sizer.AddSpacer(20)
        self.login_sizer.Add(self.backButton)

        self.sizer.AddMany([(self.title_sizer, 0, wx.CENTER),
                            (self.scroll_panel, 0, wx.CENTER),
                            (self.login_sizer, 0, wx.CENTER)])

        self.SetSizer(self.sizer)

        pub.subscribe(self._get_branches, "filesOk")
        pub.subscribe(self._delete_obj, "deleteOk")

        self.Layout()
        self.Hide()

    def login_control(self, event):
        self.parent.change_screen(self, self.parent.login)

    def _get_branches(self, branches):
        self.branches = branches

        for branch in branches:
            if branch[0] == "":
                self.curPath = ""
                self.show_files()

    def show_files(self):
        branch = ["", [], []]
        for temp in self.branches:
            if temp[0] == self.curPath:
                branch = temp

        dirs = branch[1][::]
        files = branch[2][::]

        if dirs == ['']:
            dirs = []

        if files == ['']:
            files = []

        # for child in self.scroll_panel.GetChildren():
        #     child.Destroy()

        self.scroll_panel.DestroyChildren()

        self.grid_sizer = wx.GridSizer(cols=15, hgap=10, vgap=10)

        image_paths = [r"C:\Users\reefg\PycharmProjects\Project_code_start\Graphics\dirs_image.png",
                       r"C:\Users\reefg\PycharmProjects\Project_code_start\Graphics\files_image.png"]

        # Add items with corresponding images to the grid sizer
        while dirs or files:
            dir_file_flag = False
            if dirs:
                item = dirs.pop(0)
                image_path = image_paths[0]
                dir_file_flag = True
            elif files:
                item = files.pop(0)
                image_path = image_paths[1]
            else:
                continue

            item_sizer = wx.BoxSizer(wx.VERTICAL)

            # Add image
            item_image = wx.StaticBitmap(self.scroll_panel, -1, wx.Bitmap(image_path, wx.BITMAP_TYPE_ANY),
                                         size=(100, 80), name=item)
            item_image.Bind(wx.EVT_LEFT_DOWN, self.select_file)
            item_sizer.Add(item_image, 0, wx.ALL)

            # Add item text
            item_text = wx.StaticText(self.scroll_panel, label=item, name=item)
            item_text.Bind(wx.EVT_LEFT_DOWN, self.select_file)
            item_sizer.Add(item_text, 0, wx.CENTER)

            self.filesObj[f"{self.curPath}/{item}".lstrip('/')] = (item_sizer, dir_file_flag)

            # Add item sizer to grid_sizer
            self.grid_sizer.Add(item_sizer, 0, wx.CENTER)

        # Set the grid sizer for the scrollable panel
        self.files_sizer.Add(self.grid_sizer, 0, wx.TOP)

        # Scroll to the top
        self.scroll_panel.Scroll(0, 0)

        if self.curPath == "":
            self.backButton.Hide()
        else:
            self.backButton.Show()

        # Refresh the layout
        self.sizer.Layout()

    def select_file(self, event):
        obj = event.GetEventObject()

        if self.filesObj[f"{self.curPath}/{obj.GetName()}".lstrip('/')][1]:
            self.chose_dir(obj.GetName())

        else:
            self._delete_file_request(obj.GetName())

    def chose_dir(self, name):
        self.curPath += f"/{name}"
        self.curPath = self.curPath.lstrip('/')

        self.show_files()

    def back_dir(self, event):
        self.curPath = "/".join(self.curPath.split('/')[:-1])

        self.show_files()

    def _delete_file_request(self, name):
        full_path = f"{self.curPath}/{name}".lstrip("/")
        msg2send = clientProtocol.pack_delete_request(self.parent.username, full_path)
        self.comm.send(msg2send)

    def _delete_obj(self, name):
        name = "/".join(name.split("/")[1::])
        isDir = self.filesObj[name][1]
        name = name.split("/")[-1]

        for branch in self.branches:
            if branch[0] == self.curPath:
                if isDir:
                    branch[1].remove(name)
                else:
                    branch[2].remove(name)
                break

        self.show_files()

    # def _delete_obj(self, name):
    #     file_sizer = self.filesObj[name][0]
    #
    #     elements = []
    #
    #     for child in file_sizer.GetChildren():
    #         elements.append(child.Window)
    #
    #     for element in elements:
    #         if element:
    #             element.Destroy()
    #
    #     self.Layout()


class RegistrationPanel(wx.Panel):
    def __init__(self, parent, frame, comm):
        wx.Panel.__init__(self, parent, pos=wx.DefaultPosition, size=(1920, 1080), style=wx.SIMPLE_BORDER)
        self.frame = frame
        self.comm = comm
        self.parent = parent
        self.SetBackgroundColour(wx.LIGHT_GREY)

        title = wx.StaticText(self, -1, label="Register panel", pos=(0, 0))
        titlefont = wx.Font(22, wx.DECORATIVE, wx.NORMAL, wx.NORMAL)
        title.SetForegroundColour(wx.BLACK)
        title.SetFont(titlefont)

        login_button = wx.Button(self, label="BACK TO LOGIN", pos=(10, 190))
        self.Bind(wx.EVT_BUTTON, self.login_control, login_button)

        name_text = wx.StaticText(self, 1, label="UserName: ", pos=(10, 40))
        self.nameField = wx.TextCtrl(self, -1, name="username", pos=(10, 60), size=(150, -1))

        pass_text = wx.StaticText(self, 1, pos=(10, 90), label="Password: ")
        self.passField = wx.TextCtrl(self, -1, name="password", pos=(10, 110), size=(150, -1), style=wx.TE_PASSWORD)

        email_text = wx.StaticText(self, 1, pos=(10, 140), label="Email: ")
        self.emailField = wx.TextCtrl(self, -1, name="email", pos=(10, 160), size=(150, -1))

        pub.subscribe(self.register_ok, "registerOk")
        pub.subscribe(self.register_not_ok, "registerNotOk")

        register_button = wx.Button(self, label="REGISTER", pos=(120, 190))
        self.Bind(wx.EVT_BUTTON, self.on_register, register_button)

        self.Hide()

    def login_control(self, event):
        self.parent.change_screen(self, self.parent.login)

    def on_register(self, event):
        username_input = self.nameField.GetValue()
        password_input = self.passField.GetValue()
        email_input = self.emailField.GetValue()

        self.nameField.SetValue("")
        self.passField.SetValue("")
        self.emailField.SetValue("")

        if not 0 < len(username_input) <= 10 or not 0 < len(username_input) <= 10 or not 0 < len(email_input) <= 50:
            self.parent.show_pop_up("Please enter a valid username and password.", "Error")

        else:
            msg2send = clientProtocol.pack_register_request(username_input, password_input, email_input)
            self.comm.send(msg2send)

    def register_ok(self):
        self.parent.change_screen(self, self.parent.login)
        self.parent.show_pop_up("User created successfully.", "Message")

    def register_not_ok(self):
        self.parent.show_pop_up("User already exists.", "Error")


if __name__ == '__main__':
    app = wx.App()
    frame1 = MyFrame(comm="")
    app.MainLoop()
