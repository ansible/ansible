#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'core'}

DOCUMENTATION = '''
module: win_disk_image
short_description: Manage ISO/VHD/VHDX mounts on Windows hosts
version_added: '2.3'
description:
     - Manages mount behavior for a specified ISO, VHD, or VHDX image on a Windows host. When C(state) is C(present),
       the image will be mounted under a system-assigned drive letter, which will be returned in the C(mount_path) value
       of the module result. Requires Windows 8+ or Windows Server 2012+.
options:
  image_path:
    description:
      - Path to an ISO, VHD, or VHDX image on the target Windows host (the file cannot reside on a network share)
    required: yes
  state:
    description:
      - Whether the image should be present as a drive-letter mount or not.
    choices: [ absent, present ]
    default: present
author:
    - Matt Davis (@nitzmahone)
'''

RETURN = r'''
mount_path:
    description: filesystem path where the target image is mounted
    returned: when C(state) is C(present)
    type: string
    sample: F:\
'''

EXAMPLES = r'''
# Run installer from mounted ISO, then unmount
- name: Ensure an ISO is mounted
  win_disk_image:
    image_path: C:\install.iso
    state: present
  register: disk_image_out

- name: Run installer from mounted iso
  win_package:
    path: '{{ disk_image_out.mount_path }}setup\setup.exe'
    product_id: 35a4e767-0161-46b0-979f-e61f282fee21
    state: present

- name: Unmount iso
  win_disk_image:
    image_path: C:\install.iso
    state: absent
'''
