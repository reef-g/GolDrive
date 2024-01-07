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


def unpack_files_message(msg):
    def get_data_from_string(line, leng):
        # getting the data from the length of the string
        data = line[leng:leng + int(line[:leng])]

        # substring
        line = line[leng + int(line[:leng])::]

        return data, line

    branches = []

    # until last element since its blank
    lines = msg.split('\n')[:-1]

    for line in lines:
        nameToAdd, line = get_data_from_string(line, 2)
        dirs, line = get_data_from_string(line, 4)
        files, line = get_data_from_string(line, 4)

        # joined directories with !
        dirs = dirs.split('!')

        # joined files with @
        files = files.split('@')

        # adding to list of branches
        branches.append((nameToAdd, dirs, files))

    return branches


def pack_register_request(username, password, email):
    """
    :param username: username of user
    :param password: password of user
    :param email: email of user
    :return: message built by protocol
    """
    return f"01{str(len(username)).zfill(2)}{username}{str(len(password)).zfill(2)}{password}{str(len(email)).zfill(2)}{email}"


def pack_login_request(usernaname, password):


def Pack_verify_check_request(code):


def Pack_forgot_password_request(email):


def Pack_file_download_request(path):


def Pack_upload_file_request(path, upload_path):

def pack_create_folder_request(name, upload_path):

def Pack_delete_request():

def Pack_rename_file_request():

def Pack_share_request():

def Pack__change_userename_request():

def Pack_change_password_request():

def Pack_change_email_request():


if __name__ == '__main__':
    print(unpack_files_message("000007folder10009fil1.docx\n07folder10008checking0000\n16folder1\checking00000000"))

    print(pack_register_request("reef", "123", "reefg19@gmail.com"))