#!/usr/bin/python
# -*- coding: <<encoding>> -*-
# -------------------------------------------------------------------------------
#   <<project>>
#
# -------------------------------------------------------------------------------

import wx

from PIL import Image, ImageDraw
import wx, wx.html
import sys
import os
import numpy as np


def set_profile_picture(pic):
    if not os.path.isfile(f"pro_{pic}"):
        with open(pic, "rb") as file:
            data = file.read()
        with open(f"pro_{pic}", "wb") as profile:
            profile.write(data)
        resize_profile(f"pro_{pic}")
        make_circle_profile(f"pro_{pic}")


def make_circle_profile(profile_picture_path):
    """
        Make a circle profile image
    """
    # Open the input image as numpy array, convert to RGB
    imgae = Image.open(profile_picture_path).convert("RGB")
    npImage = np.array(imgae)
    height, weight = imgae.size
    # Create same size alpha layer with circle
    alpha = Image.new('L', imgae.size, 0)
    draw = ImageDraw.Draw(alpha)
    #draw.pieslice([0, 0, height, weight], 0, 360, fill=255)
    draw.pieslice([0, 0, height, weight], 0, 360, fill=255)
    # Convert alpha Image to numpy array
    npAlpha = np.array(alpha)
    # Add alpha layer to RGB
    npImage = np.dstack((npImage, npAlpha))
    # Save with alpha
    Image.fromarray(npImage).save(profile_picture_path)

def resize_profile(profile_picture_path):
    """
        Resize profile picture
    """
    #size = 138, 137
    size = 100, 200
    # Open picture
    im = Image.open(profile_picture_path).convert("RGB")
    # Change the size and saved it
    im.thumbnail(size, Image.ANTIALIAS)
    im.save(profile_picture_path, "PNG")

aboutText = """<p>Sorry, there is no information about this program. It is
running on version %(wxpy)s of <b>wxPython</b> and %(python)s of <b>Python</b>.
See <a href="http://wiki.wxpython.org">wxPython Wiki</a></p>"""


class HtmlWindow(wx.html.HtmlWindow):
    def __init__(self, parent, id, size=(800, 600)):
        wx.html.HtmlWindow.__init__(self, parent, id, size=size)
        if "gtk2" in wx.PlatformInfo:
            self.SetStandardFonts()

    def OnLinkClicked(self, link):
        wx.LaunchDefaultBrowser(link.GetHref())


class AboutBox(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(self, None, -1, "About <<project>>",
                           style=wx.DEFAULT_DIALOG_STYLE | wx.THICK_FRAME | wx.RESIZE_BORDER |
                                 wx.TAB_TRAVERSAL)
        hwin = HtmlWindow(self, -1, size=(400, 200))
        vers = {}
        vers["python"] = sys.version.split()[0]
        vers["wxpy"] = wx.VERSION_STRING
        hwin.SetPage(aboutText % vers)
        btn = hwin.FindWindowById(wx.ID_OK)
        irep = hwin.GetInternalRepresentation()
        hwin.SetSize((irep.GetWidth() + 25, irep.GetHeight() + 10))
        self.SetClientSize(hwin.GetSize())
        self.CentreOnParent(wx.BOTH)
        self.SetFocus()


class Frame(wx.Frame):
    def __init__(self, title):
        wx.Frame.__init__(self, None, title=title, pos=(150, 150), size=(800, 400))
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.SetBackgroundColour(wx.WHITE)

        menuBar = wx.MenuBar()
        self.profile_picture_path = None
        menu = wx.Menu()
        m_exit = menu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Close window and exit program.")
        self.Bind(wx.EVT_MENU, self.OnClose, m_exit)
        menuBar.Append(menu, "&File")
        menu = wx.Menu()
        m_about = menu.Append(wx.ID_ABOUT, "&About", "Information about this program")
        self.Bind(wx.EVT_MENU, self.OnAbout, m_about)
        menuBar.Append(menu, "&Help")
        self.SetMenuBar(menuBar)

        self.statusbar = self.CreateStatusBar()

        panel = wx.Panel(self)
        box = wx.BoxSizer(wx.VERTICAL)

        m_text = wx.StaticText(panel, -1, "Hello World!")
        m_text.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        m_text.SetSize(m_text.GetBestSize())
        box.Add(m_text, 0, wx.ALL, 10)

        m_close = wx.Button(panel, wx.ID_CLOSE, "Close")
        m_close.Bind(wx.EVT_BUTTON, self.OnClose)
        box.Add(m_close, 0, wx.ALL, 10)

        profile_picture = r"D:\!ReefGold\Project_code_start\Graphics\pro_bg.png"

        try:
        # Open the new picture and calculate the position
            im = Image.open(profile_picture)
            width, height = im.size
            im.close()
            if height > 100:
                y = 10
            else:
                y = 40
        except Exception as e:
            print(str(e))

        #review the profile picture
        image = wx.Bitmap(f"{profile_picture}", wx.BITMAP_TYPE_PNG)
        im = wx.ImageFromBitmap(image)
        im.Scale(150, 150, wx.IMAGE_QUALITY_HIGH)
        image = wx.Bitmap(im)

        profile_button = wx.BitmapButton(self, 1, image, name="Profile", pos=(400, y), style=wx.NO_BORDER)

        profile_button.SetBackgroundColour(wx.WHITE)

        panel.SetSizer(box)
        panel.Layout()


    def OnClose(self, event):
        dlg = wx.MessageDialog(self,
                               "Do you really want to close this application?",
                               "Confirm Exit", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            self.Destroy()

    def OnAbout(self, event):
        dlg = AboutBox()
        dlg.ShowModal()
        dlg.Destroy()




    def make_profile_pic(self, pic_name):
        with open(self.profile_picture_path, "wb") as profile:
            profile.write(data)
        # Edit the profile picture (resize and circle)
        self.resize_profile()
        self.make_circle_profile()



set_profile_picture("bg.png")
app = wx.App(redirect=True)  # Error messages go to popup window
top = Frame("profile Test")
top.Show()
app.MainLoop()