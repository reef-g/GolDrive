import os


def rename_file(path, new_name):
    status = 1
    if os.path.exists(path):
        try:
            os.path.dirname(path)
            os.rename(path, os.path.dirname(path) + '/' + new_name)
            status = 0
        except Exception as e:
            print(str(e))
    else:
        print("Isn't a file")

    return status


def delete_file(path):
    status = 0
    if os.path.exists(path):
        try:
            os.remove(path)

            print("Deleted file at - " + path)
        except Exception as e:
            print(str(e))
            status = 1
    else:
        status = 2

    return status


def download_file(path):
    status = 1

    if os.path.exists(path):
        try:
            with open(path, 'rb') as f:
                data = f.read()
            status = 0
        except Exception as e:
            print(str(e))
    else:
        print("Isn't a file")

    return status, data





if __name__ == '__main__':
    rename_file(r"C:\Users\talmid\Desktop\word.lnk", r"Word.lnk")
    delete_file(r"rD:\!ReefGold\Project_code_start\text")
