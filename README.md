# OTA File Patcher

### <u>Purpose</u>
The OTA File Patcher serves as a way to patch files on multiple remote Linux-powered devices. A Bash script is dynamically created within the Patcher program which gets transferred over to the Linux device and executed. A top-view of the script is as such that:
- Finds the difference between the new patch file and the file to be patched. Stores these differences in an .update file.
- Performs a dry run of the patch. The patch is performed but no changes are made. 
- Once the dry run is successful, it performs the final patch using the .update file. The patch is verified by comparing the SHA1 hash strings of the patched file and the file that was used for the patch. If the hashes match, the patch is considered a success. Else, the patch is reverted and the original file is converted back to its original state before the patch.
- Based on exit codes, the script will appropriately handle errors throughout the patching process.


### <u>Getting Started</u>
This program requires a Python 3 environment along with the installation of the following modules:
- paramiko
- pynacl
- scp

The above modules can be installed by running the following commands from your terminal:
```
python -m pip paramiko
```
```
python -m pip pynacl
```
```
python -m pip scp
```

You will also need access to a MySQL database and the driver 'MYSQL Connector'.
The 'MYSQL Connector' driver can be downloaded [here](https://dev.mysql.com/downloads/connector/python/).

Once downloaded, the driver can be installed by running the following commands from your terminal:
```
python -m pip install mysql-connector
```

To run the program, navigate to the location of the files in terminal and run
```
python .\patcher.py
```

**Notes:** 
- This program was developed on a Windows operating system. A Linux port is currently a work in process.
- Certain lines of code are modified or renamed to mask sensitive information.
- Due to the nature of this program being workspace-specific, a test run may not be successful in your own environment. A working demo recording has been provided for demonstration.

### <u>System Design</u>
This Python Program was developed to perform automated, uniform file patches on a massive scale to remote Linux devices. The user will initially be asked to provide certain information of the patch file: file owner, permission, and directory. Once this information is provided it will no longer require user input after the program has been executed. 

A list of Linux devices is provided via a unique identifier. This list is looped through and the entire patching process is executed. Once the device in the first index has completed its patching process, the program restarts and begins the patching process on the next to the last index in the list of Linux devices.

When the program executes for the first time it asks the user for credentials to begin the patching process. This information is saved as a dictionary and then saved as a Pickle file. The Pickle module allows dictionaries to be saved as a file to be used at a later time. This is implemented to allow automation of multiple patch files - in a group of multiple Linux devices to be patched, only the patching process on the first Linux device will be prompted to be provided information. All other Linux devices in the list will utilize this Pickle file to populate all the required information for the patching process.

A locally saved configuration file containing MySQL login information is parsed to gain access to the database. A file containing a SQL query is then parsed to execute the commands. The results of the query are saved as a dictionary which can now be accessed directly through the Patcher program. The key: value pairs of the dictionary are the results of the user's input regarding the patch file details mentioned above. 

The variables from the dictionary are then used to dynamically create a Bash script and saved on the user's local machine in a folder containing the file that will be used to perform the patch. This folder is then SCP'd over to the Linux device where it is executed. A file containing Linux commands to execute the script is then parsed and sent over to the Linux device via SSH. 

The Bash script is then executed on the Linux device. A series of logic in the script determines a successful or a failed patch. If the patch has failed, it will restore the original that was to be patched to its original state before the patch was attempted. If the patch is successful, it will create a folder on the Linux device to hold a copy of the original version of the file to be patched. This backup folder will then be SCP'd from the Linux device to the user's local machine.

The SSH connection to the Linux device will then be closed. The Patcher program will then restart and be executed on the next Linux device in line. From this point on, the entire process will be automated - no user input will be required to perform the patching process on the rest of the required Linux devices.

### <u>Program Demo</u>
(Click the thumbnail below to be taken to a working demonstration.)

Due to the nature of the program, certain parts have been masked to hide sensitive information.

The right side of the screen demonstrates automation - on a list of two Linux devices to be patched, the user is required to enter in the relevant information to provide enough information for a file patch. After the program completes execution on the first Linux device, the second device does not require any additional user input to execute and complete a patching process.

The left side of the screen demonstrates the dynamic creation of the Bash script. The script is automatically populated with the information the user provided - specifically the file to be patched's owner, permissions, and directory.

[![OTA File Patcher](https://i.imgur.com/nAbRBAC.png)](https://www.youtube.com/watch?v=kJ6yZsMF2JM "OTA File Patcher")
