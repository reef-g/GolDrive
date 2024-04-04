import os
import zipfile


def rename_file(path, new_name):
    """
    :param path: path of file to rename
    :param new_name: the new name of the file
    :return: renames the file and returns 1 if it didn't work and 0 if it manged
    """
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
    """
    :param path: path of file to delete
    :return: deletes file 1 if successful 0 if failed
    """
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
    """
    :param path: path of file to download
    :return: reads the file 1 if it could read it 0 if failed
    """
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


def generate_unique_zip_name(path, base_name):
    """
    :param path: path of the folder to zip
    :param base_name: the name of the folder
    :return: creates the name based on the existing files
    """
    full_path = f"{path}/{base_name}.zip"
    unique_name = f"{base_name}.zip"

    if os.path.exists(full_path):
        index = 1
        while os.path.exists(f"{path}/{base_name} ({index}).zip"):
            index += 1
        unique_name = f"{base_name} ({index}).zip"

    return unique_name


def create_zip(total_path):
    """
    :param total_path: path of the folder
    :return: zips the path returns 1 if failed to zip 0 if it worked
    """
    status = 0
    zip_file_name = None
    if os.path.isdir(total_path):
        try:
            folder_path, name = total_path.split('/')[:-1], total_path.split('/')[-1]
            folder_path = '/'.join(folder_path)

            # generates the correct name
            zip_file_name = generate_unique_zip_name(folder_path, name)
            zip_path = f"{folder_path}/{zip_file_name}"

            # Create a ZipFile object in write mode
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                # Add all files in the directory and its subdirectories to the zip file
                for root, _, files in os.walk(total_path):
                    for file in files:
                        file_path = f"{root}/{file}"
                        file_name = os.path.relpath(file_path, total_path)
                        zipf.write(file_path, arcname=file_name)

        except Exception as e:
            print(str(e))
            status = 1
    else:
        status = 1

    return status, zip_file_name


if __name__ == '__main__':
    create_zip("C:/Users/reefg/PycharmProjects/goldrive_code/ServerFiles")
