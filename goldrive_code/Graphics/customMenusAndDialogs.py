from settings import CurrentSettings as Settings
import wx


class FileMenuFeatures(wx.Menu):
    def __init__(self, parent, name):
        """
        :param parent: parent panel
        :param name: name of what the user clicked on
        """
        super(FileMenuFeatures, self).__init__()

        image_types = ["apng", "avif", "gif", "jpg", "jpeg", "jfif", "pjpeg", "pjp", "png", "svg", "webp", "bmp", "ico",
                       "cur", "tif", "tiff"]

        self.parent = parent
        self.name = name

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
        """
        :param event: event
        :return: starts the correct function based on what the user clicked
        """
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


class FolderMenuFeatures(wx.Menu):
    def __init__(self, parent, name):
        """
        :param parent: parent panel
        :param name: name of what the user clicked on
        """
        super(FolderMenuFeatures, self).__init__()

        self.parent = parent
        self.name = name

        static_text_item = wx.MenuItem(self, 0, name)
        # Make it non-selectable
        static_text_item.Enable(False)
        self.Append(static_text_item)

        self.AppendSeparator()

        self.Append(wx.MenuItem(self, -1, 'Open'))
        self.Append(wx.MenuItem(self, -1, 'Delete folder'))
        self.Append(wx.MenuItem(self, -1, 'Rename folder'))
        self.Append(wx.MenuItem(self, -1, 'Zip folder'))

        self.AppendSeparator()

        self.Append(wx.MenuItem(self, -1, "Cancel"))

        # Bind the menu item click event
        self.Bind(wx.EVT_MENU, self.on_menu_item_click)

    def on_menu_item_click(self, event):
        """
        :param event: event
        :return: starts the according function to what the user pressed on
        """
        clicked_item_id = event.GetId()
        clicked_item = self.FindItemById(clicked_item_id)

        item = clicked_item.GetItemLabelText()
        if item == "Open":
            self.parent.chose_dir(self.name)
        elif item == "Delete folder":
            self.parent.delete_file_request(self.name)
        elif item == "Rename folder":
            self.parent.rename_file_request(self.name)
        elif item == "Zip folder":
            self.parent.zip_folder_request(self.name)


class UserMenuFeatures(wx.Menu):
    def __init__(self, parent, show_back):
        """
        :param parent: parent panel
        :param show_back: show go back flag
        """
        super(UserMenuFeatures, self).__init__()

        self.parent = parent

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
        """
        :param event: event
        :return: starts the according function to what the user pressed on
        """
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


class ProfileSettingsMenu(wx.Menu):
    def __init__(self, parent):
        """
        :param parent: parent panel
        """
        super(ProfileSettingsMenu, self).__init__()

        self.parent = parent

        self.Append(wx.MenuItem(self, -1, 'Change profile photo'))
        self.Append(wx.MenuItem(self, -1, 'Clear profile photo'))

        self.AppendSeparator()

        self.Append(wx.MenuItem(self, -1, "Cancel"))

        # Bind the menu item click event
        self.Bind(wx.EVT_MENU, self.on_menu_item_click)

    def on_menu_item_click(self, event):
        """
        :param event: event
        :return: strats the according function to what the user clicked on
        """
        item_id = event.GetId()
        clicked_item = self.FindItemById(item_id)

        item = clicked_item.GetItemLabelText()
        if item == "Change profile photo":
            self.parent.change_photo_request(wx.CommandEvent)
        elif item == "Clear profile photo":
            self.parent.delete_photo_request(wx.CommandEvent)


class ChangePasswordDialog(wx.Dialog):
    def __init__(self, parent, title):
        """
        :param parent: parent panel
        :param title: title of the dialog
        """
        super(ChangePasswordDialog, self).__init__(parent, title=title, size=(388, 230), pos=(960-174, 540-115))

        self.panel = wx.Panel(self)

        self.is_showing_password = False

        hidden_path = f"{Settings.USER_FILES_PATH}\\hidden-eye.png"
        open_path = f"{Settings.USER_FILES_PATH}\\open-eye.png"

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
        """
        :param event: event
        :return: changes if you can see the password entered or not
        """
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
        """
        :return: the values entered
        """
        return [self.old_password_ctrl.GetValue(), self.new_password_ctrl.GetValue(),
                self.confirm_password_ctrl.GetValue()]

    def on_ok(self, event):
        """
        :param event: event on click
        :return: ends the event with wx.ID_OK id
        """
        self.EndModal(wx.ID_OK)

    def on_cancel(self, event):
        """
        :param event: event on click
        :return: ends the event with wx.ID_CANCEL id
        """
        self.EndModal(wx.ID_CANCEL)


