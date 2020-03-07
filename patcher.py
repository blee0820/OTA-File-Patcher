import paramiko
import mysql.connector
import os
import sys
import getpass
import pickle
import time

from paramiko import SSHClient, AutoAddPolicy
from sql_conn import connector
from decrypt_cam_pw import cam_pw_decrypt
from parse_commands import parse_commands
from scp import SCPClient

def pickler(username=None, port=None, su_pw=None, auth_key=None):
        try:
            # Creates .pickle file to store user inputted data.
            if username and port and su_pw:
                user_dict = {'username': username, 'port': port, 'su_pw': su_pw}
                filename = 'user.pickle'
                outfile = open(filename, 'wb')
                pickle.dump(user_dict, outfile)
                outfile.close()
            if auth_key:
                infile = open('user.pickle', 'rb')
                user_dict = pickle.load(infile)
                user_dict.update({'auth_key': auth_key})
                outfile = open('user.pickle', 'wb')
                pickle.dump(user_dict, outfile)
                infile.close()
                outfile.close()
            return user_dict
        except Exception as e:
            print("Error has occurred when pickling files. See below.")
            print(e)
            sys.exit(1)

class Patch:
    def __init__(self, cam_id, cam_count, cam_id_list):
        self.cam_id = cam_id   
        self.cam_count = cam_count
        self.cam_id_list = cam_id_list
    
    def patch_files(self):
        try:
            if self.cam_count == 1:
                file_details = {"Owner": None, "Permission": None, "Directory": None}
                service_file = []
                files = next(os.walk('./bash-scripts/patch-files/'))[2]
                print("These are the files marked for transfer:")
                
                # store all .service files in a separate list to be parsed later
                for file_list in files:
                    print("-",file_list)
                    if ".service" in file_list:
                        service_file.append(file_list)
                
                # print user instructions        
                print("")
                print("*"*104)
                print("For each file, please submit the following info, each submission confirmed with Enter Key")
                print("Owner: (please use format <user:user>)")
                print("Permission: (numeric value or symbolic notation)")
                print("Directory where the to-be patched file is located: (absolute path name, do not include filename in path)")
                print("*"*104)
                print("")
                
                # begin bash script template
                f = open("./bash-scripts/patcher.sh", "w+" )       
                f.write("#!/bin/bash"\
                        "\n\npatcher(){"\
                        "\n\ttime=$( date +'%m-%d-%Y-%H,%M,%S')"\
                        "\n\tmount - / -oremount,rw"\
                        "\n\tcd /tmp/patch/bash-scripts/patch-files\n")
                
                # dynamically populate bash script based on user input
                for file in files:
                    print("File:", file)
                    for key in file_details:
                        file_details[key] = input("{}: ".format(key))
                    f.write("\n\tchown " + file_details["Owner"] + " " + file +\
                            "\n\tchmod " + file_details["Permission"] + " " + file +\
                            "\n\techo Patching " + file + " to " + file_details["Directory"] +\
                            "\n\tdiff -u " + file_details["Directory"] + "/" + file + " " + file + " > update.patch"\
                            "\n\tif [ \"$?\" = \"1\" ]; then"\
                            "\n\t\tpatch --dry-run " + file_details["Directory"] + "/" + file + " < update.patch"\
                            "\n\t\tif [ \"$?\" = \"0\" ]; then"\
                            "\n\t\t\tpatch -b " + file_details["Directory"] + "/" + file + " < update.patch && mkdir -p /tmp/patch/" + str(self.cam_id) + "_backup_$time && mv /tmp/patch/bash-scripts/patch-files/*.patch /tmp/patch/" + str(self.cam_id) + "_backup_$time && mv " + file_details["Directory"] + "/*.orig /tmp/patch/" + str(self.cam_id) + "_backup_$time"\
                            "\n\t\t\tif [ \"$?\" = \"0\" ]; then"\
                            "\n\t\t\t\thash1=$(sha1sum $'" + file + "' | cut -d ' ' -f 1)"\
                            "\n\t\t\t\thash2=$(sha1sum $'" + file_details["Directory"] + "/" + file + "' | cut -d ' ' -f 1)"\
                            "\n\t\t\t\tif [ \"$hash1\" == \"$hash2\" ]; then"\
                            "\n\t\t\t\t\tmount - / -oremount,ro"\
                            "\n\t\t\t\t\techo The hash codes of " + file + " and " + file_details["Directory"] + "/" + file + " match."\
                            "\n\t\t\t\t\techo Successfully patched " + file + "."\
                            "\n\t\t\t\t\techo Exiting patching process."\
                            "\n\t\t\t\t\texit 0"\
                            "\n\t\t\t\telse"\
                            "\n\t\t\t\t\tpatch -R " + file_details["Directory"] + "/" + file + " < update.patch"\
                            "\n\t\t\t\t\tif [ \"$?\" = \"0\" ]; then"\
                            "\n\t\t\t\t\t\tmount - / -oremount,ro"\
                            "\n\t\t\t\t\t\techo The hash codes of the source file and patch file do not match."\
                            "\n\t\t\t\t\t\techo Please check your source and patch files."\
                            "\n\t\t\t\t\t\techo Reverting patch and aborting patch process."\
                            "\n\t\t\t\t\t\texit 0"\
                            "\n\t\t\t\t\telse"\
                            "\n\t\t\t\t\t\tmount - / -oremount,ro"\
                            "\n\t\t\t\t\t\techo The has codes of the source file and patch file do not match."\
                            "\n\t\t\t\t\t\techo Tried to revert patch but it has failed."\
                            "\n\t\t\t\t\t\techo Please check your source and patch files."\
                            "\n\t\t\t\t\t\techo Aborting patching process."\
                            "\n\t\t\t\t\t\texit 1"\
                            "\n\t\t\t\t\tfi"\
                            "\n\t\t\t\tfi"\
                            "\n\t\t\telse"\
                            "\n\t\t\t\tmount - / -oremount,ro"\
                            "\n\t\t\t\techo There was an error during the patching process."\
                            "\n\t\t\t\techo Please double check all back up files for existence."\
                            "\n\t\t\t\techo Please check your source and patch files."\
                            "\n\t\t\t\techo Aborting patching process."\
                            "\n\t\t\t\texit 1"\
                            "\n\t\t\tfi"\
                            "\n\t\telse"\
                            "\n\t\t\tmount - / -oremount,ro"\
                            "\n\t\t\techo There was an error during the dry run process of the patch."\
                            "\n\t\t\techo Please check your source and patch files."\
                            "\n\t\t\techo Aborting patching process."\
                            "\n\t\t\texit 1"\
                            "\n\t\tfi"\
                            "\n\telif [ \"$?\" = \"0\" ]; then"\
                            "\n\t\trm update.patch"\
                            "\n\t\tmount - / -oremount,ro"\
                            "\n\t\techo No differences found between source file and patch file."\
                            "\n\t\techo No patching was initiated."\
                            "\n\t\techo Aborting patching process."\
                            "\n\t\texit 1"\
                            "\n\telif [ \"$?\" = \"2\" ]; then"\
                            "\n\t\tmount - / -oremount,ro"\
                            "\n\t\techo An error has occurred during the diff process when creating the update file."\
                            "\n\t\techo Please check your source file and patch file."\
                            "\n\t\techo Aborting patching process."\
                            "\n\t\texit 1"\
                            "\n\tfi"\
                            "\n}"\
                            "\npatcher"               
                            )
                    f.close()
            else:
                # replace cam_ID on backup folder name
                # open patcher.sh and read contents
                prev_cam_id = self.cam_id_list[self.cam_count - 2]
                f = open("./bash-scripts/patcher.sh", "rt")
                contents = f.read()
                contents = contents.replace(str(prev_cam_id), str(self.cam_id))
                f.close()
                
                # open patcher.sh and write replaced text
                f = open("./bash-scripts/patcher.sh", "wt")
                f.write(contents)
                f.close()
                    
        except Exception as e:
            print(e)
        
    def camera_SSH(self):      
        try:
            print("")
            print("*** Starting Patcher for", self.cam_id,"***")
            if self.cam_count == 1:
                print("")
                username = input("Enter username: ")
                port = input("Enter port number: ")
                su_pw = getpass.getpass("Enter su password: ")
                pickler(username=username, port=port, su_pw=su_pw)
            else:
                pickle_file = open('user.pickle', 'rb')
                load_pickle = pickle.load(pickle_file)
                username = load_pickle['username']
                port = load_pickle['port']
                su_pw = load_pickle['su_pw']
                pickle_file.close()
        except KeyboardInterrupt as ki:
            print(ki)
            sys.exit(0)
        except Exception as e:
            print(e)
            print("An Exception has occurred.")
            print("")
            sys.exit(1)
        
        # SSH into camera and execute Linux commands         
        try:
            # Retrieve final decrypted IP address and password
            # Calls cam_pw_decrypt() to begin decryption of password
            cam_info = cam_pw_decrypt(self.cam_id, self.cam_count)
            host = cam_info.get('cam_IP')
            password = cam_info.get('password')
            
            ssh = SSHClient()
            ssh.load_system_host_keys()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, port=port, username=username, password=password)
            
            print("")
            print("SSH connection to camera", self.cam_id, "at", host, "established.")
            print("")
            print("Attempting patching process, please wait...")
            print("")

            try:
                # call parse_commands() to execute appropriate Linux commands
                stdin, stdout, stderr = ssh.exec_command("su \n")
                stdin.write(su_pw + "\n")
                
                reboot = 0
                while reboot == 0:
                    stdin.write('killall php\n' + 'mount - / -oremount,rw\n' + 'mkdir -m 777 -p /tmp/patch\n')
                                                    
                    # push required files to camera from local machine
                    # sanitization required for using wildcards on scp.get()
                    # otherwise wildcards are treated literally
                    # https://stackoverflow.com/questions/47926123/using-wildcards-in-file-names-using-pythons-scpclient-library
                    with SCPClient(ssh.get_transport(), sanitize=lambda x: x) as scp:
                        try:
                            #if self.cam_count == 1:
                            self.patch_files()
                            scp.put('bash-scripts', '/tmp/patch', recursive=True)
                            scp.close()
                            print("Required files successfully transferred to camera.")
                            print("")
                        except Exception as e:
                            scp.close()
                            ssh.close()
                            print(e)
                            print("Error transferring required files to camera.")
                            print("Terminating program")
                            print("")
                            sys.exit(1)
                            
                        script = parse_commands() 
                        for cmd in script:
                            stdin.write(cmd + '\n')
                        
                        stdin.close()
                        out = stdout.read().decode()
                        print("Terminal output:")
                        print(out)
                        # pull backed up files from camera to local machine
                        try:
                            scp.get(remote_path='/tmp/patch/*_backup_*', local_path='.', recursive=True)
                            print("Backed up files successfully transferred to local machine.")
                            print("")
                            scp.close()
                            reboot = 1
                        except Exception as e:
                            scp.close()
                            ssh.close()
                            print("Error transferring backup files to local machine.")
                            print("Error may have occurred due to source file and patch file being identical.")
                            print("Terminating program")
                            print("")
                            sys.exit(1)
            except Exception as e:
                ssh.close()
                print(e)
                print("Error parsing and executing Linux commands.")
                print("Closing SSH session and terminating program.")
                sys.exit(1)
        except paramiko.AuthenticationException:
            ssh.close()
            print("Authentication Error. SSH connection terminated.")
        finally:
            print("Closing SSH connection to " + host + ".")
            print("System will now reboot, please wait.")
            print("")
            stdin, stdout, stderr = ssh.exec_command("su \n")
            stdin.write(su_pw + "\n")
            stdin.write("mount - / -oremount,rw\n" + "rm -r /tmp/patch\n" + "systemctl reboot\n")
            ssh.close()
            time.sleep(5)
if __name__ == '__main__':
    cam_id_list = [12345, 67890]
    
    for cam_count, cam in enumerate(cam_id_list, 1):        
        start_transfer = Patch(cam, cam_count, cam_id_list)
        start_transfer.camera_SSH()
    os.remove('auth_key.pickle')
    os.remove('user.pickle')
    os.remove('bash-scripts/patcher.sh')
    print("Patching process complete. Program will now exit.")
    sys.exit(0)