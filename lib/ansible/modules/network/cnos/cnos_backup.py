#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Lenovo, Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
# Module to Backup Config to Lenovo Switches
# Lenovo Networking
#
#---- Documentation Start ----------------------------------------------------#
DOCUMENTATION = '''
---
module: cnos_backup
short_description: Performs configuration Back up of switches using SFTP/SCP/FTP/TFTP.
description: 
    - Manages network device configurations over SSH. 
     This module allows implementors to work with the device configurations. 
     It provides a way to backup configurations of a network device to an SFTP/SCP/FTP/TFTP server.
     You can store either the running config or start up config of the device. 
     You have to first create a folder which has the reach of the SFTP/SCP/FTP/TFTP Server. 
     Then specify the full path from where you need to backup the config file. 
     Authentication details pertaining to SFTP/SCP/FTP server also have to be provided. 
     Results of the backup operation can be viewed in results folder.
version_added: "2.3"
options:
    configType:
        description:
            -This refers to the type of configuration which you want to back up. The choices are as mentioned. There is no 
            default value, so if incorrect will give an error.
        required: Yes
        default: null
        choices: [running-config, startup-config]
    protocol:
        description:
            -This refers to the protocol in which your device will interract with the server you are connecting to 
            download image onto the device. The choices for you are SFTP, SCP, FTP or TFTP. Any other protocols apart from
            the above will result in error. There is no default specified for this argument
        required: Yes
        default: null
        choices: [SFTP, SCP, FTP, TFTP]
    rcserverip:
        description:
            -IP Address of the SFTP/SCP/FTP/TFTP server you are using to store the backed up config file
        required: Yes
        default: null
    rcpath:
        description:
            - This specifies the absolute path of the config file will be located in the server. In case u are using the 
             relative path as the variable value, you need to specify the root folder for the user of the server which u 
             have specified.
        required: Yes
        default: null
    serverusername:
        description:
            - Username for the server pertaining to respective protocol of your choice.
        required: Yes
        default: null
    serverpassword:
        description:
            - Password for the server pertaining to respective protocol of your choice.
        required: Yes
        default: null
    
Notes:
    - For help in developing on modules, should you be so inclined, please read 
     Community Information & Contributing, Helping Testing PRs and Developing Modules.
Module Dependency :
    1. cnos_backup.py
    2. cnos.py
'''

EXAMPLES = '''
#The tasks/main.yml will look like this
---
- name: Test Running Config Backup
  cnos_backup: host={{ inventory_hostname }} username={{ hostvars[inventory_hostname]['username']}}  password={{ hostvars[inventory_hostname]['password']}} deviceType={{ hostvars[inventory_hostname]['deviceType']}} outputfile=./results/cnos_backup_{{ inventory_hostname }}_output.txt configType='{{item.configType}}' protocol='{{item.protocol}}' serverip='{{item.serverip}}' rcpath='{{item.rcpath}}' serverusername='{{item.serverusername}}' serverpassword='{{item.serverpassword}}'
  with_items: "{{test_config_data1}}"

- name: Test Startup Config Backup
  cnos_backup: host={{ inventory_hostname }} username={{ hostvars[inventory_hostname]['username']}}  password={{ hostvars[inventory_hostname]['password']}} deviceType={{ hostvars[inventory_hostname]['deviceType']}} outputfile=./results/cnos_backup_{{ inventory_hostname }}_output.txt configType='{{item.configType}}' protocol='{{item.protocol}}' serverip='{{item.serverip}}' rcpath='{{item.rcpath}}' serverusername='{{item.serverusername}}' serverpassword='{{item.serverpassword}}'
  with_items: "{{test_config_data2}}"
  
- name: Test Running Config Backup -TFTP
  cnos_backup: host={{ inventory_hostname }} username={{ hostvars[inventory_hostname]['username']}}  password={{ hostvars[inventory_hostname]['password']}} deviceType={{ hostvars[inventory_hostname]['deviceType']}} outputfile=./results/cnos_backup_{{ inventory_hostname }}_output.txt configType='{{item.configType}}' protocol='{{item.protocol}}' serverip='{{item.serverip}}' rcpath='{{item.rcpath}}' serverusername='{{item.serverusername}}' serverpassword='{{item.serverpassword}}'
  with_items: "{{test_config_data3}}"

- name: Test Startup Config Backup - TFTP
  cnos_backup: host={{ inventory_hostname }} username={{ hostvars[inventory_hostname]['username']}}  password={{ hostvars[inventory_hostname]['password']}} deviceType={{ hostvars[inventory_hostname]['deviceType']}} outputfile=./results/cnos_backup_{{ inventory_hostname }}_output.txt configType='{{item.configType}}' protocol='{{item.protocol}}' serverip='{{item.serverip}}' rcpath='{{item.rcpath}}' serverusername='{{item.serverusername}}' serverpassword='{{item.serverpassword}}'
  with_items: "{{test_config_data4}}"

#In the vars/main.yml will look like this
---
test_config_data1:
  - {configType: running-config, protocol: "sftp", serverip: "10.241.106.118", rcpath: "/root/cnos/G8272-running-config.txt",  serverusername: "root", serverpassword: "root123"}

test_config_data2:
  - {configType: startup-config, protocol: "sftp", serverip: "10.241.106.118", rcpath: "/root/cnos/G8272-startup-config.txt",  serverusername: "root", serverpassword: "root123"}

test_config_data3:
  - {configType: running-config, protocol: "tftp", serverip: "10.241.106.118", rcpath: "/anil/G8272-running-config.txt",  serverusername: "root", serverpassword: "root123"}

test_config_data4:
  - {configType: startup-config, protocol: "tftp", serverip: "10.241.106.118", rcpath: "/anil/G8272-startup-config.txt",  serverusername: "root", serverpassword: "root123"}

---
#In the inventory file u specify like this
inventory sample: |
    [cnos_backup_sample]
    10.241.107.39  username=<username> password=<password> deviceType=g8272_cnos 
    10.241.107.40  username=<username> password=<password> deviceType=g8272_cnos 

'''

