import win32file
import subprocess
import queue
import psutil

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

default_for_type = {'txt': 'Notepad.exe',
                    'docx': 'WINWORD.EXE',
                    'pptx': 'POWERPNT.EXE',
                    'ppt': 'POWERPNT.EXE',
                    'zip': 'explorer.exe',
                    **{img: 'Microsoft.Photos.exe' for img in image_types},
                    'xlsx': 'EXCEL.EXE'}


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
            try:
                result = win32file.ReadDirectoryChangesW(
                    directory_handle,
                    4096,
                    True,  # Watch subtree
                    FILE_NOTIFY_CHANGE_LAST_WRITE | FILE_NOTIFY_CHANGE_FILE_NAME,
                    None
                )

                for action in result:
                    if file_actions[action[0]] == "Modified" and not action[1].startswith('~'):
                        q.put("Changed")
            except Exception as e:
                break



def get_all_pid(process_name):
    current = []
    for p in psutil.process_iter():
        if p.name() == process_name:
            current.append(p.pid)

    return current


def wait_until(file_path, q):
    file_extension = file_path[file_path.rfind('.') + 1:]

    if file_extension in default_for_type:
        process_name = default_for_type[file_extension]
    else:
        process_name = 'Notepad.exe'

    ls1 = get_all_pid(process_name)
    subprocess.Popen(['start', file_path], shell=True)

    while True:
        ls2 = get_all_pid(process_name)
        if ls2 != ls1:
            break

    new_pid = set(ls2) - set(ls1)
    pid = list(new_pid)[0]

    while psutil.pid_exists(pid):
        pass

    q.put("Finished")


if __name__ == '__main__':
    Q = queue.Queue()

    # file_path = r"T:\public\reefcheck\check.docx"
    # file_extension = file_path[file_path.rfind('.')+1:]
    #
    # if file_extension in default_for_type:
    #     process_name = default_for_type[file_extension]
    # else:
    #     process_name = 'Notepad.exe'
    #
    # print(process_name)
    #
    # wait_until(process_name, file_path, q)
