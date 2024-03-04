class ClassSettings:
    def __init__(self):
        self.SERVERPORT = 1234
        self.SERVERIP = "192.168.4.75"
        self.USER_FILES_PATH = r"D:\!ReefGold\goldrive_code\UserGraphics".replace("\\", '/')
        self.SERVER_FILES_PATH = r"D:\!ReefGold\users_files".replace("\\", '/')
        self.USER_PROFILE_PHOTOS = r"D:\!ReefGold\user_profile_photos".replace('\\', '/')


class HomeSettings():
    def __init__(self):
        self.SERVERPORT = 1234
        self.SERVERIP = "10.0.0.12"
        self.USER_FILES_PATH = r"C:\Users\reefg\PycharmProjects\goldrive_code\UserGraphics".replace("\\", '/')
        self.SERVER_FILES_PATH = r"C:\Users\reefg\user_files".replace("\\", '/')
        self.USER_PROFILE_PHOTOS = r"C:\Users\reefg\user_profile_photos".replace('\\', '/')


class CurrentSettings:
    settings = HomeSettings()
    SERVERPORT = settings.SERVERPORT
    SERVERIP = settings.SERVERIP
    USER_FILES_PATH = settings.USER_FILES_PATH
    SERVER_FILES_PATH = settings.SERVER_FILES_PATH
    USER_PROFILE_PHOTOS = settings.USER_PROFILE_PHOTOS

