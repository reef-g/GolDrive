import os


def unpack_message(msg):
    """
    :param msg: message to unpack
    :return: tuple with opcode and variables
    """

    opcode = msg[:2]
    data_from_msg = []
    msg = msg[2:]

    while len(msg) > 0:
        try:
            leng = msg[:2]
            msg = msg[2:]
            data_from_msg.append(msg[:int(leng)])
            msg = msg[int(leng):]
        except Exception as e:
            print("in unpack_message -", str(e))
            opcode = None
            break

    return opcode, data_from_msg


def pack_files_message(username):
    """
    :param username:
    :return: string with all files and directories of user in the drive
    """
    files_of_user = ""
    # the path to work at, will later to change to the person directory
    path = fr"D:\!ReefGold\Drive_files\\{username}"

    for (dirname, dirs, files) in os.walk(path):
        # removing the path so that its only the directories in the system and not from the server
        dirname = dirname[len(path) + 1::]

        # adding the length of the name and the name
        files_of_user += str(len(dirname)).zfill(2) + dirname

        # adding the length of the directories and the directories list
        dirs = '!'.join(dirs)
        files_of_user += str(len(dirs)).zfill(4) + dirs

        # adding the length of the files and the files list
        files = '@'.join(files)
        files_of_user += str(len(files)).zfill(4) + files

        files_of_user += '\n'

    return files_of_user


def pack_register_response(response):
    """
    :param response: response to send
    :return: opcode + response
    """
    return "01" + str(response)


def pack_login_response(response):
    """
    :param response: response to send
    :return: opcode + response
    """
    return "02" + str(response)


def pack_verify_check_response(response):
    """
    :param response: response to send
    :return: opcode + response
    """
    return "15" + str(response)


def pack_forgot_password_response(response):
    """
    :param response: response to send
    :return: opcode + response
    """
    return "07" + str(response)


def pack_file_download_response(response):
    """
    :param response: response to send
    :return: opcode + response
    """
    return "11" + str(response)


def pack_file_upload_response(response):
    """
    :param response: response to send
    :return: opcode + response
    """
    return "12" + str(response)


def pack_create_folder_response(response):
    """
    :param response: response to send
    :return: opcode + response
    """
    return "13" + str(response)


def pack_delete_response(response):
    """
    :param response: response to send
    :return: opcode + response
    """
    return "10" + str(response)


def pack_share_response(response):
    """
    :param response: response to send
    :return: opcode + response
    """
    return "09" + str(response)


def pack_change_username_response(response):
    """
    :param response: response to send
    :return: opcode + response
    """
    return "04" + str(response)


def pack_change_passowrd_response(response):
    """
    :param response: response to send
    :return: opcode + response
    """
    return "06" + str(response)


def pack_change_email_response(response):
    """
    :param response: response to send
    :return: opcode + response
    """
    return "05" + str(response)


if __name__ == '__main__':
    code, data_from_message = unpack_message("0112abaaaaaaaaaa01b")
    data = pack_files_message("reefg")

    print(data)

