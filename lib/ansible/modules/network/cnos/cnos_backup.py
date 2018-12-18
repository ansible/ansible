#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cnos_backup
author: "Anil Kumar Muraleedharan (@amuraleedhar)"
short_description: Backup the current running or startup configuration to a
 remote server on devices running Lenovo CNOS
description:
    - This module allows you to work with switch configurations. It provides a
     way to back up the running or startup configurations of a switch to a
     remote server. This is achieved by periodically saving a copy of the
     startup or running configuration of the network device to a remote server
     using FTP, SFTP, TFTP, or SCP. The first step is to create a directory from
     where the remote server can be reached. The next step is to provide the
     full file path of the location where the configuration will be backed up.
     Authentication details required by the remote server must be provided as
     well. This module uses SSH to manage network device configuration.
     The results of the operation will be placed in a directory named 'results'
     that must be created by the user in their local directory to where the
     playbook is run.
version_added: "2.3"
extends_documentation_fragment: cnos
options:
    configType:
        description:
            - This specifies what type of configuration will be backed up. The
             choices are the running or startup configurations. There is no
             default value, so it will result in an error if the input is
             incorrect.
        required: Yes
        default: Null
        choices: [running-config, startup-config]
    protocol:
        description:
            - This refers to the protocol used by the network device to
             interact with the remote server to where to upload the backup
             configuration. The choices are FTP, SFTP, TFTP, or SCP. Any other
             protocols will result in error. If this parameter is
             not specified, there is no default value to be used.
        required: Yes
        default: Null
        choices: [SFTP, SCP, FTP, TFTP]
    rcserverip:
        description:
            -This specifies the IP Address of the remote server to where the
            configuration will be backed up.
        required: Yes
        default: Null
    rcpath:
        description:
            - This specifies the full file path where the configuration file
             will be copied on the remote server. In case the relative path is
             used as the variable value, the root folder for the user of the
             server needs to be specified.
        required: Yes
        default: Null
    serverusername:
        description:
            - Specify the username for the server relating to the protocol
             used.
        required: Yes
        default: Null
    serverpassword:
        description:
            - Specify the password for the server relating to the protocol
             used.
        required: Yes
        default: Null
'''
EXAMPLES = '''
Tasks : The following are examples of using the module cnos_backup.
 These are written in the main.yml file of the tasks directory.
---
- name: Test Running Config Backup
  cnos_backup:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      outputfile: "./results/test_backup_{{ inventory_hostname }}_output.txt"
      configType: running-config
      protocol: "sftp"
      serverip: "10.241.106.118"
      rcpath: "/root/cnos/G8272-running-config.txt"
      serverusername: "root"
      serverpassword: "root123"

- name: Test Startup Config Backup
  cnos_backup:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      outputfile: "./results/test_backup_{{ inventory_hostname }}_output.txt"
      configType: startup-config
      protocol: "sftp"
      serverip: "10.241.106.118"
      rcpath: "/root/cnos/G8272-startup-config.txt"
      serverusername: "root"
      serverpassword: "root123"

- name: Test Running Config Backup -TFTP
  cnos_backup:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      outputfile: "./results/test_backup_{{ inventory_hostname }}_output.txt"
      configType: running-config
      protocol: "tftp"
      serverip: "10.241.106.118"
      rcpath: "/anil/G8272-running-config.txt"
      serverusername: "root"
      serverpassword: "root123"

- name: Test Startup Config Backup - TFTP
  cnos_backup:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      outputfile: "./results/test_backup_{{ inventory_hostname }}_output.txt"
      configType: startup-config
      protocol: "tftp"
      serverip: "10.241.106.118"
      rcpath: "/anil/G8272-startup-config.txt"
      serverusername: "root"
      serverpassword: "root123"

'''
RETURN = '''
msg:
  description: Success or failure message
  returned: always
  type: str
  sample: "Config file tranferred to server"
