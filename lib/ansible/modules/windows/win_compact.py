#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Micah Hunsberger (@mhunsber)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_compact
version_added: '2.9'
short_description: Alters the compression of directories on NTFS partitions.
description:
  - This module sets the compressed attribute for directories on an NTFS file system.
  - NTFS compression can be used to save disk space.
options:
  state:
    path:
      - The full path of the directory to modify.
      - The folder must exist on an NTFS FileSystem.
    required: yes
    type: path
  compressed:
    description:
      - The compressed state of the directory.
    type: bool
    default: true
  recurse:
    description:
      - Whether to recursively apply changes to all subdirectories and files.
      - When set to C(false), only applies changes to I(path).
      - When set to C(true), applies changes to I(path) and all subdirectories and files.
    type: bool
    default: false
author:
  - Micah Hunsberger (@mhunsber)
notes:
  - C(win_compact) does not create a zip archive file.
  - For more about NTFS Compression, see U(http://www.ntfs.com/ntfs-compressed.htm)
'''

EXAMPLES = r'''
- name: Compress log files directory
  win_compact:
    path: C:\Logs
    compressed: yes
    recurse: no

- name: Decompress log files directory
  win_compact:
    path: C:\Logs
    compressed: no
    recurse: no

- name: Compress reports directory and all subdirectories
  win_compact:
    path: C:\business\reports
    compressed: yes
    recurse: yes
'''

RETURN = r'''
rc:
  description: The return code of the compress/uncompress operation.
    If no changes are made or the operation is successful, rc is 0.
  returned: always
  sample: 0
  type: int
'''
