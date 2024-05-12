import wx
import wx.lib.scrolledpanel
import io
import os
from pubsub import pub
import time
from .userPanel import UserPanel
from .customMenusAndDialogs import UserMenuFeatures, FileMenuFeatures, FolderMenuFeatures, TransparentText
from settings import CurrentSettings as Settings
from ClientFiles import clientProtocol


class MyDropTarget(wx.DropTarget):
    def __init__(self, panel):
        """
        :param panel: parent panel
        """
        wx.DropTarget.__init__(self)
        self.panel = panel

        self.name = wx.TextDataObject()
        self.SetDataObject(self.name)

        self.data = wx.TextDataObject()
        self.SetDataObject(self.data)

    def OnDragOver(self, x, y, default):
        """
        :param x: x position
        :param y: y position
        :param default: default cursor to show
        :return: which cursor to show depending on where the mouse is
        """
        # Check if the cursor is above an image using the panel's method
        cursor_to_show = wx.DragNone
        isAbove, name = self.panel.is_cursor_above_image()

        if isAbove:
            # Visual feedback for a valid drop location
            cursor_to_show = wx.DragCopy
            self.data = name

        return cursor_to_show

    def OnData(self, x, y, result):
        """
        :param x: x position
        :param y: y position
        :param result: is the drop ok
        :return: result
        """
        # Get the dropped data
        dragged_name = self.name.GetText()
        dropped_name = self.data.GetText()
        # Process the dropped data
        if dragged_name and dropped_name:
            self.panel.handle_dropped_item(dragged_name, dropped_name)

        return result


