import os

import Settings


def unpack_message(msg):
    """
    :param msg: message to unpack
    :return: tuple with opcode and variables
    """

    opcode = msg[:2]
    data_from_msg = []
    msg = msg[2:]

    if opcode == "12":
        leng = msg[:2]
        msg = msg[2:]
        data_from_msg.append(msg[:int(leng)])
        msg = msg[int(leng):]
        data_from_msg.append(msg[:])

    else:
        while len(msg) > 0:
            try:
                data, msg = get_data_from_string(msg, 2)
                data_from_msg.append(data)

            except Exception as e:
                print("in unpack_message -", str(e))
                opcode = None
                break

    return opcode, data_from_msg


def get_data_from_string(line, leng):
    """
    :param line: line to slice
    :param leng: length to slice
    :return:
    """
    # getting the data from the length of the string
    data = line[leng:leng + int(line[:leng])]

    # substring
    line = line[leng + int(line[:leng])::]

    return data, line


def pack_files_message(username):
    """
    :param username: username of user
    :return: string with all files and directories of user in the drive
    """
    files_of_user = "13"
    # the path to work at, will later to change to the person directory
    path = f"{Settings.USER_FILES_PATH}/{username}"

    for (dirname, dirs, files) in os.walk(path):
        # removing the path so that it's only the directories in the system and not from the server
        dirname = dirname[len(path) + 1::].replace('\\', '/')

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
    :param response: response to register
    :return: opcode + length + response
    """
    return f"01{str(len(str(response))).zfill(2)}{response}"


def pack_login_response(response):
    """
    :param response: response to login
    :return: opcode + length + response
    """
    return f"02{str(len(str(response))).zfill(2)}{response}"


def pack_verify_check_response(response):
    """
    :param response: response to verify check
    :return: opcode + length + response
    """
    return f"15{str(len(str(response))).zfill(2)}{response}"


def pack_forgot_password_response(response):
    """
    :param response: response to forgot password
    :return: opcode + length + response
    """
    return f"07{str(len(str(response))).zfill(2)}{response}"


def pack_file_download_response():
    # download file response
    return "11"


def pack_upload_port_response(response):
    """
    :param response: response to upload port
    return: opcode + length + response
    """
    return f"16{str(len(str(response))).zfill(2)}{response}"


def pack_file_upload_response(response):
    """
    :param response: response to file upload
    :return: opcode + length + response
    """
    return f"12{str(len(str(response))).zfill(2)}{response}"


def pack_create_folder_response(response):
    """
    :param response: response to folder create
    :return: opcode + length + response
    """
    return f"13{str(len(str(response))).zfill(2)}{response}"


def pack_delete_response(response, path):
    """
    :param response: response to file delete
    :param path: the path deleted
    :return: opcode + length + response
    """
    return f"10{str(len(str(response))).zfill(2)}{response}{str(len(str(path))).zfill(2)}{path}"


def pack_share_response(response):
    """
    :param response: response to share file
    :return: opcode + length + response
    """
    return f"09{str(len(str(response))).zfill(2)}{response}"


def pack_change_username_response(response):
    """
    :param response: response to change username
    :return: opcode + length + response
    """
    return f"04{str(len(str(response))).zfill(2)}{response}"


def pack_change_passowrd_response(response):
    """
    :param response: response to change password
    :return: opcode + length + response
    """
    return f"06{str(len(str(response))).zfill(2)}{response}"


def pack_change_email_response(response):
    """
    :param response: response to change email
    :return: opcode + length + response
    """
    return f"05{str(len(str(response))).zfill(2)}{response}"


def pack_verify_email_message():
    return "17"


if __name__ == '__main__':
    code, data_from_message = unpack_message("1210reef/reef1000012")
    dataa = pack_files_message("reef")

    print(dataa)
