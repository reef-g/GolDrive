# README

GolDrive is a storage app which helps you store your files in the cloud.

--------------------------------------------------------
## Install

1. Clone the project using the following command in cmd:
```cmd
git clone https://github.com/reef-g/GolDrive
```
2. in order to install run the following commands in cmd:
```cmd
cd goldrive_code
pip install –r requirements.txt
```

------------------------------------------------------
## Run
- Open settings.py and set change SERVERIP to your servers ip, change USER_FILES_PATH to the directory on your computer that contains the images to run the project.


**Firstly make sure your cmd is mounted on the project files!**
In order to run the server use the following command in cmd:
```cmd
python .\ServerFiles\serverLogic.py
```
In order to run the client use the following commands in cmd:
```cmd
python .\ClientFiles\mainClient.py
```
