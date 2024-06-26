import os
from settings import CurrentSettings as Settings


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
    :return: message built by protocol
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
    files_of_user = "03"
    path = f"{Settings.SERVER_FILES_PATH}/{username}"

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


def pack_register_response(response, username, password, email):
    """
    :param response: response to register
    :param username: username of user
    :param password: password of user
    :param email: email of user
    :return: message built by protocol
    """
    return (f"01{str(len(str(response))).zfill(2)}{response}{str(len(str(username))).zfill(2)}{username}"
            f"{str(len(str(password))).zfill(2)}{password}{str(len(str(email))).zfill(2)}{email}")


def pack_login_response(response, email):
    """
    :param response: response to login
    :return: message built by protocol
    """
    return f"02{str(len(str(response))).zfill(2)}{response}{str(len(str(email))).zfill(2)}{email}"


def pack_verify_check_response(response):
    """
    :param response: response to verify check
    :return: message built by protocol
    """
    return f"15{str(len(str(response))).zfill(2)}{response}"


def pack_file_download_response(response, datalen, path, selected_path):
    """
    :param response: response to download file
    :param datalen: length of the data
    :param path: path of the file they asked to download
    :param selected_path: path of the user where to download
    :return: message built by protocol
    """
    return f"11{str(len(str(response))).zfill(2)}{response}{str(len(str(datalen))).zfill(2)}{datalen}" \
           f"{str(len(str(path))).zfill(2)}{path}{str(len(str(selected_path))).zfill(2)}{selected_path}"


def pack_upload_port(port):
    """
    :param port: upload port
    :return: message built by protocol
    """
    return f"16{str(len(str(port))).zfill(2)}{port}"


def pack_file_upload_response(response, path):
    """
    :param response: response to file upload
    :param path: path of file
    :return: message built by protocol
    """
    return f"12{str(len(str(response))).zfill(2)}{response}{str(len(str(path))).zfill(2)}{path}"


def pack_create_folder_response(response):
    """
    :param response: response to folder create
    :return: message built by protocol
    """
    return f"13{str(len(str(response))).zfill(2)}{response}"


def pack_delete_response(response):
    """
    :param response: response to file delete
    :param path: the path deleted
    :return: message built by protocol
    """
    return f"10{str(len(str(response))).zfill(2)}{response}"


def pack_rename_file_response(response, new_name):
    """
    :param response: response to file delete
    :param path: the path deleted
    :param new_name: the name of the file
    :return: message built by protocol
    """
    return f"08{str(len(str(response))).zfill(2)}{response}{str(len(str(new_name))).zfill(2)}{new_name}"


def pack_share_response(response):
    """
    :param response: response to share file
    :return: message built by protocol
    """
    return f"09{str(len(str(response))).zfill(2)}{response}"


def pack_change_photo_response(response, file_len):
    """
    :param response: response to change photo
    :return: message built by protocol
    """
    return f"04{str(len(str(response))).zfill(2)}{response}{str(len(str(file_len))).zfill(2)}{file_len}"


def pack_change_password_response(response):
    """
    :param response: response to change password
    :return: message built by protocol
    """
    return f"06{str(len(str(response))).zfill(2)}{response}"


def pack_change_email_response(response, email):
    """
    :param response: response to change email
    :param email: email to change to
    :return: message built by protocol
    """
    return f"05{str(len(str(response))).zfill(2)}{response}{str(len(str(email))).zfill(2)}{email}"


def pack_login_verify_response(status):
    """
    :param status: response to login verify
    :return: message built by protocol
    """
    return f"23{str(len(str(status))).zfill(2)}{status}"


def pack_add_shared_file(path):
    """
    :param path: path of file to add to client branches
    :return: message built by protocol
    """
    return f"14{str(len(str(path))).zfill(2)}{path}"


def pack_send_email_response(status, email):
    return f"17{str(len(str(status))).zfill(2)}{status}{str(len(str(email))).zfill(2)}{email}"


def pack_move_file_response(status, new_folder):
    """
    :param status: response to move file
    :param new_folder: the folder moved to
    :return: message built by protocol
    """
    return f"18{str(len(str(status))).zfill(2)}{status}{str(len(str(new_folder))).zfill(2)}{new_folder}"


def pack_paste_file_response(status):
    """
    :param status: response to paste file
    :return: message built by protocol
    """
    return f"19{str(len(str(status))).zfill(2)}{status}"


def pack_open_file_response(status, file_path, data_len):
    """
    :param status: status to open file
    :param file_path: the file path in the server
    :param data_len: the length of the data of the file
    :return: message built by protocol
    """
    return f"20{str(len(str(status))).zfill(2)}{status}{str(len(str(data_len))).zfill(2)}{data_len}" \
           f"{str(len(str(file_path))).zfill(2)}{file_path}"


def pack_get_details_response(status, email, data_len):
    """
    :param status: response to get details
    :param email: email of the client
    :param data_len: length of the profile photo
    :return: message built by protocol
    """
    return (f"21{str(len(str(status))).zfill(2)}{status}"
            f"{str(len(str(email))).zfill(2)}{email}{str(len(str(data_len))).zfill(2)}{data_len}")


def pack_delete_profile_photo_response(status):
    """
    :param status: response to delete photo request
    :return: message built by protocol
    """
    return f"22{str(len(str(status))).zfill(2)}{status}"


def pack_register_verify_response(status):
    """
    :param status: response to register verify
    :return: message built by protocol
    """
    return f"24{str(len(str(status))).zfill(2)}{status}"


def pack_check_code_response(status):
    """
    :param status: response to check code
    :return: message built by protocol
    """
    return f"25{str(len(str(status))).zfill(2)}{status}"


def pack_forgot_password_response(status):
    """
    :param status: response to forgot password request
    :return: message built by protocol
    """
    return f"26{str(len(str(status))).zfill(2)}{status}"


def pack_zip_folder_response(status, zipped_folder_name):
    """
    :param status: response to zip folder
    :param zipped_folder_name: zipped folder name
    :return: message built by protocol
    """
    return f"27{str(len(str(status))).zfill(2)}{status}{str(len(str(zipped_folder_name))).zfill(2)}{zipped_folder_name}"


if __name__ == '__main__':
    code, data_from_message = unpack_message("1210reef/reef1000012")
    dataa = pack_files_message("reef")

    print(dataa)
