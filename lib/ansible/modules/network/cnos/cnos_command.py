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
# Module to send CLI commands to Lenovo Switches
# Lenovo Networking
#
#---- Documentation Start ----------------------------------------------------#
DOCUMENTATION = '''
---
module: cnos_command
short_description: Run a single CNOS Command on Devices.
description: 
    - Manages network device configurations over SSH. This module allows implementors to work with the device 
     running-config. It provides a way to push a CNOS command onto a network device by evaluating the current 
     running-config and only pushing configuration commands that are not already configured. The command is 
     passed as an argument to the method
version_added: "2.3"
options:
    clicommand:
        description:
            - Specify the CLI command as an attribute to this method. Pass on the command in double quotes. 
             The variables can also be placed directly on to CLIs or can come from the vars folder.
        required: true
        default: null
    
notes:
    - For help in developing on modules, should you be so inclined, please read 
     Community Information & Contributing, Helping Testing PRs and Developing Modules.

Module Dependency :
    1. cnos_command.py
    2. cnos.py 

'''
EXAMPLES = '''
#The tasks/main.yml will look like this
---
- name: Test Command
  cnos_command: host={{ inventory_hostname }}  username={{ hostvars[inventory_hostname]['username']}} password={{ hostvars[inventory_hostname]['password']}} deviceType={{ hostvars[inventory_hostname]['deviceType']}} clicommand='{{item.clicommand}}' enablePassword='{{item.enablePassword}}' outputfile=./results/cnos_command_{{ inventory_hostname }}_output.txt
  with_items: "{{test_runcommand_data1}}"

#Inside vars/main.yml will look like this
---
test_runcommand_data1:
  - {enablePassword: "anil", clicommand: "display users"}
  
#In the inventory file u specify as 
inventory sample: |
    [cnos_command_sample]
    10.240.178.74  username=<username> password=<password> deviceType=g8272_cnos 


'''

RETURN = '''
return value: |
    On successful execution, the method returns and empty string with a message "Command Applied" in json format. 
    But upon any failure, the output will be the error display string.

'''
#---- Documentation Ends ----------------------------------------------------#
#---- Logic Start ------------------------------------------------------------#

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
            clicommand=dict(required=True),
            outputfile=dict(required=True),
            host=dict(required=True),
            deviceType=dict(required=True),
            username=dict(required=True),
            password=dict(required=True,no_log=True),
            enablePassword=dict(required=False,no_log=True),),
        supports_check_mode=False)

    username = module.params['username']
    password = module.params['password']
    enablePassword = module.params['enablePassword']
    cliCommand= module.params['clicommand']
    deviceType = module.params['deviceType']
    outputfile =  module.params['outputfile']
    hostIP = module.params['host']
    output = ""

    # Create instance of SSHClient object
    remote_conn_pre = paramiko.SSHClient()

    # Automatically add untrusted hosts (make sure okay for security policy in your environment)
    remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # initiate SSH connection with the switch
    remote_conn_pre.connect(hostIP, username=username, password=password)
    time.sleep(2)
    
    # Use invoke_shell to establish an 'interactive session'
    remote_conn = remote_conn_pre.invoke_shell()
    time.sleep(2)
    
    # Enable and enter configure terminal then send command
    output = output + cnos.waitForDeviceResponse("\n",">", 2, remote_conn)
    
    output = output + cnos.enterEnableModeForDevice(enablePassword, 3, remote_conn)
            
    #Make terminal length = 0
    output = output + cnos.waitForDeviceResponse("terminal length 0\n","#", 2, remote_conn)
        
    #Go to config mode
    output = output + cnos.waitForDeviceResponse("configure d\n","(config)#", 2, remote_conn)
	
    #Send the CLi command
    output = output + cnos.waitForDeviceResponse(cliCommand +"\n","(config)#", 2, remote_conn)
	
    #Save it into the file
    file = open(outputfile, "a")
    file.write(output)
    file.close()
    
    # Logic to check when changes occur or not
    errorMsg = cnos.checkOutputForError(output)
    if(errorMsg == None):
        module.exit_json(changed=True, msg="CLI command executed and results saved in file ")
    else:
        module.fail_json(msg=errorMsg)
    

if __name__ == '__main__':
        main()
                                   
