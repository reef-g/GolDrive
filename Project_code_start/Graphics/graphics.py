import io
import os
from settings import Settings
import wx
import wx.lib.scrolledpanel
from pubsub import pub
import clientProtocol
import time


class MyFrame(wx.Frame):
    def __init__(self, comm, parent=None):
        super(MyFrame, self).__init__(parent, title="GolDrive")
        self.comm = comm
        self.Maximize()

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
        self.files_comm = None
        self.SetBackgroundColour(wx.LIGHT_GREY)
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
        cur_screen.Hide()
        screen.Show()

        self.Layout()
        self.Refresh()
        self.Update()

    def show_pop_up(self, text, title):
        dlg = wx.MessageDialog(self, text, title, wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def _files_comm_update(self, filecomm):
        self.files_comm = filecomm


class LoginPanel(wx.Panel):
    def __init__(self, parent, frame, comm):
        wx.Panel.__init__(self, parent, pos=wx.DefaultPosition, size=(1920, 1080), style=wx.SIMPLE_BORDER)
        self.frame = frame
        self.comm = comm
        self.parent = parent
        self.SetBackgroundColour(wx.LIGHT_GREY)

        title_font = wx.Font(65, wx.DECORATIVE, wx.NORMAL, wx.NORMAL, False, "High Tower Text")
        text_font = wx.Font(30, wx.DECORATIVE, wx.NORMAL, wx.NORMAL, False)
        self.entry_font = wx.Font(20, wx.DECORATIVE, wx.NORMAL, wx.NORMAL, False)

        hidden_path = f"{Settings.USER_IMAGES_PATH}\\hidden-eye.png"
        open_path = f"{Settings.USER_IMAGES_PATH}\\open-eye.png"

        self.is_showing_password = False
        self.hidden_bitmap = wx.Bitmap(hidden_path, wx.BITMAP_TYPE_ANY)
        self.shown_bitmap = wx.Bitmap(open_path, wx.BITMAP_TYPE_ANY)

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.sizer.AddSpacer(290)
        title = wx.StaticText(self, -1, label="LOG IN")
        title.SetForegroundColour(wx.BLACK)
        title.SetFont(title_font)

        name_sizer = wx.BoxSizer(wx.VERTICAL)
        name_text = wx.StaticText(self, 1, label="Username: ")
        name_text.SetFont(text_font)
        self.nameField = wx.TextCtrl(self, -1, name="username", size=(650, 40))
        self.nameField.SetFont(self.entry_font)

        name_sizer.Add(name_text, 0, wx.Center, 5)
        name_sizer.Add(self.nameField)
        name_sizer.AddSpacer(15)

        self.pass_sizer = wx.BoxSizer(wx.HORIZONTAL)
        pass_text = wx.StaticText(self, 1, label="Password: ")
        pass_text.SetFont(text_font)
        self.passField = wx.TextCtrl(self, -1, name="password", size=(650, 40), style=wx.TE_PASSWORD)
        self.passField.SetFont(self.entry_font)

        name_sizer.Add(pass_text)
        self.pass_sizer.AddSpacer(27)
        self.pass_sizer.Add(self.passField)
        self.eye_bitmap = wx.StaticBitmap(self, wx.ID_ANY, self.hidden_bitmap)
        self.eye_bitmap.Bind(wx.EVT_LEFT_DOWN, self.change_visibility)
        self.pass_sizer.Add(self.eye_bitmap)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(self, label="LOG IN", size=(90, 40))
        self.Bind(wx.EVT_BUTTON, self.on_ok, ok_button)

        register_button = wx.Button(self, label="REGISTER", size=(90, 40))
        self.Bind(wx.EVT_BUTTON, self.register_control, register_button)

        button_sizer.Add(ok_button, 0, wx.CENTER, 10)
        button_sizer.AddSpacer(80)
        button_sizer.Add(register_button, 0, wx.CENTER, 10)

        self.sizer.AddMany([(title, 0, wx.CENTER, 10),
                            (name_sizer, 0, wx.CENTER, 5),
                            (self.pass_sizer, 0, wx.CENTER, 5)])

        self.sizer.AddSpacer(20)
        self.sizer.Add(button_sizer, 0, wx.CENTER, 5)

        pub.subscribe(self.login_ok, "loginOk")
        pub.subscribe(self._get_details, "detailsOk")

        self.SetSizer(self.sizer)
        self.Layout()

        self.Hide()

    def change_visibility(self, event):
        open_or_closed = self.hidden_bitmap if not self.is_showing_password else self.shown_bitmap

        position = self.passField.GetPosition()
        size = self.passField.GetSize()

        # Create a new text control with the updated style
        new_style = wx.TE_PASSWORD if not self.is_showing_password else wx.TE_PROCESS_ENTER
        new_textctrl = wx.TextCtrl(self, pos=position, size=size, style=new_style)
        new_textctrl.SetFont(self.entry_font)

        # Copy the text from the existing text control to the new one
        new_textctrl.SetValue(self.passField.GetValue())

        self.eye_bitmap.SetBitmap(open_or_closed)
        self.pass_sizer.Replace(self.passField, new_textctrl)
        self.passField.Destroy()
        self.passField = new_textctrl

        self.is_showing_password = not self.is_showing_password

    def register_control(self, event):
        self.parent.change_screen(self, self.parent.register)

    def login_ok(self):
        self.parent.files.title.SetLabel(self.parent.username.upper())
        msg = clientProtocol.pack_get_details_request(self.parent.username)
        self.parent.files_comm.send(msg)
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

    def _get_details(self, email, photo):
        self.parent.email = email
        self.parent.profilePhoto = photo
        wx.CallAfter(pub.sendMessage, "changeSettingsToPhoto")


class MyDropTarget(wx.DropTarget):
    def __init__(self, panel):
        wx.DropTarget.__init__(self)
        self.panel = panel

        self.name = wx.TextDataObject()
        self.SetDataObject(self.name)
        # Specify the data format you want to accept
        self.data = wx.TextDataObject()
        self.SetDataObject(self.data)

    def OnDragOver(self, x, y, default):
        # Check if the cursor is above an image using the panel's method
        cursor_to_show = wx.DragNone
        isAbove, name = self.panel.is_cursor_above_image()

        if isAbove:
            # Visual feedback for a valid drop location
            cursor_to_show = wx.DragCopy
            self.data = name

        return cursor_to_show

    def OnData(self, x, y, result):
        # Get the dropped data
        dragged_name = self.name.GetText()
        dropped_name = self.data.GetText()
        # Process the dropped data (you can customize this part)
        if dragged_name and dropped_name:
            self.panel.handle_dropped_item(dragged_name, dropped_name)

        return result


class FilesPanel(wx.Panel):
    def __init__(self, parent, frame, comm):
        wx.Panel.__init__(self, parent, pos=wx.DefaultPosition, size=(1920, 1080), style=wx.SIMPLE_BORDER)

        self.grid_sizer = None
        self.frame = frame
        self.comm = comm
        self.parent = parent

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.title_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.title = wx.StaticText(self, -1)
        titlefont = wx.Font(60, wx.DECORATIVE, wx.NORMAL, wx.NORMAL, 0, "High tower text")
        self.title.SetFont(titlefont)

        self.title_sizer.Add(self.title)

        self.curPath = None
        self.copied_file = None
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
        self.settings_img.Bind(wx.EVT_LEFT_DOWN, self.show_settings)

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
        self.scroll_panel.Bind(wx.EVT_RIGHT_DOWN, self.show_menu)

        self.buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.login_button = wx.Button(self, label="BACK TO LOGIN")
        self.backButton = wx.Button(self, label="BACK")
        self.uploadButton = wx.Button(self, label="UPLOAD FILE")
        self.createDirButton = wx.Button(self, label="CREATE DIRECTORY")
        self.pasteButton = wx.Button(self, label="PASTE")

        self.login_button.Bind(wx.EVT_BUTTON, self.login_control)
        self.backButton.Bind(wx.EVT_BUTTON, self.back_dir)
        self.uploadButton.Bind(wx.EVT_BUTTON, self.upload_file_request)
        self.createDirButton.Bind(wx.EVT_BUTTON, self.create_dir_request)
        self.pasteButton.Bind(wx.EVT_BUTTON, self.paste_file_request)

        self.buttons_sizer.Add(self.backButton)
        self.buttons_sizer.AddSpacer(20)
        self.buttons_sizer.Add(self.login_button)
        self.buttons_sizer.AddSpacer(20)
        self.buttons_sizer.Add(self.uploadButton)
        self.buttons_sizer.AddSpacer(20)
        self.buttons_sizer.Add(self.createDirButton)
        self.buttons_sizer.AddSpacer(20)
        self.buttons_sizer.Add(self.pasteButton)

        self.sizer.AddMany([(self.title_sizer, 0, wx.CENTER),
                            (self.icons_and_files_sizer, 0, wx.CENTER)])

        self.sizer.AddSpacer(15)
        self.sizer.Add(self.buttons_sizer, 0, wx.CENTER)

        self.SetSizer(self.sizer)

        pub.subscribe(self._get_branches, "filesOk")
        pub.subscribe(self._delete_obj, "deleteOk")
        pub.subscribe(self._rename_obj, "renameOk")
        pub.subscribe(self._upload_object, "uploadOk")
        pub.subscribe(self._create_dir, "createOk")
        pub.subscribe(self._add_shared_file, "addFile")
        pub.subscribe(self._move_file, "moveFile")
        pub.subscribe(self._handle_paste_file, "pasteFile")
        pub.subscribe(self._show_progress_bar, "startBar")
        pub.subscribe(self._change_progress_bar, "changeProgress")
        pub.subscribe(self.change_settings_to_profile, "changeSettingsToPhoto")

        self.Layout()
        self.Hide()
        self.drop_target = MyDropTarget(self)
        self.SetDropTarget(self.drop_target)

    def change_settings_to_profile(self):

        image = wx.Image(io.BytesIO(self.parent.profilePhoto), wx.BITMAP_TYPE_ANY)
        image.Rescale(108, 108)

        # Convert the wx.Image to a wx.Bitmap
        bitmap = wx.Bitmap(image)

        self.settings_img.SetBitmap(bitmap)

    def show_menu(self, event):
        flag = True
        if self.curPath == "":
            flag = False
        self.PopupMenu(MenuFeatures(self, flag))

    def start_drag(self, event):
        # Start a drag-and-drop operation when an item is left-clicked
        item_text = event.GetEventObject()
        data = wx.TextDataObject(item_text.GetName())
        self.drop_target.name = data
        drop_source = wx.DropSource(item_text)
        drop_source.SetData(data)
        drop_source.DoDragDrop(wx.Drag_CopyOnly)

    def handle_dropped_item(self, item_dropped, dropped_to_item):
        # Process the dropped item (customize this part based on your needs)
        self.file_name = item_dropped
        src = f"{self.parent.username}/{self.curPath}/{item_dropped}".replace('//', '/')
        dst = f"{self.parent.username}/{self.curPath}/{dropped_to_item}".replace('//', '/')

        msg = clientProtocol.pack_move_file_folder_request(src, dst)
        self.comm.send(msg)

    def is_cursor_above_image(self):
        # Get the mouse position
        mouse_position = wx.GetMousePosition()
        screen_position = self.scroll_panel.GetScreenPosition()
        mouse_x, mouse_y = mouse_position.x - screen_position.x, mouse_position.y - screen_position.y
        flag = False
        text_data_object = None

        # Iterate over sizer items to check if the cursor is over an image
        for item in self.scroll_panel.GetChildren():
            item_rect = item.GetRect()
            if self.filesObj[f"{self.curPath}/{item.GetName()}".lstrip('/')][1]:
                if item_rect.Contains(mouse_x, mouse_y):
                    flag = True
                    text_data_object = wx.TextDataObject()
                    text_data_object.SetText(item.GetName())

        return flag, text_data_object

    def login_control(self, event):
        self.parent.change_screen(self, self.parent.login)

    def _get_branches(self, branches):
        self.branches = branches
        self.copied_file = None

        for branch in branches:
            branch[1].sort()
            branch[2].sort()
            if branch[1] == [""]:
                branch[1].pop(0)
            if branch[2] == [""]:
                branch[2].pop(0)

        for branch in branches:
            if branch[0] == "":
                branch[1].remove("@#$SHAREDFILES$#@")
                self.curPath = ""
                self.show_files(self.curPath)

    def show_files(self, path):
        self.scroll_panel.DestroyChildren()

        if "@#$SHAREDFILES$#@" not in self.curPath.split('/'):
            self.shared_files_img.Show()
        else:
            split_path = self.curPath.split('/')
            path = '/'.join(split_path[split_path.index("@#$SHAREDFILES$#@"):])

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
            else:
                item_text.Bind(wx.EVT_LEFT_DOWN, self.start_drag)
                item_image.Bind(wx.EVT_LEFT_DOWN, self.start_drag)

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

        path_to_find = f"{self.curPath}/{obj.GetName()}".lstrip('/')

        if path_to_find not in self.filesObj and "@#$SHAREDFILES$#@" in path_to_find:
            split_path = self.curPath.split('/')
            path_to_find = '/'.join(split_path[split_path.index("@#$SHAREDFILES$#@"):]) + '/' + obj.GetName()

        if self.filesObj[path_to_find][1]:
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
            self.parent.files_comm.send(msg2send)

        dlg.Destroy()

    def upload_file_request(self, event):
        dlg = wx.FileDialog(self, "Choose a file", style=wx.DD_DEFAULT_STYLE)
        result = dlg.ShowModal()

        if result == wx.ID_OK:
            selected_path = dlg.GetPath().replace('\\', '/')
            self.parent.files_comm.send_file(12, selected_path, f"{self.parent.username}/{self.curPath}".rstrip('/'))

    def _upload_object(self, path):
        name_to_add = path.split('/')[-1]
        text_to_show = f"Uploaded {name_to_add} successfully."
        for branch in self.branches:
            if branch[0] == self.curPath:
                if name_to_add not in branch[2]:
                    branch[2].append(name_to_add)
                    branch[2].sort()
                else:
                    text_to_show = f"Updated {name_to_add} successfully."
                break
        self.show_files(self.curPath)
        self.parent.show_pop_up(text_to_show, "Success")

    def create_dir_request(self, event):
        dlg = wx.TextEntryDialog(self, f'Please enter the name for the directory:', 'Create new directory', '')
        result = dlg.ShowModal()
        dlg.Destroy()

        if result == wx.ID_OK:
            if dlg.GetValue() != "@#$SHAREDFILES$#@":
                self.file_name = dlg.GetValue()
                full_path = f"{self.parent.username}/{self.curPath}/{self.file_name}".lstrip("/")
                msg2send = clientProtocol.pack_create_folder_request(full_path)
                self.comm.send(msg2send)
            else:
                self.parent.show_pop_up(f"Can't create a folder with that name, please choose a different name.", "Error")

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
        self.curPath += "/@#$SHAREDFILES$#@"
        self.curPath.lstrip('/')
        self.show_files("@#$SHAREDFILES$#@")

    def _add_shared_file(self, path):
        user_who_shared, file = path.split('/')[0], path.split('/')[-1]
        for branch in self.branches:
            if branch[0] == "@#$SHAREDFILES$#@":
                if user_who_shared not in branch[1]:
                    branch[1].append(user_who_shared)
                    branch[1].sort()
                break

        if not any(branch[0] == f"@#$SHAREDFILES$#@/{user_who_shared}" for branch in self.branches):
            self.branches.append((f'@#$SHAREDFILES$#@/{user_who_shared}', [], []))
            self.branches[-1][2].append(file)
            self.branches[-1][2].sort()

        else:
            for branch in self.branches:
                if branch[0] == f"@#$SHAREDFILES$#@/{user_who_shared}":
                    branch[2].append(file)
                    branch[2].sort()

        self.show_files(self.curPath)

    def _move_file(self, path):
        path = "/".join(path.split('/')[1::])

        for branch in self.branches:
            if branch[0] == self.curPath:
                branch[2].remove(self.file_name)

            if branch[0] == path:
                branch[2].append(self.file_name)

        self.show_files(self.curPath)
        self.parent.show_pop_up("Moved file successfully", "Success")

    def paste_file_request(self, event):
        if self.copied_file:
            src = f"{self.parent.username}/{self.copied_file}"
            dst = f"{self.parent.username}/{self.curPath}".rstrip('/')

            msg = clientProtocol.pack_paste_file_request(src, dst)
            self.comm.send(msg)
        else:
            self.parent.show_pop_up(f"Your clipboard is empty.", "Error")

    def _handle_paste_file(self):
        file_name = self.copied_file.split('/')[-1]
        text_to_show = "Pasted file successfully."
        for branch in self.branches:
            if branch[0] == self.curPath:
                if file_name not in branch[2]:
                    branch[2].append(file_name)
                    branch[2].sort()
                else:
                    text_to_show = "Updated file successfully."
                break

        self.show_files(self.curPath)
        self.parent.show_pop_up(text_to_show, "Success")

    def open_file_request(self, name):
        try:
            msg2send = clientProtocol.pack_open_file_request(
                f"{self.parent.username}/{self.curPath}/{name}".replace("//", '/')
            )
            self.parent.files_comm.send(msg2send)
        except Exception as e:
            print(str(e))

    def _show_progress_bar(self, name, opcode):
        msg = "Download" if opcode != "04" else "Upload"
        msg += f" at 0%"

        self.progressDialog = wx.ProgressDialog(title=name, message=msg, maximum=100,
                                                style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE)

    def _change_progress_bar(self, percent, opcode):
        while not self.progressDialog:
            pass

        self.progressDialog.Update(percent, f"Download at {percent}%" if opcode != "04" else f"Upload at {percent}%")
        # wasting time to show update of percent
        time.sleep(0.0001)

        if percent == 100:
            self.progressDialog.Destroy()

    def show_settings(self, event):
        settings = UserPanel(self.parent, self.frame, self.comm, self.parent.files_comm)

        self.parent.change_screen(self, settings)


class UserPanel(wx.Panel):
    def __init__(self, parent, frame, comm, files_comm):
        wx.Panel.__init__(self, parent, pos=wx.DefaultPosition, size=(1920, 1080), style=wx.SIMPLE_BORDER)
        self.frame = frame
        self.comm = comm
        self.files_comm = files_comm
        self.parent = parent

        self.SetBackgroundColour(wx.LIGHT_GREY)

        self.selected_path = ""
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.AddSpacer(2)

        self.title = wx.StaticText(self, -1, label="SETTINGS")
        font = wx.Font(65, wx.DECORATIVE, wx.NORMAL, wx.NORMAL, 0, "High tower text")
        self.title.SetFont(font)
        self.sizer.Add(self.title, 0, wx.CENTER)

        image = wx.Image(io.BytesIO(self.parent.profilePhoto), wx.BITMAP_TYPE_ANY)
        image.Rescale(108, 108)

        # Convert the wx.Image to a wx.Bitmap
        bitmap = wx.Bitmap(image)

        self.settings_img = wx.StaticBitmap(self, wx.ID_ANY, bitmap)

        self.titleSizer = wx.BoxSizer(wx.VERTICAL)
        self.usernameTitleSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.emailTitleSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.imageSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.userAndImageSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.usernameTitle = wx.StaticText(self, -1, label=f"Username: {self.parent.username}")
        self.emailTitle = wx.StaticText(self, -1, label=f"Email: {self.parent.email}")
        title_font = wx.Font(45, wx.DECORATIVE, wx.NORMAL, wx.NORMAL)
        self.usernameTitle.SetFont(title_font)
        self.emailTitle.SetFont(title_font)

        # adding padding to the text, so it doesn't start from the edge
        self.usernameTitleSizer.AddSpacer(120)
        self.usernameTitleSizer.Add(self.usernameTitle)

        # adding padding to the image, so it doesn't start from the edge
        self.imageSizer.Add(self.settings_img)
        self.imageSizer.AddSpacer(17)  # Adjust the spacing if needed

        # adding padding to the text, so it doesn't start from the edge
        self.emailTitleSizer.AddSpacer(120)
        self.emailTitleSizer.Add(self.emailTitle)

        self.sizer.Add(self.imageSizer, 0, wx.ALIGN_RIGHT)
        self.sizer.Add(self.usernameTitleSizer)
        self.sizer.AddSpacer(350)
        self.sizer.Add(self.emailTitleSizer)

        self.loginButton = wx.Button(self, label="BACK TO LOGIN")
        self.filesButton = wx.Button(self, label="BACK TO FILES")
        self.changeEmailButton = wx.Button(self, label="CHANGE EMAIL")
        self.changePasswordButton = wx.Button(self, label="CHANGE PASSWORD")
        self.changePhotoButton = wx.Button(self, label="CHANGE PROFILE PHOTO")
        self.deletePhotoButton = wx.Button(self, label="DELETE PROFILE PHOTO")

        self.loginButton.Bind(wx.EVT_BUTTON, self.login_control)
        self.filesButton.Bind(wx.EVT_BUTTON, self.files_control)
        self.changeEmailButton.Bind(wx.EVT_BUTTON, self.change_email_request)
        self.changePasswordButton.Bind(wx.EVT_BUTTON, self.change_password_request)
        self.changePhotoButton.Bind(wx.EVT_BUTTON, self.change_photo_request)
        self.deletePhotoButton.Bind(wx.EVT_BUTTON, self.delete_photo_request)
        self.settings_img.Bind(wx.EVT_RIGHT_DOWN, self.show_setttings_menu)

        self.buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.buttons_sizer.Add(self.loginButton)
        self.buttons_sizer.AddSpacer(20)
        self.buttons_sizer.Add(self.filesButton)
        self.buttons_sizer.AddSpacer(20)
        self.buttons_sizer.Add(self.changeEmailButton)
        self.buttons_sizer.AddSpacer(20)
        self.buttons_sizer.Add(self.changePasswordButton)
        self.buttons_sizer.AddSpacer(20)
        self.buttons_sizer.Add(self.changePhotoButton)
        self.buttons_sizer.AddSpacer(20)
        self.buttons_sizer.Add(self.deletePhotoButton)

        self.sizer.AddSpacer(211)
        self.sizer.Add(self.buttons_sizer, 0, wx.CENTER)

        self.SetSizer(self.sizer)
        self.Layout()

        pub.subscribe(self._change_email, "changeEmailOk")
        pub.subscribe(self._change_photo, "changePhotoOk")

        self.Hide()

    def login_control(self, event):
        self.parent.change_screen(self, self.parent.login)

    def files_control(self, event):
        self.parent.change_screen(self, self.parent.files)

    def change_email_request(self, event):
        email_dlg = wx.TextEntryDialog(self, f'What new email to change to?', 'Confirmation', '')
        result = email_dlg.ShowModal()

        if result == wx.ID_OK:
            email = email_dlg.GetValue()
            email_dlg.Destroy()

            split_email = email.split('@')
            if '@' in email and len(split_email) == 2 and split_email[0] and split_email[1]:
                msg = clientProtocol.pack_send_verify_request(email)
                self.comm.send(msg)

                verify_dlg = wx.TextEntryDialog(self, f'Which 6-digit code did you receive in your mail?', 'Verify', '')
                result = verify_dlg.ShowModal()

                if result == wx.ID_OK:
                    msg = clientProtocol.pack_change_email_request(self.parent.username, email, verify_dlg.GetValue())
                    self.comm.send(msg)

                verify_dlg.Destroy()
            else:
                self.parent.show_pop_up("Please enter a valid email address.", "Error")

        else:
            email_dlg.Destroy()

    def _change_email(self, email):
        self.parent.email = email
        self.emailTitle.SetLabel(f"Email: {email}")
        self.Layout()

        self.parent.show_pop_up(f"Changed email to {email} successfully.", "Success")

    def change_password_request(self, event):
        password_dlg = ChangePasswordDialog(self, "Confirmation")
        result = password_dlg.ShowModal()

        if result == wx.ID_OK:
            values = password_dlg.GetValues()

            msg = clientProtocol.pack_change_password_request(self.parent.username, *values)
            self.comm.send(msg)
        password_dlg.Destroy()

    def change_photo_request(self, event):
        image_types = ["apng", "avif", "gif", "jpg", "jpeg", "jfif", "pjpeg", "pjp", "png", "svg", "webp", "bmp", "ico",
                       "cur", "tif", "tiff"]

        what_to_show = ([f'*.{image_type}' for image_type in image_types])
        wildcard = f"Image Files ({';'.join(what_to_show)})|{';'.join(what_to_show)}"

        dlg = wx.FileDialog(self, "Choose a file", wildcard=wildcard, style=wx.DD_DEFAULT_STYLE)
        result = dlg.ShowModal()

        if result == wx.ID_OK:
            self.selected_path = dlg.GetPath().replace('\\', '/')
            self.files_comm.send_file(4, self.selected_path, self.parent.username)

    def _change_photo(self, data):
        self.parent.profilePhoto = data

        image = wx.Image(io.BytesIO(self.parent.profilePhoto), wx.BITMAP_TYPE_ANY)
        image.Rescale(108, 108)

        # Convert the wx.Image to a wx.Bitmap
        bitmap = wx.Bitmap(image)

        self.parent.files.settings_img.SetBitmap(bitmap)
        self.settings_img.SetBitmap(bitmap)

    def delete_photo_request(self, event):
        verify_dlg = wx.MessageDialog(self, f'Are you sure you want to delete your profile photo?',
                                      'Confirmation', wx.YES_NO | wx.ICON_QUESTION)
        result = verify_dlg.ShowModal()

        if result == wx.ID_YES:
            msg = clientProtocol.pack_delete_profile_photo_request(self.parent.username)
            self.files_comm.send(msg)

    def show_setttings_menu(self, event):
        self.PopupMenu(ProfileSettings(self))


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

        msg2send = clientProtocol.pack_register_request(username_input, password_input, email_input)
        self.comm.send(msg2send)

    def register_ok(self):
        self.parent.change_screen(self, self.parent.login)
        self.parent.show_pop_up("User created successfully.", "Message")


class PopMenu(wx.Menu):
    def __init__(self, parent, name):
        super(PopMenu, self).__init__()

        image_types = ["apng", "avif", "gif", "jpg", "jpeg", "jfif", "pjpeg", "pjp", "png", "svg", "webp", "bmp", "ico",
                       "cur", "tif", "tiff"]

        self.parent = parent
        self.name = name
        self.pos = wx.GetMousePosition()

        static_text_item = wx.MenuItem(self, 0, name)
        # Make it non-selectable
        static_text_item.Enable(False)
        self.Append(static_text_item)

        self.AppendSeparator()

        self.Append(wx.MenuItem(self, -1, 'Delete file'))
        self.Append(wx.MenuItem(self, -1, 'Rename file'))
        self.Append(wx.MenuItem(self, -1, 'Download file'))
        self.Append(wx.MenuItem(self, -1, 'Share file'))
        self.Append(wx.MenuItem(self, -1, 'Copy file'))

        view_text = "Edit file"
        if self.name.split('.')[-1] in image_types:
            view_text = "Open file"

        self.Append(wx.MenuItem(self, -1, view_text))

        self.AppendSeparator()

        self.Append(wx.MenuItem(self, -1, "Cancel"))

        # Bind the menu item click event
        self.Bind(wx.EVT_MENU, self.on_menu_item_click)

    def on_menu_item_click(self, event):
        clicked_item_id = event.GetId()
        clicked_item = self.FindItemById(clicked_item_id)

        item = clicked_item.GetItemLabelText()
        if item == "Delete file":
            self.parent.delete_file_request(self.name)
        elif item == "Rename file":
            self.parent.rename_file_request(self.name)
        elif item == "Download file":
            self.parent.download_file_request(self.name)
        elif item == "Share file":
            self.parent.share_file_request(self.name)
        elif item == "Copy file":
            self.parent.copied_file = f"{self.parent.curPath}/{self.name}".lstrip('/')
        elif item == "Edit file" or item == "Open file":
            self.parent.open_file_request(self.name)


class MenuFeatures(wx.Menu):
    def __init__(self, parent, show_back):
        super(MenuFeatures, self).__init__()

        self.parent = parent
        self.pos = wx.GetMousePosition()

        self.Append(wx.MenuItem(self, -1, 'Upload file'))
        self.Append(wx.MenuItem(self, -1, 'Create new directory'))
        self.Append(wx.MenuItem(self, -1, 'Paste file'))
        self.back_item = wx.MenuItem(self, -1, 'Go back')
        self.Append(self.back_item)
        self.Enable(self.back_item.GetId(), show_back)

        self.AppendSeparator()

        self.Append(wx.MenuItem(self, -1, "Cancel"))

        # Bind the menu item click event
        self.Bind(wx.EVT_MENU, self.on_menu_item_click)

    def on_menu_item_click(self, event):
        clicked_item_id = event.GetId()
        clicked_item = self.FindItemById(clicked_item_id)

        item = clicked_item.GetItemLabelText()
        if item == "Upload file":
            self.parent.upload_file_request(wx.CommandEvent)
        elif item == "Create new directory":
            self.parent.create_dir_request(wx.CommandEvent)
        elif item == "Paste file":
            self.parent.paste_file_request(wx.CommandEvent)
        elif item == "Go back":
            self.parent.back_dir(wx.CommandEvent)


class ProfileSettings(wx.Menu):
    def __init__(self, parent):
        super(ProfileSettings, self).__init__()

        self.parent = parent
        self.pos = wx.GetMousePosition()

        self.Append(wx.MenuItem(self, -1, 'Change profile photo'))
        self.Append(wx.MenuItem(self, -1, 'Clear profile photo'))

        self.AppendSeparator()

        self.Append(wx.MenuItem(self, -1, "Cancel"))

        # Bind the menu item click event
        self.Bind(wx.EVT_MENU, self.on_menu_item_click)

    def on_menu_item_click(self, event):
        item_id = event.GetId()
        clicked_item = self.FindItemById(item_id)

        item = clicked_item.GetItemLabelText()
        if item == "Change profile photo":
            self.parent.change_photo_request(wx.CommandEvent)
        elif item == "Clear profile photo":
            self.parent.delete_photo_request(wx.CommandEvent)


class ChangePasswordDialog(wx.Dialog):
    def __init__(self, parent, title):
        super(ChangePasswordDialog, self).__init__(parent, title=title, size=(388, 230), pos=(960-174, 540-115))

        self.panel = wx.Panel(self)

        self.is_showing_password = False

        hidden_path = f"{Settings.USER_IMAGES_PATH}\\hidden-eye.png"
        open_path = f"{Settings.USER_IMAGES_PATH}\\open-eye.png"

        self.hidden_bitmap = wx.Bitmap(hidden_path, wx.BITMAP_TYPE_ANY)
        self.shown_bitmap = wx.Bitmap(open_path, wx.BITMAP_TYPE_ANY)

        # Create two text boxes
        self.old_password_ctrl = wx.TextCtrl(self.panel, size=(308, -1), style=wx.TE_PASSWORD)
        self.new_password_ctrl = wx.TextCtrl(self.panel, size=(308, -1), style=wx.TE_PASSWORD)
        self.confirm_password_ctrl = wx.TextCtrl(self.panel, size=(308, -1), style=wx.TE_PASSWORD)

        # Create OK and Cancel buttons
        self.ok_button = wx.Button(self.panel, label="OK")
        self.cancel_button = wx.Button(self.panel, label="Cancel")

        # Bind events to buttons
        self.ok_button.Bind(wx.EVT_BUTTON, self.on_ok)
        self.cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)

        # Set up the layout using a box sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        entries = wx.BoxSizer(wx.VERTICAL)
        entries.Add(wx.StaticText(self.panel, label="Enter old password:"), 0, wx.LEFT | wx.ALL)

        old_password_sizer = wx.BoxSizer(wx.HORIZONTAL)
        old_password_sizer.Add(self.old_password_ctrl, 0, wx.CENTER | wx.ALL, 5)
        self.old_pass_icon = wx.StaticBitmap(self.panel, wx.ID_ANY, self.hidden_bitmap)
        self.old_pass_icon.name = "old"
        old_password_sizer.Add(self.old_pass_icon)
        entries.Add(old_password_sizer)

        entries.AddSpacer(2)
        entries.Add(wx.StaticText(self.panel, label="Enter new password:"), 0, wx.LEFT | wx.ALL)

        new_password_sizer = wx.BoxSizer(wx.HORIZONTAL)
        new_password_sizer.Add(self.new_password_ctrl, 0, wx.CENTER | wx.ALL, 5)
        self.new_pass_icon = wx.StaticBitmap(self.panel, wx.ID_ANY, self.hidden_bitmap)
        self.new_pass_icon.name = "new"
        new_password_sizer.Add(self.new_pass_icon)
        entries.Add(new_password_sizer)

        entries.AddSpacer(2)
        entries.Add(wx.StaticText(self.panel, label="Confirm password:"), 0, wx.LEFT | wx.ALL)

        con_password_sizer = wx.BoxSizer(wx.HORIZONTAL)
        con_password_sizer.Add(self.confirm_password_ctrl, 0, wx.CENTER | wx.ALL, 5)
        self.con_pass_icon = wx.StaticBitmap(self.panel, wx.ID_ANY, self.hidden_bitmap)
        self.con_pass_icon.name = "con"
        con_password_sizer.Add(self.con_pass_icon)
        entries.Add(con_password_sizer)

        entries.AddSpacer(5)
        sizer.Add(entries, 0, wx.CENTER | wx.ALL)

        buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        buttons_sizer.Add(self.ok_button, 0, wx.ALL)
        buttons_sizer.AddSpacer(10)
        buttons_sizer.Add(self.cancel_button, 0, wx.ALL)
        buttons_sizer.AddSpacer(15)

        sizer.Add(buttons_sizer, 0, wx.ALIGN_RIGHT)

        self.old_pass_icon.Bind(wx.EVT_LEFT_DOWN, self.change_visibility)
        self.new_pass_icon.Bind(wx.EVT_LEFT_DOWN, self.change_visibility)
        self.con_pass_icon.Bind(wx.EVT_LEFT_DOWN, self.change_visibility)

        self.panel.SetSizerAndFit(sizer)

    def change_visibility(self, event):
        # Get the current position and size of the existing text control
        ctrls = {"old": self.old_password_ctrl, "new": self.new_password_ctrl, "con": self.confirm_password_ctrl}
        name = getattr(event.GetEventObject(), 'name', None)
        open_or_closed = self.hidden_bitmap if not self.is_showing_password else self.shown_bitmap

        if name in ctrls:
            ctrl = ctrls[name]

            position = ctrl.GetPosition()
            size = ctrl.GetSize()

            # Create a new text control with the updated style
            new_style = wx.TE_PASSWORD if not self.is_showing_password else wx.TE_PROCESS_ENTER
            new_textctrl = wx.TextCtrl(self.panel, pos=position, size=size, style=new_style)

            # Copy the text from the existing text control to the new one
            new_textctrl.SetValue(ctrl.GetValue())

            # Update the reference to the new text control
            if name == "old":
                self.old_pass_icon.SetBitmap(open_or_closed)
                self.panel.GetSizer().Replace(self.old_password_ctrl, new_textctrl)
                self.old_password_ctrl.Destroy()
                self.old_password_ctrl = new_textctrl
            elif name == "new":
                self.new_pass_icon.SetBitmap(open_or_closed)
                self.panel.GetSizer().Replace(self.new_password_ctrl, new_textctrl)
                self.new_password_ctrl.Destroy()
                self.new_password_ctrl = new_textctrl
            else:
                self.con_pass_icon.SetBitmap(open_or_closed)
                self.panel.GetSizer().Replace(self.confirm_password_ctrl, new_textctrl)
                self.confirm_password_ctrl.Destroy()
                self.confirm_password_ctrl = new_textctrl

            self.is_showing_password = not self.is_showing_password

    def GetValues(self):
        return [self.old_password_ctrl.GetValue(), self.new_password_ctrl.GetValue(),
                self.confirm_password_ctrl.GetValue()]

    def on_ok(self, event):
        self.EndModal(wx.ID_OK)

    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)


if __name__ == '__main__':
    app = wx.App()
    frame1 = MyFrame(comm="")
    app.MainLoop()
