def unpack_message(msg):
    """
    :param msg: message to unpack
    :return: tuple with opcode and variables
    """
    opcode = msg[:2]
    msg = msg[2:]
    data_from_msg = []
    if opcode == "03":
        data_from_msg = unpack_files_message(msg)

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


def get_data_from_string(line, length):
    """
    :param line: line to slice
    :param length: length to slice
    :return:
    """
    # getting the data from the length of the string
    data = line[length:length + int(line[:length])]

    # substring
    line = line[length + int(line[:length])::]

    return data, line


def unpack_files_message(msg):
    """
    :param msg: the files message
    :return: list of branches each branch has its directories and files
    """
    branches = []

    # until last element since its blank
    lines = msg.split('\n')[:-1]

    for line in lines:
        name_to_add, line = get_data_from_string(line, 2)
        dirs, line = get_data_from_string(line, 4)
        files, line = get_data_from_string(line, 4)

        # joined directories with !
        dirs = dirs.split('!')

        # joined files with @
        files = files.split('@')

        # adding to list of branches
        branches.append((name_to_add, dirs, files))

    return branches


def pack_register_request(username, password, email):
    """
    :param username: username
    :param password: password
    :param email: email
    :return: message built by protocol
    """
    return f"01{str(len(username)).zfill(2)}{username}{str(len(password)).zfill(2)}{password}" \
        f"{str(len(email)).zfill(2)}{email}"


def pack_login_request(username, password):
    """
    :param username: username
    :param password: password
    :return: message built py protocol
    """
    return f"02{str(len(username)).zfill(2)}{username}{str(len(password)).zfill(2)}{password}"


def pack_verify_check_request(email, code):
    """
    :param email: email to verify
    :param code: code sent to email
    :return: message built py protocol
    """
    return f"15{str(len(email)).zfill(2)}{email}{str(len(str(code))).zfill(2)}{code}"


def pack_send_verify_request(email):
    """
    :param email: email
    :return: message built py protocol
    """
    return f"07{str(len(email)).zfill(2)}{email}"


def pack_download_file_request(path, selected_path):
    """
    :param path: path of file to download
    :param selected_path: path of where to download the file to
    :return: message built py protocol
    """
    return f"11{str(len(path)).zfill(2)}{path}{str(len(selected_path)).zfill(2)}{selected_path}"


def pack_upload_file_request(upload_path, data_len):
    """
    :param upload_path: path to upload to including file name
    :param data_len: the length of the data
    :return: message built py protocol
    """
    return f"12{str(len(upload_path)).zfill(2)}{upload_path}{str(len(str(data_len))).zfill(2)}{data_len}"


def pack_create_folder_request(path):
    """
    :param path: path of where to create the folder
    :return: message built py protocol
    """
    return f"13{str(len(path)).zfill(2)}{path}"


def pack_delete_request(path):
    """
    :param path: path of file to delete
    :return: message built py protocol
    """""
    return f"10{str(len(path)).zfill(2)}{path}"


def pack_rename_file_request(path, new_name):
    """
    :param path: path of file to rename
    :param new_name: new name of file
    :return: message built py protocol
    """
    return f"08{str(len(path)).zfill(2)}{path}{str(len(new_name)).zfill(2)}{new_name}"


def pack_share_request(path, username):
    """
    :param path: file to share path
    :param username: username of person to share
    :return: message built py protocol
    """
    return f"09{str(len(path)).zfill(2)}{path}{str(len(username)).zfill(2)}{username}"


def pack_change_photo_request(username, file_len):
    """
    :param username: username to change to
    :param file_len: length of the photo
    :return: message built py protocol
    """
    return f"04{str(len(str(username))).zfill(2)}{username}{str(len(str(file_len))).zfill(2)}{file_len}"


def pack_change_password_request(username, old_password, new_password, confirmed_password):
    """
    :param username: username of user
    :param old_password: password
    :param new_password: new password of user
    :param confirmed_password: confirmation of the new password
    :return: message built py protocol
    """
    return (f"06{str(len(str(username))).zfill(2)}{username}{str(len(str(old_password))).zfill(2)}{old_password}"
            f"{str(len(str(new_password))).zfill(2)}{new_password}"
            f"{str(len(str(confirmed_password))).zfill(2)}{confirmed_password}")


def pack_change_email_request(username, email, code):
    """
    :param username: username of user
    :param email: email
    :param code: the code sent to the user
    :return: message built py protocol
    """
    return (f"05{str(len(str(username))).zfill(2)}{username}{str(len(str(email))).zfill(2)}{email}"
            f"{str(len(str(code))).zfill(2)}{code}")


def pack_move_file_folder_request(src, dst):
    return f"18{str(len(str(src))).zfill(2)}{src}{str(len(str(dst))).zfill(2)}{dst}"


def pack_paste_file_request(src, dst):
    return f"19{str(len(str(src))).zfill(2)}{src}{str(len(str(dst))).zfill(2)}{dst}"


def pack_open_file_request(path):
    return f"20{str(len(str(path))).zfill(2)}{path}"


def pack_get_details_request(username):
    return f"21{str(len(str(username))).zfill(2)}{username}"


def pack_delete_profile_photo_request(username):
    return f"22{str(len(str(username))).zfill(2)}{username}"


def pack_verify_login_email_request(email, code, dont_ask_again, username):
    return (f"23{str(len(str(email))).zfill(2)}{email}{str(len(str(code))).zfill(2)}{code}"
            f"{str(len(str(dont_ask_again))).zfill(2)}{dont_ask_again}{str(len(str(username))).zfill(2)}{username}")


if __name__ == '__main__':
    print(unpack_files_message("000007folder10009fil1.docx\n07folder10008checking0000\n16folder1\\checking00000000"))

    print(pack_register_request("reef", "123", "reefg19@gmail.com"))
    print(unpack_message("0104reef0312317reefg19@gmail.com"))
    print(pack_login_request("reef", "123"))

    print(pack_get_details_request("reef"))
