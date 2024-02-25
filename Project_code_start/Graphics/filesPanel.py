import wx
import wx.lib.scrolledpanel
import io
import os
from pubsub import pub
from .userPanel import UserPanel
from .customMenusAndDialogs import UserMenuFeatures, FileMenuFeatures
from settings import CurrentSettings as Settings
from ClientFiles import clientProtocol


class MyDropTarget(wx.DropTarget):
    def __init__(self, panel):
        wx.DropTarget.__init__(self)
        self.panel = panel

        self.name = wx.TextDataObject()
        self.SetDataObject(self.name)

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
        self.progressDialog = None
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
        self.scroll_panel.Bind(wx.EVT_RIGHT_DOWN, self.show_user_options_menu)

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

    def show_user_options_menu(self, event):
        flag = True
        if self.curPath == "":
            flag = False
        self.PopupMenu(UserMenuFeatures(self, flag))

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
            self.PopupMenu(FileMenuFeatures(self, name=obj.GetName()))

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
        pass

        if percent == 100:
            self.progressDialog.Destroy()

    def show_settings(self, event):
        settings = UserPanel(self.parent, self.frame, self.comm, self.parent.files_comm)

        self.parent.change_screen(self, settings)