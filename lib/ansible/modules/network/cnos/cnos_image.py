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
# Module to download new image to Lenovo Switches
# Lenovo Networking
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cnos_image
author: "Dave Kasberg (@dkasberg)"
short_description: Perform firmware upgrade/download from a remote server on devices running Lenovo CNOS
description:
    - This module allows you to work with switch firmware images. It provides a way to download a firmware image
     to a network device from a remote server using FTP, SFTP, TFTP, or SCP. The first step is to create a directory
     from where the remote server can be reached. The next step is to provide the full file path of the image's
     location. Authentication details required by the remote server must be provided as well. By default, this
     method makes the newly downloaded firmware image the active image, which will be used by the switch during the
     next restart.
     This module uses SSH to manage network device configuration.
     The results of the operation will be placed in a directory named 'results'
     that must be created by the user in their local directory to where the playbook is run.
     For more information about this module from Lenovo and customizing it usage for your
     use cases, please visit U(http://systemx.lenovofiles.com/help/index.jsp?topic=%2Fcom.lenovo.switchmgt.ansible.doc%2Fcnos_image.html)
version_added: "2.3"
extends_documentation_fragment: cnos
options:
    protocol:
        description:
            - This refers to the protocol used by the network device to interact with the remote server from where
             to download the firmware image. The choices are FTP, SFTP, TFTP, or SCP. Any other protocols will
             result in error. If this parameter is not specified, there is no default value to be used.
        required: true
        default: null
        choices: [SFTP, SCP, FTP, TFTP]
    serverip:
        description:
            - This specifies the IP Address of the remote server from where the software image will be downloaded.
        required: true
        default: null
    imgpath:
        description:
            - This specifies the full file path of the image located on the remote server. In case the relative path
             is used as the variable value, the root folder for the user of the server needs to be specified.
        required: true
        default: null
    imgtype:
        description:
            - This specifies the firmware image type to be downloaded
        required: true
        default: null
        choices: [all, boot, os, onie]
    serverusername:
        description:
            - Specify the username for the server relating to the protocol used.
        required: true
        default: null
    serverpassword:
        description:
            - Specify the password for the server relating to the protocol used.
        required: false
        default: null
'''
EXAMPLES = '''
Tasks : The following are examples of using the module cnos_image. These are written in the main.yml file of the tasks directory.
---
- name: Test Image transfer
  cnos_image:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_image_{{ inventory_hostname }}_output.txt"
      protocol: "sftp"
      serverip: "10.241.106.118"
      imgpath: "/root/cnos_images/G8272-10.1.0.112.img"
      imgtype: "os"
      serverusername: "root"
      serverpassword: "root123"

- name: Test Image tftp
  cnos_image:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_image_{{ inventory_hostname }}_output.txt"
      protocol: "tftp"
      serverip: "10.241.106.118"
      imgpath: "/anil/G8272-10.2.0.34.img"
      imgtype: "os"
      serverusername: "root"
      serverpassword: "root123"
'''
RETURN = '''
msg:
  description: Success or failure message
  returned: always
  type: string
  sample: "Image file tranferred to device"
'''

import sys
try:
    import paramiko
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False
import time
import socket
import array
import json
import time
import re
try:
    from ansible.module_utils.network.cnos import cnos
    HAS_LIB = True
except:
    HAS_LIB = False
from ansible.module_utils.basic import AnsibleModule
from collections import defaultdict


def main():
    module = AnsibleModule(
        argument_spec=dict(
            outputfile=dict(required=True),
            host=dict(required=True),
            username=dict(required=True),
            password=dict(required=True, no_log=True),
            enablePassword=dict(required=False, no_log=True),
            deviceType=dict(required=True),
            protocol=dict(required=True),
            serverip=dict(required=True),
            imgpath=dict(required=True),
            imgtype=dict(required=True),
            serverusername=dict(required=False),
            serverpassword=dict(required=False, no_log=True),),
        supports_check_mode=False)

    username = module.params['username']
    password = module.params['password']
    enablePassword = module.params['enablePassword']
    outputfile = module.params['outputfile']
    host = module.params['host']
    deviceType = module.params['deviceType']
    protocol = module.params['protocol'].lower()
    imgserverip = module.params['serverip']
    imgpath = module.params['imgpath']
    imgtype = module.params['imgtype']
    imgserveruser = module.params['serverusername']
    imgserverpwd = module.params['serverpassword']
    output = ""
    timeout = 120
    tftptimeout = 600
    if not HAS_PARAMIKO:
        module.fail_json(msg='paramiko is required for this module')

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

    # Enable and enter configure terminal then send command
    output = output + cnos.waitForDeviceResponse("\n", ">", 2, remote_conn)

    output = output + cnos.enterEnableModeForDevice(enablePassword, 3, remote_conn)

    # Make terminal length = 0
    output = output + cnos.waitForDeviceResponse("terminal length 0\n", "#", 2, remote_conn)

    transfer_status = ""
    # Invoke method for image transfer from server
    if(protocol == "tftp" or protocol == "ftp"):
        transfer_status = cnos.doImageTransfer(protocol, tftptimeout, imgserverip, imgpath, imgtype, imgserveruser, imgserverpwd, remote_conn)
    elif(protocol == "sftp" or protocol == "scp"):
        transfer_status = cnos.doSecureImageTransfer(protocol, timeout, imgserverip, imgpath, imgtype, imgserveruser, imgserverpwd, remote_conn)
    else:
        transfer_status = "Invalid Protocol option"

    output = output + "\n Image Transfer status \n" + transfer_status

    # Save it into the file
    file = open(outputfile, "a")
    file.write(output)
    file.close()

    # Logic to check when changes occur or not
    errorMsg = cnos.checkOutputForError(output)
    if(errorMsg is None):
        module.exit_json(changed=True, msg="Image file tranferred to device")
    else:
        module.fail_json(msg=errorMsg)

if __name__ == '__main__':
    main()
