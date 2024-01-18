import os


def rename_file(path, new_name):
    if os.path.exists(path):
        os.path.dirname(path)
        os.rename(path, os.path.dirname(path) + '/' + new_name)
    else:
        print("Isn't a file")


def delete_file(path):
    if os.path.exists(path):
        os.remove(path)
    else:
        print("Isn't a file")


if __name__ == '__main__':
    rename_file(r"C:\Users\talmid\Desktop\word.lnk", r"Word.lnk")
    delete_file(r"rD:\!ReefGold\Project_code_start\text")