RETURN = '''
---
return value: |
 On successful execution, the method returns and empty string with a message "Config file tranferred to server"
 in json format. But upon any failure, the output will be the error display string. You may have to rectify 
 the error and try again.
 
'''
#---- Documentation Ends ----------------------------------------------------#
#---- Logic Start ------------------------------------------------------------###

import sys
import paramiko
import time
import argparse
import socket
import array
import json
import time
import re
try:
    import cnos
    HAS_LIB=True
except:
    HAS_LIB=False

#
# load Ansible module
#
from ansible.module_utils.basic import AnsibleModule
from collections import defaultdict

#
def  main():
    #
    # Define parameters for commandline entry
    #
    module = AnsibleModule(
        argument_spec=dict(
            outputfile=dict(required=True),
            host=dict(required=True),
            username=dict(required=True),
            password=dict(required=True,no_log=True),
            enablePassword=dict(required=False,no_log=True),
            deviceType=dict(required=True),
            configType=dict(required=True),
            protocol=dict(required=True),
            serverip=dict(required=True),
            rcpath=dict(required=True),
            serverusername=dict(required=False),
            serverpassword=dict(required=False,no_log=True),),
        supports_check_mode=False)

    username = module.params['username']
    password = module.params['password']
    enablePassword = module.params['enablePassword']
    outputfile = module.params['outputfile']
    host = module.params['host']
    deviceType = module.params['deviceType']
    configType = module.params['configType']
    protocol = module.params['protocol'].lower()
    rcserverip = module.params['serverip']
    rcpath = module.params['rcpath']
    serveruser = module.params['serverusername']
    serverpwd = module.params['serverpassword'] 
    output = ""
    timeout = 90
    tftptimeout = 450

    # Create instance of SSHClient object
    remote_conn_pre = paramiko.SSHClient()

    # Automatically add untrusted hosts (make sure okay for security policy in your environment)
    remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # initiate SSH connection with the switch
    remote_conn_pre.connect(host, username=username, password=password)
    time.sleep(2)
    
    # Use invoke_shell to establish an 'interactive session'
    remote_conn = remote_conn_pre.invoke_shell()
    time.sleep(2)
    
    #
    # Enable and enter configure terminal then send command
    output = output + cnos.waitForDeviceResponse("\n", ">", 2, remote_conn)
    
    output = output + cnos.enterEnableModeForDevice(enablePassword, 3, remote_conn)
    
    # Make terminal length = 0
    output = output + cnos.waitForDeviceResponse("terminal length 0\n", "#", 2, remote_conn)
    
    # Invoke method for config transfer from server    
    if(configType == 'running-config'):
        if(protocol == "tftp" or protocol == "ftp"):
            transfer_status = cnos.doRunningConfigBackUp(protocol, tftptimeout, rcserverip, rcpath, serveruser, serverpwd, remote_conn)
        elif(protocol == "sftp" or protocol == "scp"):
            transfer_status = cnos.doSecureRunningConfigBackUp(protocol, timeout, rcserverip, rcpath, serveruser, serverpwd, remote_conn)
        else:
            transfer_status = "Invalid Protocol option"
    elif(configType == 'startup-config'):
        if(protocol == "tftp" or protocol == "ftp"):
            transfer_status = cnos.doStartupConfigBackUp(protocol, tftptimeout, rcserverip, rcpath, serveruser, serverpwd, remote_conn)
        elif(protocol == "sftp" or protocol == "scp"):
            transfer_status = cnos.doSecureStartupConfigBackUp(protocol, timeout, rcserverip, rcpath, serveruser, serverpwd, remote_conn)
        else:
            transfer_status = "Invalid Protocol option"
    else:
        transfer_status = "Invalid configType Option"
    
    output = output + "\n Config Back Up status \n" + transfer_status 

    # Save it into the file
    file = open(outputfile, "a")
    file.write(output)
    file.close()
    
    # Logic to check when changes occur or not
    errorMsg = cnos.checkOutputForError(output)
    if(errorMsg == None):
        module.exit_json(changed=True, msg="Config file tranferred to server")
    else:
        module.fail_json(msg=errorMsg)
    
    
if __name__ == '__main__':
        main()
