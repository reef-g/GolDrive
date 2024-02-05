import os
import Settings
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

        pub.subscribe(self.show_pop_up, "showPopUp")

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
        self.files_comm = None

        # self.png = wx.StaticBitmap(self, -1, wx.Bitmap(r"C:\Users\talmid\Pictures\שקופית1.JPG", wx.BITMAP_TYPE_ANY))
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.title_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.title = wx.StaticText(self, -1)
        titlefont = wx.Font(60, wx.DECORATIVE, wx.NORMAL, wx.NORMAL, 0, "High tower text")
        self.title.SetFont(titlefont)

        self.title_sizer.Add(self.title)

        self.curPath = None
        self.file_name = ""
        self.filesObj = {}

        self.scroll_panel = wx.lib.scrolledpanel.ScrolledPanel(self, -1, size=(1670, 800), style=wx.SIMPLE_BORDER)
        self.scroll_panel.SetupScrolling()
        self.scroll_panel.SetBackgroundColour("white")

        self.icons_and_files_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.icons_sizer = wx.BoxSizer(wx.VERTICAL)
        self.settings_img = wx.StaticBitmap(self, -1, wx.Bitmap(
            f"{Settings.USER_IMAGES_PATH}/Settings.png", wx.BITMAP_TYPE_ANY))
        self.shared_files_img = wx.StaticBitmap(self, -1, wx.Bitmap(
            f"{Settings.USER_IMAGES_PATH}/Shared.png", wx.BITMAP_TYPE_ANY))

        self.shared_files_img.Bind(wx.EVT_LEFT_DOWN, self.show_shared_files)

        self.icons_sizer.AddSpacer(10)
        self.icons_sizer.Add(self.settings_img)
        self.icons_sizer.AddSpacer(22)
        self.icons_sizer.Add(self.shared_files_img)

        self.files_sizer = wx.BoxSizer()
        self.icons_and_files_sizer.AddSpacer(90)
        self.icons_and_files_sizer.Add(self.scroll_panel, 0, wx.CENTER)
        self.icons_and_files_sizer.AddSpacer(17)
        self.icons_and_files_sizer.Add(self.icons_sizer)

        self.scroll_panel.SetSizer(self.files_sizer)

        self.login_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.back_sizer = wx.BoxSizer(wx.HORIZONTAL)

        login_button = wx.Button(self, label="BACK TO LOGIN")
        self.backButton = wx.Button(self, label="BACK")
        self.uploadButton = wx.Button(self, label="UPLOAD FILE")
        self.createDirButton = wx.Button(self, label="CREATE DIRECTORY")
        self.Bind(wx.EVT_BUTTON, self.login_control, login_button)
        self.Bind(wx.EVT_BUTTON, self.back_dir, self.backButton)
        self.Bind(wx.EVT_BUTTON, self.upload_file_request, self.uploadButton)
        self.Bind(wx.EVT_BUTTON, self.create_dir_request, self.createDirButton)
        self.login_sizer.Add(login_button)
        self.login_sizer.AddSpacer(20)
        self.back_sizer.Add(self.backButton)
        self.back_sizer.AddSpacer(20)
        self.login_sizer.Add(self.back_sizer)
        self.login_sizer.Add(self.uploadButton)
        self.login_sizer.AddSpacer(20)
        self.login_sizer.Add(self.createDirButton)

        self.sizer.AddMany([(self.title_sizer, 0, wx.CENTER),
                            (self.icons_and_files_sizer, 0, wx.CENTER),
                            (self.login_sizer, 0, wx.CENTER)])

        self.SetSizer(self.sizer)

        pub.subscribe(self._get_branches, "filesOk")
        pub.subscribe(self._delete_obj, "deleteOk")
        pub.subscribe(self._rename_obj, "renameOk")
        pub.subscribe(self._upload_object, "uploadOk")
        pub.subscribe(self._create_dir, "createOk")
        pub.subscribe(self._add_shared_file, "addFile")
        pub.subscribe(self._files_comm_update, "update_file_comm")

        self.drag_data = wx.CustomDataObject("Text")
        self.drag_source = None

        self.Layout()
        self.Hide()

    def _files_comm_update(self, filecomm):
        self.files_comm = filecomm

    def login_control(self, event):
        self.parent.change_screen(self, self.parent.login)

    def _get_branches(self, branches):
        self.branches = branches

        for branch in branches:
            branch[1].sort()
            branch[2].sort()
            if branch[1] == [""]:
                branch[1].pop(0)
            if branch[2] == [""]:
                branch[2].pop(0)

        for branch in branches:
            if branch[0] == "":
                branch[1].remove("Shared")
                self.curPath = ""
                self.show_files(self.curPath)

    def show_files(self, path):
        self.scroll_panel.DestroyChildren()

        if self.curPath.split('/')[-1] != "Shared":
            self.shared_files_img.Show()

        if path == "":
            self.backButton.Show(False)
        else:
            self.backButton.Show(True)

        branch = ["", [], []]
        for temp in self.branches:
            if temp[0] == path:
                branch = temp

        dirs = branch[1][::]
        files = branch[2][::]

        self.grid_sizer = wx.GridSizer(cols=15, hgap=10, vgap=10)

        image_paths = [f"{Settings.USER_IMAGES_PATH}/dirs_image.png",
                       f"{Settings.USER_IMAGES_PATH}/files_image.png"]

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

            item_sizer.Add(item_image, 0, wx.ALL)

            # Add item text
            item_text = wx.StaticText(self.scroll_panel, label=item[:10] + "..." if len(item) > 13 else item, name=item)
            item_sizer.Add(item_text, 0, wx.CENTER)

            where_bind = wx.EVT_RIGHT_DOWN
            if dir_file_flag:
                where_bind = wx.EVT_LEFT_DOWN

            item_text.Bind(where_bind, self.select_file)
            item_image.Bind(where_bind, self.select_file)

            self.filesObj[f"{path}/{item}".lstrip('/')] = (item_sizer, dir_file_flag)

            # Add item sizer to grid_sizer
            self.grid_sizer.Add(item_sizer, 0, wx.CENTER)

        # Set the grid sizer for the scrollable panel
        self.files_sizer.Add(self.grid_sizer, 0, wx.TOP)

        # Scroll to the top
        self.scroll_panel.Scroll(0, 0)

        # Refresh the layout
        self.sizer.Layout()

    def select_file(self, event):
        obj = event.GetEventObject()

        if self.filesObj[f"{self.curPath}/{obj.GetName()}".lstrip('/')][1]:
            self.chose_dir(obj.GetName())

        else:
            self.PopupMenu(PopMenu(self, name=obj.GetName()))

    def chose_dir(self, name):
        self.curPath += f"/{name}"
        self.curPath = self.curPath.lstrip('/')
        self.show_files(self.curPath)

    def back_dir(self, event):
        self.curPath = "/".join(self.curPath.split('/')[:-1])
        self.show_files(self.curPath)

    def delete_file_request(self, name):
        dlg = wx.MessageDialog(self, 'Do you want to delete?', 'Confirmation', wx.YES_NO | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()

        if result == wx.ID_YES:
            self.file_name = name
            full_path = f"{self.parent.username}/{self.curPath}/{self.file_name}".lstrip("/")
            msg2send = clientProtocol.pack_delete_request(full_path)
            self.comm.send(msg2send)

    def _delete_obj(self):
        is_dir = self.filesObj[f"{self.curPath}/{self.file_name}".lstrip('/')][1]

        for branch in self.branches:
            if branch[0] == self.curPath:
                if is_dir:
                    branch[1].remove(self.file_name)
                else:
                    branch[2].remove(self.file_name)
                break

        self.show_files(self.curPath)
        self.parent.show_pop_up(f"Deleted {self.file_name} successfully.", "Success")

    def rename_file_request(self, name):
        dlg = wx.TextEntryDialog(self, f'Do you want to rename {name}?', 'Confirmation', '')
        result = dlg.ShowModal()
        dlg.Destroy()

        if result == wx.ID_OK:
            self.file_name = name
            full_path = f"{self.parent.username}/{self.curPath}/{name}".lstrip("/")
            msg2send = clientProtocol.pack_rename_file_request(full_path, dlg.GetValue())
            self.comm.send(msg2send)

    def _rename_obj(self, new_name):
        is_dir = self.filesObj[f"{self.curPath}/{self.file_name}".lstrip('/')][1]

        for branch in self.branches:
            if branch[0] == self.curPath:
                if is_dir:
                    index_to_replace = branch[1].index(self.file_name)
                    branch[1][index_to_replace] = new_name
                else:
                    index_to_replace = branch[2].index(self.file_name)
                    branch[2][index_to_replace] = new_name
                break

        self.show_files(self.curPath)
        self.parent.show_pop_up(f"Renamed {self.file_name} to {new_name} successfully.", "Success")

    def download_file_request(self, file_name):
        base_name, file_extension = os.path.splitext(file_name)

        file_type = file_extension[1:].lower()

        type_descriptions = {
            'txt': 'Text files',
            'docx': 'Microsoft Word documents',
            'jpg': 'JPEG images',
            'png': 'PNG images',
        }

        wildcard_list = [f"{type_descriptions[key]} (*.{key.lower()})|*.{key.lower()}" for key in type_descriptions]
        if file_type in type_descriptions:
            wildcard_list.remove(f"{type_descriptions[file_type]} (*.{file_type})|*.{file_type}")
            wildcard_list.insert(0, f"{type_descriptions[file_type]} (*.{file_type})|*.{file_type}")
            wildcard_list.append("All files (*.*)|*.*")
        else:
            wildcard_list.insert(0, "All files (*.*)|*.*")

        wildcard = '|'.join(wildcard_list)

        dlg = wx.FileDialog(self, "Choose a file", defaultFile=file_name, wildcard=wildcard, style=wx.FD_SAVE)
        result = dlg.ShowModal()

        if result == wx.ID_OK:
            selected_path = dlg.GetPath().replace('\\', '/')

            msg2send = clientProtocol.pack_download_file_request(f"{self.parent.username}/{self.curPath}/{file_name}", selected_path)
            self.files_comm.send(msg2send)

        dlg.Destroy()

    def upload_file_request(self, event):
        dlg = wx.FileDialog(self, "Choose a file", style=wx.DD_DEFAULT_STYLE)
        result = dlg.ShowModal()

        if result == wx.ID_OK:
            selected_path = dlg.GetPath().replace('\\', '/')
            self.files_comm.send_file(selected_path, f"{self.parent.username}/{self.curPath}".rstrip('/'))

    def _upload_object(self, path):
        name_to_add = path.split('/')[-1]

        for branch in self.branches:
            if branch[0] == self.curPath:
                branch[2].append(name_to_add)
                branch[2].sort()
                break
        self.show_files(self.curPath)

    def create_dir_request(self, event):
        dlg = wx.TextEntryDialog(self, f'Please enter the name for the directory:', 'Create new directory', '')
        result = dlg.ShowModal()
        dlg.Destroy()

        if result == wx.ID_OK:
            self.file_name = dlg.GetValue()
            full_path = f"{self.parent.username}/{self.curPath}/{self.file_name}".lstrip("/")
            msg2send = clientProtocol.pack_create_folder_request(full_path)
            self.comm.send(msg2send)

    def _create_dir(self):
        for branch in self.branches:
            if branch[0] == self.curPath:
                branch[1].append(self.file_name)
                branch[1].sort()
                break

        self.branches.append((f'{self.curPath}/{self.file_name}'.lstrip('/'), [], []))
        self.show_files(self.curPath)

    def share_file_request(self, name):
        dlg = wx.TextEntryDialog(self, f'Enter username of user you want to share to:', 'Confirmation', '')
        result = dlg.ShowModal()
        dlg.Destroy()

        if result == wx.ID_OK:
            username = dlg.GetValue()
            if username != self.parent.username:
                full_path = f"{self.parent.username}/{self.curPath}/{name}".replace('//', '/')
                msg = clientProtocol.pack_share_request(full_path, username)
                self.comm.send(msg)

            else:
                self.parent.show_pop_up(f"Don't enter your own username.", "Error")

    def show_shared_files(self, event):
        self.shared_files_img.Hide()
        self.curPath += "/Shared".lstrip('/')
        self.show_files("Shared")

    def _add_shared_file(self, path):
        user_who_shared, file = path.split('/')
        for branch in self.branches:
            if branch[0] == "Shared":
                branch[1].append(user_who_shared)
                branch[1].sort()
                break

        self.branches.append((f'Shared/{user_who_shared}'.lstrip('/'), [], []))
        self.branches[-1][2].append(file)
        self.show_files(self.curPath)


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


class PopMenu(wx.Menu):

    def __init__(self, parent, name):
        super(PopMenu, self).__init__()

        self.parent = parent
        self.name = name
        self.pos = wx.GetMousePosition()

        static_text_item = wx.MenuItem(self, 0, name)
        # Make it non-selectable
        static_text_item.Enable(False)
        self.Append(static_text_item)

        self.AppendSeparator()

        self.Append(wx.MenuItem(self, -1, 'delete file'))

        self.Append(wx.MenuItem(self, -1, 'rename file'))

        self.Append(wx.MenuItem(self, -1, 'download file'))

        self.Append(wx.MenuItem(self, -1, 'share file'))

        self.AppendSeparator()

        cancel_item = wx.MenuItem(self, -1, "Cancel")
        self.Append(cancel_item)

        # Bind the menu item click event
        self.Bind(wx.EVT_MENU, self.on_menu_item_click)

    def on_menu_item_click(self, event):
        clicked_item_id = event.GetId()
        clicked_item = self.FindItemById(clicked_item_id)

        item = clicked_item.GetItemLabelText()
        if item == "delete file":
            self.parent.delete_file_request(self.name)
        elif item == "rename file":
            self.parent.rename_file_request(self.name)
        elif item == "download file":
            self.parent.download_file_request(self.name)
        elif item == "share file":
            self.parent.share_file_request(self.name)


if __name__ == '__main__':
    app = wx.App()
    frame1 = MyFrame(comm="")
    app.MainLoop()
