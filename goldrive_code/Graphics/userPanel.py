import wx
from pubsub import pub
import io
from ClientFiles import clientProtocol
from .customMenusAndDialogs import ChangePasswordDialog, ProfileSettingsMenu, TransparentText
from settings import CurrentSettings as Settings


class UserPanel(wx.Panel):
    def __init__(self, parent, frame, comm, files_comm):
        wx.Panel.__init__(self, parent, pos=wx.DefaultPosition, size=(1920, 1080), style=wx.SIMPLE_BORDER)
        self.frame = frame
        self.comm = comm
        self.files_comm = files_comm
        self.parent = parent

        button_font = wx.Font(15, wx.DEFAULT, wx.NORMAL, wx.BOLD)

        self.selected_path = ""
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.AddSpacer(2)

        self.title = TransparentText(self, -1, label="SETTINGS")
        font = wx.Font(65, wx.DECORATIVE, wx.NORMAL, wx.NORMAL, 0, "High tower text")
        self.title.SetFont(font)
        self.sizer.Add(self.title, 0, wx.CENTER)

        image = wx.Image(io.BytesIO(self.parent.profilePhoto), wx.BITMAP_TYPE_ANY)
        image.Rescale(108, 108)

        # Convert the wx.Image to a wx.Bitmap
        bitmap = wx.Bitmap(image)
        self.settings_img = wx.BitmapButton(self, wx.ID_ANY, bitmap)

        self.titleSizer = wx.BoxSizer(wx.VERTICAL)
        self.usernameTitleSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.emailTitleSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.imageSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.userAndImageSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.usernameTitle = TransparentText(self, -1, label=f"Username: {self.parent.username}")
        self.emailTitle = TransparentText(self, -1, label=f"Email: {self.parent.email}")
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
        self.loginButton.SetFont(button_font)
        self.filesButton = wx.Button(self, label="BACK TO FILES")
        self.filesButton.SetFont(button_font)
        self.changeEmailButton = wx.Button(self, label="CHANGE EMAIL")
        self.changeEmailButton.SetFont(button_font)
        self.changePasswordButton = wx.Button(self, label="CHANGE PASSWORD")
        self.changePasswordButton.SetFont(button_font)
        self.changePhotoButton = wx.Button(self, label="CHANGE PROFILE PHOTO")
        self.changePhotoButton.SetFont(button_font)
        self.deletePhotoButton = wx.Button(self, label="DELETE PROFILE PHOTO")
        self.deletePhotoButton.SetFont(button_font)

        self.loginButton.Bind(wx.EVT_BUTTON, self.login_control)
        self.filesButton.Bind(wx.EVT_BUTTON, self.files_control)
        self.changeEmailButton.Bind(wx.EVT_BUTTON, self.change_email_request)
        self.changePasswordButton.Bind(wx.EVT_BUTTON, self.change_password_request)
        self.changePhotoButton.Bind(wx.EVT_BUTTON, self.change_photo_request)
        self.deletePhotoButton.Bind(wx.EVT_BUTTON, self.delete_photo_request)
        self.settings_img.Bind(wx.EVT_RIGHT_DOWN, self.show_settings_menu)

        self.buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.buttons_sizer.Add(self.filesButton)
        self.buttons_sizer.AddSpacer(20)
        self.buttons_sizer.Add(self.loginButton)
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

        self.Bind(wx.EVT_PAINT, self.PaintBackgroundImage)

        self.Hide()

    def PaintBackgroundImage(self, evt):
        dc = wx.PaintDC(self)

        bmp = wx.Bitmap(rf"{Settings.USER_FILES_PATH}\bg.png")
        dc.DrawBitmap(bmp, 0, 0)

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

    def show_settings_menu(self, event):
        self.PopupMenu(ProfileSettingsMenu(self))