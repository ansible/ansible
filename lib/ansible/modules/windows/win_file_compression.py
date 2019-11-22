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
module: win_file_compression
version_added: '2.10'
short_description: Alters the compression of files and directories on NTFS partitions.
description:
  - This module sets the compressed attribute for files and directories on a filesystem that supports it like NTFS.
  - NTFS compression can be used to save disk space.
options:
  path:
    description:
      - The full path of the file or directory to modify.
      - The path must exist on file system that supports compression like NTFS.
    required: yes
    type: path
  state:
    description:
      - Set to C(present) to ensure the I(path) is compressed.
      - Set to C(absent) to ensure the I(path) is not compressed.
    type: str
    choices:
      - absent
      - present
    default: present
  recurse:
    description:
      - Whether to recursively apply changes to all subdirectories and files.
      - This option only has an effect when I(path) is a directory.
      - When set to C(false), only applies changes to I(path).
      - When set to C(true), applies changes to I(path) and all subdirectories and files.
    type: bool
    default: false
  force:
    description:
      - This option only has an effect when I(recurse) is C(true)
      - If C(true), will check the compressed state of all subdirectories and files
        and make a change if any are different from I(compressed).
      - If C(false), will only make a change if the compressed state of I(path) is different from I(compressed).
      - If the folder structure is complex or contains a lot of files, it is recommended to set this
        option to C(false) so that not every file has to be checked.
    type: bool
    default: true
author:
  - Micah Hunsberger (@mhunsber)
notes:
  - C(win_file_compression) sets the file system's compression state, it does not create a zip archive file.
  - For more about NTFS Compression, see U(http://www.ntfs.com/ntfs-compressed.htm)
'''

EXAMPLES = r'''
- name: Compress log files directory
  win_file_compression:
    path: C:\Logs
    state: present

- name: Decompress log files directory
  win_file_compression:
    path: C:\Logs
    state: absent

- name: Compress reports directory and all subdirectories
  win_file_compression:
    path: C:\business\reports
    state: present
    recurse: yes

# This will only check C:\business\reports for the compressed state
# If C:\business\reports is compressed, it will not make a change
# even if one of the child items is uncompressed

- name: Compress reports directory and all subdirectories (quick)
  win_file_compression:
    path: C:\business\reports
    compressed: yes
    recurse: yes
    force: no
'''

RETURN = r'''
rc:
  description:
    - The return code of the compress/uncompress operation.
    - If no changes are made or the operation is successful, rc is 0.
  returned: always
  sample: 0
  type: int
'''
