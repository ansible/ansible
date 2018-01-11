#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Red Hat, Inc.
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
module: win_disk_image
short_description: Manage ISO/VHD/VHDX mounts on Windows hosts
version_added: 2.3
description:
     - Manages mount behavior for a specified ISO, VHD, or VHDX image on a Windows host. When C(state) is C(present),
       the image will be mounted under a system-assigned drive letter, which will be returned in the C(mount_path) value
       of the module result. Requires Windows 8+ or Windows Server 2012+.
options:
  image_path:
    description:
      - path to an ISO, VHD, or VHDX image on the target Windows host (the file cannot reside on a network share)
    required: true
  state:
    description:
      - whether the image should be present as a drive-letter mount or not.
    choices:
      - present
      - absent
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
# ensure an iso is mounted
- win_disk_image:
    image_path: C:\install.iso
    state: present
  register: disk_image_out

# run installer from mounted iso
- win_package:
    path: '{{ disk_image_out.mount_path }}setup\setup.exe'
    product_id: '35a4e767-0161-46b0-979f-e61f282fee21'
    state: present

# unmount iso
- win_disk_image:
    image_path: C:\install.iso
    state: absent

'''
