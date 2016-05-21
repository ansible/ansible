#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Corwin Brown <blakfeld@gmail.com>
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

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

DOCUMENTATION = """
---
module: win_robocopy
version_added: "2.2"
short_description: Synchronizes the contents of two directories using Robocopy.
description:
    - Synchronizes the contents of two directories on the remote machine. Under the hood this just calls out to RoboCopy, since that should be available on most modern Windows Systems.
options:
  src:
    description:
      - Source file/directory to sync.
    required: true
  dest:
    description:
      - Destination file/directory to sync (Will receive contents of src).
    required: true
  recurse:
    description:
      - Includes all subdirectories (Toggles the `/e` flag to RoboCopy). If "flags" is set, this will be ignored.
    choices:
      - true
      - false
    defaults: false
    required: false
  purge:
    description:
      - Deletes any files/directories found in the destination that do not exist in the source (Toggles the `/purge` flag to RoboCopy). If "flags" is set, this will be ignored.
    choices:
      - true
      - false
    defaults: false
    required: false
  flags:
    description:
      - Directly supply Robocopy flags. If set, purge and recurse will be ignored.
    default: None
    required: false
author: Corwin Brown (@blakfeld)
notes:
    - This is not a complete port of the "synchronize" module. Unlike the "synchronize" module this only performs the sync/copy on the remote machine, not from the master to the remote machine.
    - This module does not currently support all Robocopy flags.
    - Works on Windows 7, Windows 8, Windows Server 2k8, and Windows Server 2k12
"""

EXAMPLES = """
# Syncs the contents of one diretory to another.
$ ansible -i hosts all -m win_robocopy -a "src=C:\\DirectoryOne dest=C:\\DirectoryTwo"

# Sync the contents of one directory to another, including subdirectories.
$ ansible -i hosts all -m win_robocopy -a "src=C:\\DirectoryOne dest=C:\\DirectoryTwo recurse=true"

# Sync the contents of one directory to another, and remove any files/directories found in destination that do not exist in the source.
$ ansible -i hosts all -m win_robocopy -a "src=C:\\DirectoryOne dest=C:\\DirectoryTwo purge=true"

# Sample sync
---
- name: Sync Two Directories
  win_robocopy:
    src: "C:\\DirectoryOne
    dest: "C:\\DirectoryTwo"
    recurse: true
    purge: true

---
- name: Sync Two Directories
  win_robocopy:
    src: "C:\\DirectoryOne
    dest: "C:\\DirectoryTwo"
    recurse: true
    purge: true
    flags: '/XD SOME_DIR /XF SOME_FILE /MT:32'
"""

RETURN = '''
src:
    description: The Source file/directory of the sync.
    returned: always
    type: string
    sample: "c:/Some/Path"
dest:
    description: The Destination file/directory of the sync.
    returned: always
    type: string
    sample: "c:/Some/Path"
recurse:
    description: Whether or not the recurse flag was toggled.
    returned: always
    type: bool
    sample: False
purge:
    description: Whether or not the purge flag was toggled.
    returned: always
    type: bool
    sample: False
flags:
    description: Any flags passed in by the user.
    returned: always
    type: string
    sample: "/e /purge"
return_code:
    description: The return code retuned by robocopy.
    returned: success
    type: int
    sample: 1
output:
    description: The output of running the robocopy command.
    returned: success
    type: string
    sample: "-------------------------------------------------------------------------------\n   ROBOCOPY     ::     Robust File Copy for Windows                              \n-------------------------------------------------------------------------------\n"
msg:
    description: Output intrepreted into a concise message.
    returned: always
    type: string
    sample: No files copied!
changed:
    description: Whether or not any changes were made.
    returned: always
    type: bool
    sample: False
'''
