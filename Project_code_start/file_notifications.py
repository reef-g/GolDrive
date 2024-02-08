import sys
import os
import win32file
import shutil
from pathlib import Path
import time


FILE_LIST_DIRECTORY = 0x0001
FILE_NOTIFY_CHANGE_FILE_NAME = 0x0001
FILE_NOTIFY_CHANGE_DIR_NAME = 0x0002
FILE_NOTIFY_CHANGE_LAST_WRITE = 0x0010
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
OPEN_EXISTING = 3

file_actions = {
    0x00000001:
        "Added",
    0x00000002:
        "Removed",
    0x00000003:
        "Modified",
    0x00000004:
        "Renamed old name",
    0x00000005:
        "Renamed new name"
}

image_types = ["apng", "avif", "gif", "jpg", "jpeg", "jfif", "pjpeg", "pjp", "png", "svg", "webp", "bmp", "ico", "cur",
               "tif", "tiff"]

if __name__ == '__main__':
    path_to_watch = input("Enter directory to watch: ")
    path_to_copy = input("Enter directory to copy images to: ")

    directory_handle = win32file.CreateFileW(
        path_to_watch,
        FILE_LIST_DIRECTORY,  # No access (required for directories)
        win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE | win32file.FILE_SHARE_DELETE,
        None,
        OPEN_EXISTING,
        FILE_FLAG_BACKUP_SEMANTICS,
        None
    )
    if directory_handle == -1:
        print("Error opening directory")
    else:
        while True:
            result = win32file.ReadDirectoryChangesW(
                directory_handle,
                4096,
                True,  # Watch subtree
                FILE_NOTIFY_CHANGE_LAST_WRITE | FILE_NOTIFY_CHANGE_FILE_NAME,
                None
            )

            actions = ", ".join(map(lambda action: f"{file_actions[action[0]].title()} {action[1]}", result))
            print(actions)

            if file_actions[result[0][0]] == "Added" and any(result[0][1].endswith("." + end) for end in image_types):
                time.sleep(0.02)
                source = f"{path_to_watch}\\{result[0][1]}"
                target = f"{path_to_copy}\\{result[0][1]}"

                shutil.copyfile(source, target)