'''

import sys
import time
import socket
import array
import json
import time
import re
import os
try:
    from ansible.module_utils.network.cnos import cnos
    HAS_LIB = True
except Exception:
    HAS_LIB = False
from ansible.module_utils.basic import AnsibleModule
from collections import defaultdict


# Utility Method to back up the running config or start up copnfig
# This method supports only SCP or SFTP or FTP or TFTP
# Tuning of timeout parameter is pending
def doConfigBackUp(module, prompt, answer):
    host = module.params['host']
    server = module.params['serverip']
    username = module.params['serverusername']
    password = module.params['serverpassword']
    protocol = module.params['protocol'].lower()
    rcPath = module.params['rcpath']
    configType = module.params['configType']
    confPath = rcPath + host + '_' + configType + '.txt'

    retVal = ''

    # config backup command happens here
    command = "copy " + configType + " " + protocol + " " + protocol + "://"
    command = command + username + "@" + server + "/" + confPath
    command = command + " vrf management\n"
    cnos.debugOutput(command + "\n")
    # cnos.checkForFirstTimeAccess(module, command, 'yes/no', 'yes')
    cmd = []
    if(protocol == "scp"):
        scp_cmd1 = [{'command': command, 'prompt': 'timeout:', 'answer': '0'}]
        scp_cmd2 = [{'command': '\n', 'prompt': 'Password:',
                     'answer': password}]
        cmd.extend(scp_cmd1)
        cmd.extend(scp_cmd2)
        retVal = retVal + str(cnos.run_cnos_commands(module, cmd))
    elif(protocol == "sftp"):
        sftp_cmd = [{'command': command, 'prompt': 'Password:',
                     'answer': password}]
        cmd.extend(sftp_cmd)
        retVal = retVal + str(cnos.run_cnos_commands(module, cmd))
    elif(protocol == "ftp"):
        ftp_cmd = [{'command': command, 'prompt': 'Password:',
                    'answer': password}]
        cmd.extend(ftp_cmd)
        retVal = retVal + str(cnos.run_cnos_commands(module, cmd))
    elif(protocol == "tftp"):
        command = "copy " + configType + " " + protocol + " " + protocol
        command = command + "://" + server + "/" + confPath
        command = command + " vrf management\n"
        # cnos.debugOutput(command)
        tftp_cmd = [{'command': command, 'prompt': None, 'answer': None}]
        cmd.extend(tftp_cmd)
        retVal = retVal + str(cnos.run_cnos_commands(module, cmd))
    else:
        return "Error-110"

    return retVal
# EOM


def main():

    module = AnsibleModule(
        argument_spec=dict(
            outputfile=dict(required=True),
            host=dict(required=False),
            username=dict(required=False),
            password=dict(required=False, no_log=True),
            enablePassword=dict(required=False, no_log=True),
            deviceType=dict(required=True),
            configType=dict(required=True),
            protocol=dict(required=True),
            serverip=dict(required=True),
            rcpath=dict(required=True),
            serverusername=dict(required=False),
            serverpassword=dict(required=False, no_log=True),),
        supports_check_mode=False)

    outputfile = module.params['outputfile']
    protocol = module.params['protocol'].lower()
    output = ''
    if(protocol == "tftp" or protocol == "ftp" or
       protocol == "sftp" or protocol == "scp"):
        transfer_status = doConfigBackUp(module, None, None)
    else:
        transfer_status = "Invalid Protocol option"

    output = output + "\n Config Back Up status \n" + transfer_status

    # Save it into the file
    path = outputfile.rsplit('/', 1)
    # cnos.debugOutput(path[0])
    if not os.path.exists(path[0]):
        os.makedirs(path[0])
    file = open(outputfile, "a")
    file.write(output)
    file.close()

    # Logic to check when changes occur or not
    errorMsg = cnos.checkOutputForError(output)
    if(errorMsg is None):
        module.exit_json(changed=True, msg="Config file tranferred to server")
    else:
        module.fail_json(msg=errorMsg)


if __name__ == '__main__':
    main()
