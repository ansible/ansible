#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Aameer Raza <mail2aameer@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_linux_copy
version_added: "2.4"
short_description: This module can be used to copy files /folders from linux to windows or vice-versa.
description:
    - Copy files and folders from windows to linux or vice-versa.
    
options:
  src:
    description:
      - This switch accepts the IP / FQDN of the source host.
    type: str
  dist:
    description:
      - This switch accepts the IP / FQDN of the destination host.
    type: str
  src_path:
    description:
      - This switch accepts the path of the source.
    type: str
  dest_path:
    description:
      - This switch accepts the path of the destination.
    type: str
  usr:
    description:
      - This switch expects the Linux / Unix user's name.
    type: str
  pass:
    description:
      - This switch expects the Linux / Unix password.
    type: str  
  flow:
    description:
      - This switch expects the direction of data to be copied. Use w2l for copying data from windows to Linux / unix and l2w for Linux to windows.
    type: str
    choices: [w2l, l2w ]
    
notes:
- This module uses putty Secure Copy client application to copy the data, hence putty must be installed.
requirements:
- Putty must be installed in windows box.
author:
- Aameer Raza (@connect2aameer)
'''

EXAMPLES = r'''
- name: Copy from Windows to Linux.
  win_linux_copy:
    dist: 10.0.0.1
    src_path: c:\users\aameer\example_folder
    dest_path: /home/aameer
    flow: w2l
    usr: root
    pass: root_password

- name: Copy from Linux to Windows.
  win_linux_copy:
    src: linux.ansible.com
    src_path: /home/aameer/example_folder
    dest_path: c:\users\aameer
    flow: l2w
    usr: root
    pass: root_password
'''

RETURN = r'''
changed:
    description: True when the data is copied.
    returned: Always.
    type: bool
    sample: true
rc:
    description: The return code from the execution.
    returned: always.
    type: int
    sample: 0
msg:
    description: The output/ error message from the execution.
    returned: always.
    type: str
    sample: data.txt                  | 0 kB |   0.1 kB/s | ETA: 00:00:00 | 100%

'''
