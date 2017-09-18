#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Jon Hawkesworth (@jhawkesworth) <figs@unity.demon.co.uk>
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
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = r'''
---
module: win_file
version_added: "1.9.2"
short_description: Creates, touches or removes files, directories or links
description:
  - Sets attributes of files, symlinks, hard links, junction points and directory.
  - Can create files, symlinks, hard links, junction points, directories and files.
  - Unlike M(file), does not modify ownership or permissions.
notes:
  - For non-Windows targets, use the M(file) module instead.
  - See also M(win_copy), M(win_template), M(copy), M(template), M(assemble)
author: "Jon Hawkesworth (@jhawkesworth)"
options:
  force:
    description:
      - This flag indicates whether to force the creation of a link in the
        following cases.
      - If state=C(link) and C(path) exists and is not a symbolic link, the
        C(path) will be deleted and set as a new symbolic link.
      - If state=C(junction) and C(path) exists and is not a junction point,
        the C(path) will be deleted and set as a new junction point.
      - If state=C(hard) and C(path) exists and is not a hard link of C(src),
        the C(path) will be deleted and set as a new hard link.
    type: bool
    default: 'no'
    version_added: "2.4"
  path:
    description:
      - The path to the file being managed.
    required: true
    aliases: ['dest', 'name']
  src:
    description:
      - The path of the file to link to (applies only to
        I(state=link/junction/hard)).
      - If I(state=junction) this needs to be a directory.
      - If I(state=hard) this needs to be a file.
    version_added: "2.4"
  state:
    description:
      - If C(directory), all immediate subdirectories will be created if they
        do not exist.
      - If C(file), the file will NOT be created if it does not exist, see the M(copy)
        or M(template) module if you want that behavior.  If C(absent),
        directories will be recursively deleted, and files will be removed.
      - If C(touch), an empty file will be created if the C(path) does not
        exist, while an existing file or directory will receive updated
        modification times (similar to the way C(touch) works from the command line).
      - If C(link) a symbolic link (soft link) will be created or changed. Added in 2.4.
      - If C(junction) a junction point will be created or changed. Added in 2.4.
      - If C(hard) a hard link will be created. Added in 2.4.
    choices: [ file, directory, touch, absent, link, junction, hard ]
'''

EXAMPLES = r'''
- name: Touch a file (creates if not present, updates modification time if present)
  win_file:
    path: C:\Temp\foo.conf
    state: touch

- name: Remove a file, if present
  win_file:
    path: C:\Temp\foo.conf
    state: absent

- name: Create directory structure
  win_file:
    path: C:\Temp\folder\subfolder
    state: directory

- name: Remove directory structure
  win_file:
    path: C:\Temp
    state: absent

- name: Create a directory symbolic link
  win_file:
    path: C:\Temp\link
    src: C:\LinkSource
    state: link

- name: Force C:\Temp\link to be a directory symbolic link
  win_file:
    force: True
    path: C:\Temp\link
    src: C:\LinkSource
    state: link

- name: Create a file symbolic link
  win_file:
    path: C:\Temp\file-link.txt
    src: C:\Dev\file.txt
    state: link

- name: Create a junction point
  win_file:
    path: C:\Temp\junction-point
    src: C:\Dev\junction-source
    state: hard

- name: Create a hard link
  win_file:
    path: C:\Temp\hard-link
    src: C:\Dev\hard-source
    state: hard
'''