class ConfirmMailDialog(wx.Dialog):
    def __init__(self, parent, title):
        """
        :param parent: panel parent
        :param title: title of the dialog
        """
        super(ConfirmMailDialog, self).__init__(parent, title=title, size=(388, 150), pos=(960 - 174, 540 - 115))

        self.panel = wx.Panel(self)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.AddSpacer(2)

        label = wx.StaticText(self.panel, label="Enter the 6-digit code sent to your mail:")
        self.sizer.Add(label, 0, wx.ALL, 5)

        self.text_ctrl = wx.TextCtrl(self.panel, size=(340, -1))
        self.sizer.Add(self.text_ctrl, 0, wx.CENTER)

        self.remember_checkbox = wx.CheckBox(self.panel, label="Don't ask again on this computer.")
        self.sizer.Add(self.remember_checkbox, 0, wx.ALL, 5)

        # Create OK and Cancel buttons
        self.ok_button = wx.Button(self.panel, label="OK")
        self.cancel_button = wx.Button(self.panel, label="Cancel")

        # Bind events to buttons
        self.ok_button.Bind(wx.EVT_BUTTON, self.on_ok)
        self.cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)

        buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        buttons_sizer.Add(self.ok_button, 0, wx.ALL)
        buttons_sizer.AddSpacer(10)
        buttons_sizer.Add(self.cancel_button, 0, wx.ALL)
        buttons_sizer.AddSpacer(15)

        self.sizer.Add(buttons_sizer, 0, wx.ALIGN_RIGHT)

        self.panel.SetSizerAndFit(self.sizer)

    def GetValues(self):
        """
        :return: get the values entered
        """
        return [self.text_ctrl.GetValue(), self.remember_checkbox.GetValue()]

    def on_ok(self, event):
        """
        :param event: event on click
        :return: ends the event with wx.ID_OK id
        """
        self.EndModal(wx.ID_OK)

    def on_cancel(self, event):
        """
        :param event: event on click
        :return: ends the event with wx.ID_CANCEL id
        """
        self.EndModal(wx.ID_CANCEL)


class ForgotPasswordDialog(wx.Dialog):
    def __init__(self, parent, title):
        """
        :param parent: panel parent
        :param title: title of the dialog
        """
        super(ForgotPasswordDialog, self).__init__(parent, title=title, size=(388, 185), pos=(960-174, 540-115))

        self.panel = wx.Panel(self)

        self.is_showing_password = False

        hidden_path = f"{Settings.USER_FILES_PATH}\\hidden-eye.png"
        open_path = f"{Settings.USER_FILES_PATH}\\open-eye.png"

        self.hidden_bitmap = wx.Bitmap(hidden_path, wx.BITMAP_TYPE_ANY)
        self.shown_bitmap = wx.Bitmap(open_path, wx.BITMAP_TYPE_ANY)

        # Create two text boxes
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

        self.new_pass_icon.Bind(wx.EVT_LEFT_DOWN, self.change_visibility)
        self.con_pass_icon.Bind(wx.EVT_LEFT_DOWN, self.change_visibility)

        self.panel.SetSizerAndFit(sizer)

    def change_visibility(self, event):
        """
        :param event: event
        :return: changes if you can see the password entered or not
        """
        # Get the current position and size of the existing text control
        ctrls = {"new": self.new_password_ctrl, "con": self.confirm_password_ctrl}
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
            if name == "new":
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
        """
        :return: the values entered
        """
        return [self.new_password_ctrl.GetValue(), self.confirm_password_ctrl.GetValue()]

    def on_ok(self, event):
        """
        :param event: event on click
        :return: ends the event with wx.ID_OK id
        """
        self.EndModal(wx.ID_OK)

    def on_cancel(self, event):
        """
        :param event: event on click
        :return: ends the event with wx.ID_CANCEL id
        """
        self.EndModal(wx.ID_CANCEL)


class TransparentText(wx.StaticText):
    def __init__(self, parent, id=wx.ID_ANY, label='', pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.TRANSPARENT_WINDOW, name='transparenttext'):
        """
        :param parent: panel parent
        :param label: label of the text
        :param style: style of the text
        :param name: name of the text object
        """
        wx.StaticText.__init__(self, parent, id, label,
                               pos, size, style, name)

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)

    def on_paint(self, event):
        """
        :param event: event of on paint
        :return: paints the text with transparent background
        """
        bdc = wx.PaintDC(self)
        dc = wx.GCDC(bdc)

        font_face = self.GetFont()
        font_color = self.GetForegroundColour()

        dc.SetFont(font_face)
        dc.SetTextForeground(font_color)
        dc.DrawText(self.GetLabel(), 0, 0)

    def on_size(self, event):
        """
        :param event: event of on size
        :return: refreshes when screen changes size
        """
        self.Refresh()
        event.Skip()
