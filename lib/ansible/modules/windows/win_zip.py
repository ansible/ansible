#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_zip
version_added: "2.10"
short_description: Zip a file or directory (recursively)
description:
    - Zips a single file into a zip file, or a directory (recursively) into a zip file.
    - For non-Windows targets, use the M(archive) module instead.
requirements:
    - .NET 4.5 or higher
    - PowerShell 5.0 or higher
notes:
    - The underlying PowerShell and .NET libraries impose a limit on the max file size (2GB) that can be compressed.
    - The module scans the source (recursively for directories) before zipping and fails with an error if any are over the maximum size.
    - Due to limitations in Windows COM Shell.Application, only the NET and PowerShell versions listed are supported.
    - Check Mode is supported
options:
    creates:
        description:
            - If this file or directory exists the specified dest will not be created.
        type: str
        required: false
    delete_src:
        description:
            - Whether to delete the source file or directory after source is zipped.  Directories are deleted recursively.
        type: bool
        required: false
        default: false
        aliases: [ rm ]
    dest:
        description:
            - The absolute path of the zip file to create.
        type: str
        required: true
        aliases: [ zip_file ]
    src:
        description:
            - The absolute path of the file or directory to zip.
        type: str
        required: true
        aliases: [ path ]
author:
    - Jim Ficarra (@jimfic)
'''

EXAMPLES = r'''
- name: Zip up single file
  win_zip:
   src: "c:\\mydir\\myfile.txt"
   dest: "c:\\archivepath\\myfile.zip"

- name: Zip up a directory
  win_zip:
    src: "c:\\mydir"
    dest: "c:\\archivepath\\mydir.zip"

- name: Zip up a directory and delete the source
  win_zip:
    src: "c:\\mydir"
    dest: "c:\\archivepath\\mydir.zip"
    delete_src: true
'''

RETURN = r'''
dest:
    description: The specified target zip file
    returned: always
    type: str
    sample: "c:\\archivepath\\myfile.zip"
large_files:
    description: A list of files that exceeded maximum size
    returned: failure
    type: list
    sample:
src:
    description: The specified source for compression
    returned: always
    type: str
    sample: "c:\\mydir"
source_deleted:
    description: Whether the source path specified in the src attribute was deleted
    returned: always
    type: bool
    sample: false
utils_used:
    description: Which underlying tools were used (PowerShell or .NET)
    returned: always
    type: str
    sample: "PowerShell"
'''
