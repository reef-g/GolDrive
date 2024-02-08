import psutil
import time
import subprocess
import shlex
import winreg


def get_default_windows_app(suffix):
    print(suffix)
    class_root = winreg.QueryValue(winreg.HKEY_CLASSES_ROOT, suffix)
    with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r'{}\shell\open\command'.format(class_root)) as key:
        command = winreg.QueryValueEx(key, '')[0]
        return shlex.split(command)[0]


def get_all_pid(process_name):
    current = []
    for p in psutil.process_iter():
        if p.name() == process_name: #"notepad.exe":
            current.append(p.pid)

    return current


def wait_until(process_name, file_Path):
    ls1 = get_all_pid(process_name)
    print(ls1)
    subprocess.Popen(['start', file_Path], shell=True)
    time.sleep(2)
    ls2 = get_all_pid(process_name)
    print(ls2)

    new_pid = set(ls2)-set(ls1)
    pid = list(new_pid)[0]

    while psutil.pid_exists(pid):
        pass

    print("is closed")


def get_process_name(file_path):
    suffix = file_path[file_path.rfind("."):]
    return get_default_windows_app(suffix)


if __name__ == '__main__':
    #wait_until("Notepad.exe", r"D:\!ReefGold\test.txt")
    #wait_until("WINWORD.EXE", r"D:\!ReefGold\pictures\testw.docx")
    wait_until("python.exe", "D:\!ReefGold\Project_code_start\encryption.py")

    file_path = r"D:\!ReefGold\test.txt"
    #file_app = get_process_name(file_path)

    #print(file_app)

    #file_path = r"D:\!ReefGold\pictures\testw.docx"
    #file_app = get_process_name(file_path)

    #print(file_app)




