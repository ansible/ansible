#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Corwin Brown <blakfeld@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_robocopy
version_added: '2.2'
short_description: Synchronizes the contents of two directories using Robocopy
description:
- Synchronizes the contents of files/directories from a source to destination.
- Under the hood this just calls out to RoboCopy, since that should be available
  on most modern Windows systems.
options:
  src:
    description:
    - Source file/directory to sync.
    type: path
    required: yes
  dest:
    description:
    - Destination file/directory to sync (Will receive contents of src).
    type: path
    required: yes
  recurse:
    description:
    - Includes all subdirectories (Toggles the C(/e) flag to RoboCopy).
    - If C(flags) is set, this will be ignored.
    type: bool
    default: no
  purge:
    description:
    - Deletes any files/directories found in the destination that do not exist in the source.
    - Toggles the C(/purge) flag to RoboCopy.
    - If C(flags) is set, this will be ignored.
    type: bool
    default: no
  flags:
    description:
      - Directly supply Robocopy flags.
      - If set, C(purge) and C(recurse) will be ignored.
    type: str
notes:
- This is not a complete port of the M(synchronize) module. Unlike the M(synchronize) module this only performs the sync/copy on the remote machine,
  not from the master to the remote machine.
- This module does not currently support all Robocopy flags.
seealso:
- module: synchronize
- module: win_copy
author:
- Corwin Brown (@blakfeld)
'''

EXAMPLES = r'''
- name: Sync the contents of one directory to another
  win_robocopy:
    src: C:\DirectoryOne
    dest: C:\DirectoryTwo

- name: Sync the contents of one directory to another, including subdirectories
  win_robocopy:
    src: C:\DirectoryOne
    dest: C:\DirectoryTwo
    recurse: yes

- name: Sync the contents of one directory to another, and remove any files/directories found in destination that do not exist in the source
  win_robocopy:
    src: C:\DirectoryOne
    dest: C:\DirectoryTwo
    purge: yes

- name: Sync content in recursive mode, removing any files/directories found in destination that do not exist in the source
  win_robocopy:
    src: C:\DirectoryOne
    dest: C:\DirectoryTwo
    recurse: yes
    purge: yes

- name: Sync two directories in recursive and purging mode, specifying additional special flags
  win_robocopy:
    src: C:\DirectoryOne
    dest: C:\DirectoryTwo
    flags: /E /PURGE /XD SOME_DIR /XF SOME_FILE /MT:32

- name: Sync one file from a remote UNC path in recursive and purging mode, specifying additional special flags
  win_robocopy:
    src: \\Server1\Directory One
    dest: C:\DirectoryTwo
    flags: file.zip /E /PURGE /XD SOME_DIR /XF SOME_FILE /MT:32
'''

RETURN = r'''
cmd:
    description: The used command line.
    returned: always
    type: str
    sample: robocopy C:\DirectoryOne C:\DirectoryTwo /e /purge
src:
    description: The Source file/directory of the sync.
    returned: always
    type: str
    sample: C:\Some\Path
dest:
    description: The Destination file/directory of the sync.
    returned: always
    type: str
    sample: C:\Some\Path
recurse:
    description: Whether or not the recurse flag was toggled.
    returned: always
    type: bool
    sample: false
purge:
    description: Whether or not the purge flag was toggled.
    returned: always
    type: bool
    sample: false
flags:
    description: Any flags passed in by the user.
    returned: always
    type: str
    sample: /e /purge
rc:
    description: The return code returned by robocopy.
    returned: success
    type: int
    sample: 1
output:
    description: The output of running the robocopy command.
    returned: success
    type: str
    sample: "------------------------------------\\n   ROBOCOPY     ::     Robust File Copy for Windows         \\n------------------------------------\\n "
msg:
    description: Output interpreted into a concise message.
    returned: always
    type: str
    sample: No files copied!
'''