class FilesPanel(wx.Panel):
    def __init__(self, parent, frame, comm):
        """
        :param parent: panel parent
        :param frame: frame parent
        :param comm: comm object of user
        """
        wx.Panel.__init__(self, parent, pos=wx.DefaultPosition, size=(1920, 1080), style=wx.SIMPLE_BORDER)

        self.grid_sizer = None
        self.frame = frame
        self.comm = comm
        self.parent = parent

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        button_font = wx.Font(15, wx.DEFAULT, wx.NORMAL, wx.BOLD)

        self.title_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.title = TransparentText(self, -1)
        titlefont = wx.Font(60, wx.DECORATIVE, wx.NORMAL, wx.NORMAL, 0, "High tower text")
        self.title.SetFont(titlefont)

        self.title_sizer.Add(self.title)

        self.curPath = None
        self.pathBeforeSharedFiles = None
        self.copied_file = None
        self.progressDialog = None
        self.file_name = ""
        self.filesObj = {}

        self.scroll_panel = wx.lib.scrolledpanel.ScrolledPanel(self, -1, size=(1670, 800), style=wx.SIMPLE_BORDER)
        self.scroll_panel.SetupScrolling()
        self.scroll_panel.SetBackgroundColour("white")

        self.icons_and_files_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.icons_sizer = wx.BoxSizer(wx.VERTICAL)

        self.settings_img = wx.BitmapButton(self, wx.ID_ANY, wx.Bitmap(f"{Settings.USER_FILES_PATH}/Settings.png",
                                                                       wx.BITMAP_TYPE_ANY))
        tooltip = wx.ToolTip("Settings")
        self.settings_img.SetToolTip(tooltip)

        self.shared_files_img = wx.BitmapButton(self, wx.ID_ANY, wx.Bitmap(f"{Settings.USER_FILES_PATH}/Shared.png",
                                                                           wx.BITMAP_TYPE_ANY))
        tooltip = wx.ToolTip("Shared files")
        self.shared_files_img.SetToolTip(tooltip)

        self.shared_files_img.Bind(wx.EVT_BUTTON, self.show_shared_files)
        self.settings_img.Bind(wx.EVT_BUTTON, self.show_settings)

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
        self.login_button.SetFont(button_font)
        self.backButton = wx.Button(self, label="BACK")
        self.backButton.SetFont(button_font)
        self.uploadButton = wx.Button(self, label="UPLOAD FILE")
        self.uploadButton.SetFont(button_font)
        self.createDirButton = wx.Button(self, label="CREATE DIRECTORY")
        self.createDirButton.SetFont(button_font)
        self.pasteButton = wx.Button(self, label="PASTE")
        self.pasteButton.SetFont(button_font)

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
        pub.subscribe(self._upload_object, "zipFileOk")

        self.Layout()

        self.drop_target = MyDropTarget(self)
        self.SetDropTarget(self.drop_target)
        self.Bind(wx.EVT_PAINT, self.PaintBackgroundImage)

        self.Hide()

    def PaintBackgroundImage(self, evt):
        """
        :param evt: on paint event
        :return: showing the background image
        """
        dc = wx.PaintDC(self)

        bmp = wx.Bitmap(rf"{Settings.USER_FILES_PATH}/bg.png")
        dc.DrawBitmap(bmp, 0, 0)

    def change_settings_to_profile(self):
        """
        :return: changes the photo from the settings to the profile photo
        """
        image = wx.Image(io.BytesIO(self.parent.profilePhoto), wx.BITMAP_TYPE_ANY)
        image.Rescale(108, 108)

        # Convert the wx.Image to a wx.Bitmap
        bitmap = wx.Bitmap(image)

        self.settings_img.SetBitmap(bitmap)

    def show_user_options_menu(self, event):
        """
        :param event: on click event
        :return: showing user menu
        """
        flag = True
        if self.curPath == "":
            flag = False
        self.PopupMenu(UserMenuFeatures(self, flag))

    def start_drag(self, event):
        """
        :param event: on drag event
        :return: starts the drag event
        """
        # Start a drag-and-drop operation when an item is left-clicked
        item_text = event.GetEventObject()
        data = wx.TextDataObject(item_text.GetName())
        self.drop_target.name = data
        drop_source = wx.DropSource(item_text)
        drop_source.SetData(data)
        drop_source.DoDragDrop(wx.Drag_CopyOnly)

    def handle_dropped_item(self, item_dropped, dropped_to_item):
        """
        :param item_dropped: name of the item dropped
        :param dropped_to_item: name of the item dropped onto
        :return: requests to move the file a folder from the server
        """
        # Process the dropped item
        self.file_name = item_dropped
        src = f"{self.parent.username}/{self.curPath}/{item_dropped}".replace('//', '/')
        dst = f"{self.parent.username}/{self.curPath}/{dropped_to_item}".replace('//', '/')

        msg = clientProtocol.pack_move_file_folder_request(src, dst)
        self.comm.send(msg)

    def is_cursor_above_image(self):
        """
        :return: is the cursor above a directory image
        """
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
        """
        :param event: on click event
        :return: changes back to the login screen
        """
        self.parent.change_screen(self, self.parent.login)

    def _get_branches(self, branches):
        """
        :param branches: users branches from the server
        :return: updates the branches and shows them
        """
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
        """
        :param path: path of branch to show
        :return: shows the correct files on the screen
        """
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

        image_types = ["apng", "avif", "gif", "jpg", "jpeg", "jfif", "pjpeg", "pjp", "png", "svg", "webp", "bmp", "ico",
                       "cur", "tif", "tiff"]
        file_image_paths = {'txt': f"{Settings.USER_FILES_PATH}/text_icon.png",
                            **{img: f"{Settings.USER_FILES_PATH}/photo_icon.png" for img in image_types},
                            'zip': f"{Settings.USER_FILES_PATH}/zip_icon.png",
                            'docx': f"{Settings.USER_FILES_PATH}/docx_icon.png",
                            'doc': f"{Settings.USER_FILES_PATH}/docx_icon.png",
                            'pptx': f"{Settings.USER_FILES_PATH}/pptx_icon.png",
                            'ppt': f"{Settings.USER_FILES_PATH}/pptx_icon.png",
                            'pdf': f"{Settings.USER_FILES_PATH}/pdf_icon.png",
                            'xls': f"{Settings.USER_FILES_PATH}/xlsx_icon.png",
                            'xlsx': f"{Settings.USER_FILES_PATH}/xlsx_icon.png",
                            'default': f"{Settings.USER_FILES_PATH}/default_icon.png"}

        directory_image_path = f"{Settings.USER_FILES_PATH}/dirs_icon.png"

        # Add items with corresponding images to the grid sizer
        while dirs or files:
            dir_file_flag = False
            if dirs:
                item = dirs.pop(0)
                image_path = directory_image_path
                dir_file_flag = True
            elif files:
                item = files.pop(0)
                file_type = item[item.rfind('.')+1:]

                if file_type in file_image_paths:
                    image_path = file_image_paths[file_type]
                else:
                    image_path = file_image_paths['default']

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

            if dir_file_flag:
                item_text.Bind(wx.EVT_LEFT_DOWN, self.select_file)
                item_image.Bind(wx.EVT_LEFT_DOWN, self.select_file)
            else:
                item_text.Bind(wx.EVT_LEFT_DOWN, self.start_drag)
                item_image.Bind(wx.EVT_LEFT_DOWN, self.start_drag)

            item_text.Bind(wx.EVT_RIGHT_DOWN, self.select_file)
            item_image.Bind(wx.EVT_RIGHT_DOWN, self.select_file)

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
        """
        :param event: on click event
        :return: shows the correct menu if its a file or a folder
        """
        obj = event.GetEventObject()

        path_to_find = f"{self.curPath}/{obj.GetName()}".lstrip('/')

        if path_to_find not in self.filesObj and "@#$SHAREDFILES$#@" in path_to_find:
            split_path = self.curPath.split('/')
            path_to_find = '/'.join(split_path[split_path.index("@#$SHAREDFILES$#@"):]) + '/' + obj.GetName()

        # if left clicked a directory
        if self.filesObj[path_to_find][1] and event.GetEventType() == wx.EVT_LEFT_DOWN.typeId:
            self.chose_dir(obj.GetName())

        # if right clicked a directory
        elif self.filesObj[path_to_find][1]:
            self.PopupMenu(FolderMenuFeatures(self, name=obj.GetName()))

        # if right clicked a file
        else:
            self.PopupMenu(FileMenuFeatures(self, name=obj.GetName()))

    def chose_dir(self, name):
        """
        :param name: name of the directory chosen
        :return: showing the files inside the directory chosen
        """
        self.curPath += f"/{name}"
        self.curPath = self.curPath.lstrip('/')
        self.show_files(self.curPath)

    def back_dir(self, event):
        """
        :param event: on click event
        :return: going back a directory and showing the files
        """
        if self.curPath == "@#$SHAREDFILES$#@":
            self.curPath = self.pathBeforeSharedFiles
        else:
            self.curPath = "/".join(self.curPath.split('/')[:-1])

        self.show_files(self.curPath)

    def delete_file_request(self, name):
        """
        :param name: name of the item to delete
        :return: sends item delete request
        """
        dlg = wx.MessageDialog(self, 'Do you want to delete?', 'Confirmation', wx.YES_NO | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()

        if result == wx.ID_YES:
            self.file_name = name
            full_path = f"{self.parent.username}/{self.curPath}/{self.file_name}".lstrip("/")
            msg2send = clientProtocol.pack_delete_request(full_path)
            self.comm.send(msg2send)

    def _delete_obj(self):
        """
        :return: deletes the item from the branch
        """
        is_dir = self.filesObj[f"{self.curPath}/{self.file_name}".lstrip('/')][1]
        branches_to_remove = []

        for branch in self.branches:
            if branch[0] == self.curPath:
                if is_dir:
                    branch[1].remove(self.file_name)
                else:
                    branch[2].remove(self.file_name)

            elif branch[0].startswith(f"{self.curPath}/{self.file_name}/".lstrip('/')) or branch[0] == self.file_name\
                    and is_dir:
                branches_to_remove.append(branch)

        for branch_to_remove in branches_to_remove:
            self.branches.remove(branch_to_remove)

        self.show_files(self.curPath)
        self.parent.show_pop_up(f"Deleted {self.file_name} successfully.", "Success")

    def rename_file_request(self, name):
        """
        :param name: file to rename
        :return: send rename file request
        """
        dlg = wx.TextEntryDialog(self, f'Do you want to rename {name}?', 'Confirmation', '')
        result = dlg.ShowModal()
        dlg.Destroy()

        if result == wx.ID_OK:
            self.file_name = name
            full_path = f"{self.parent.username}/{self.curPath}/{name}".lstrip("/")
            msg2send = clientProtocol.pack_rename_file_request(full_path, dlg.GetValue())
            self.comm.send(msg2send)

    def _rename_obj(self, new_name):
        """
        :param new_name: new name of file to rename
        :return: renames item
        """
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

        for index in range(len(self.branches)):
            if not is_dir:
                break

            names_of_path = self.branches[index][0].split('/')
            if self.branches[index][0].startswith(f"{self.curPath}/{self.file_name}/".lstrip('/')) or \
                    self.branches[index][0] == self.file_name:

                index_of_name = names_of_path.index(self.file_name)
                names_of_path[index_of_name] = new_name
                branch = list(self.branches[index])
                name = '/'.join(names_of_path)
                branch[0] = name

                self.branches[index] = tuple(branch)

        self.show_files(self.curPath)
        self.parent.show_pop_up(f"Renamed {self.file_name} to {new_name} successfully.", "Success")

    def download_file_request(self, file_name):
        """
        :param file_name: name of file to download
        :return: sends download file request
        """
        base_name, file_extension = os.path.splitext(file_name)

        file_type = file_extension[1:].lower()

        type_descriptions = {
            'txt': 'Text files',
            'docx': 'Microsoft Word documents',
            'jpg': 'JPEG images',
            'png': 'PNG images',
        }

        # creating wild card for download type
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

            msg2send = clientProtocol.pack_download_file_request(f"{self.parent.username}/{self.curPath}/{file_name}",
                                                                 selected_path)
            self.parent.files_comm.send(msg2send)

        dlg.Destroy()

    def upload_file_request(self, event):
        """
        :param event: on click event
        :return: send upload file request
        """
        dlg = wx.FileDialog(self, "Choose a file", style=wx.DD_DEFAULT_STYLE)
        result = dlg.ShowModal()

        if result == wx.ID_OK:
            selected_path = dlg.GetPath().replace('\\', '/')
            self.parent.files_comm.send_file(12, selected_path, f"{self.parent.username}/{self.curPath}".rstrip('/'))

    def _upload_object(self, path):
        """
        :param path: path of file in the server
        :return: adds the file to the branches
        """
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
        """
        :param event: on click event
        :return: send create dir request
        """
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
                self.parent.show_pop_up(f"Can't create a folder with that name, please choose a different name.",
                                        "Error")

    def _create_dir(self):
        """
        :return: adding the directory to the path
        """
        for branch in self.branches:
            if branch[0] == self.curPath:
                branch[1].append(self.file_name)
                branch[1].sort()
                break

        self.branches.append((f'{self.curPath}/{self.file_name}'.lstrip('/'), [], []))
        self.show_files(self.curPath)

    def share_file_request(self, name):
        """
        :param name: file name to share
        :return: send share file request
        """
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
        """
        :param event: event on click
        :return: shows shared files
        """
        self.shared_files_img.Hide()
        self.pathBeforeSharedFiles = self.curPath
        self.curPath = "@#$SHAREDFILES$#@"
        self.show_files("@#$SHAREDFILES$#@")

    def _add_shared_file(self, path):
        """
        :param path: path to add
        :return: adds the file to the users shared files
        """
        user_who_shared, file = path.split('/')[0], path.split('/')[-1]
        for branch in self.branches:
            if branch[0] == "@#$SHAREDFILES$#@":
                if user_who_shared not in branch[1]:
                    branch[1].append(user_who_shared)
                    branch[1].sort()
                break

        # if the user who shared hasnent shared a file to this user before
        if not any(branch[0] == f"@#$SHAREDFILES$#@/{user_who_shared}" for branch in self.branches):
            self.branches.append((f'@#$SHAREDFILES$#@/{user_who_shared}', [], []))
            self.branches[-1][2].append(file)
            self.branches[-1][2].sort()

        # if the user has shared before add it to his branch
        else:
            for branch in self.branches:
                if branch[0] == f"@#$SHAREDFILES$#@/{user_who_shared}":
                    print(file)
                    branch[2].append(file)
                    branch[2].sort()

        self.show_files(self.curPath)

    def _move_file(self, path):
        """
        :param path: path to move the file from
        :return: moves the file from the path to where is needed
        """
        path = "/".join(path.split('/')[1::])

        for branch in self.branches:
            # removing the file from the old location
            if branch[0] == self.curPath:
                branch[2].remove(self.file_name)

            # adding the file to the new location
            if branch[0] == path:
                branch[2].append(self.file_name)

        self.show_files(self.curPath)
        self.parent.show_pop_up("Moved file successfully", "Success")

    def paste_file_request(self, event):
        """
        :param event: on click event
        :return: sends paste file request
        """
        if self.copied_file:
            src = f"{self.parent.username}/{self.copied_file}"
            dst = f"{self.parent.username}/{self.curPath}".rstrip('/')

            msg = clientProtocol.pack_paste_file_request(src, dst)
            self.comm.send(msg)
        else:
            self.parent.show_pop_up(f"Your clipboard is empty.", "Error")

    def _handle_paste_file(self):
        """
        :return: adds the file pasted to the users files
        """
        file_name = self.copied_file.split('/')[-1]
        text_to_show = "Pasted file successfully."

        for branch in self.branches:
            if branch[0] == self.curPath:
                if file_name not in branch[2]:
                    branch[2].append(file_name)
                    branch[2].sort()
                else:
                    text_to_show = "Updated file successfully."

        self.show_files(self.curPath)
        self.parent.show_pop_up(text_to_show, "Success")

    def open_file_request(self, name):
        """
        :param name: file name
        :return: sends file edit/open request
        """
        msg2send = clientProtocol.pack_open_file_request(
            f"{self.parent.username}/{self.curPath}/{name}".replace("//", '/')
        )
        self.parent.files_comm.send(msg2send)

    def _show_progress_bar(self, name, opcode):
        """
        :param name: name of file
        :param opcode: opcode of message
        :return: open the progress bar
        """

        msg = "Download" if opcode != "04" else "Upload" + " at 0%"

        self.progressDialog = wx.ProgressDialog(title=name, message=msg, maximum=100,
                                                style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE)

    def _change_progress_bar(self, percent, opcode):
        """
        :param percent: percent to show
        :param opcode: opcode of message
        :return: changes the progress bar
        """
        while not self.progressDialog:
            pass

        self.progressDialog.Update(percent, f"Download at {percent}%" if opcode != "04" else f"Upload at {percent}%")
        time.sleep(0.00001)

        if percent == 100:
            self.progressDialog.Destroy()

    def show_settings(self, event):
        """
        :param event: on click
        :return: shows settings
        """
        settings = UserPanel(self.parent, self.frame, self.comm, self.parent.files_comm)

        self.parent.change_screen(self, settings)

    def zip_folder_request(self, name):
        """
        :param name: file name
        :return: sends zip folder request
        """
        file_path = f"{self.curPath}/{name}".lstrip('/')
        full_path = f"{self.parent.username}/{file_path}"

        msg = clientProtocol.pack_zip_folder_request(full_path)
        self.comm.send(msg)
