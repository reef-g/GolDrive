import win32file
import subprocess
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


def monitor(path_to_watch, q):
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

            for action in result:
                if file_actions[action[0]] == "Modified":
                    q.put("Changed")


if __name__ == '__main__':
    path = input("Enter file: ")
    while True:
        print(monitor(path,))
        print("asdasd")

