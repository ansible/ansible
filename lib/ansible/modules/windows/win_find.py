#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_find
version_added: "2.3"
short_description: Return a list of files based on specific criteria
description:
    - Return a list of files based on specified criteria.
    - Multiple criteria are AND'd together.
    - For non-Windows targets, use the M(find) module instead.
options:
    age:
        description:
            - Select files or folders whose age is equal to or greater than
              the specified time.
            - Use a negative age to find files equal to or less than
              the specified time.
            - You can choose seconds, minutes, hours, days or weeks
              by specifying the first letter of an of
              those words (e.g., "2s", "10d", 1w").
        type: str
    age_stamp:
        description:
            - Choose the file property against which we compare C(age).
            - The default attribute we compare with is the last modification time.
        type: str
        choices: [ atime, ctime, mtime ]
        default: mtime
    checksum_algorithm:
        description:
            - Algorithm to determine the checksum of a file.
            - Will throw an error if the host is unable to use specified algorithm.
        type: str
        choices: [ md5, sha1, sha256, sha384, sha512 ]
        default: sha1
    file_type:
        description: Type of file to search for.
        type: str
        choices: [ directory, file ]
        default: file
    follow:
        description:
            - Set this to C(yes) to follow symlinks in the path.
            - This needs to be used in conjunction with C(recurse).
        type: bool
        default: no
    get_checksum:
        description:
            - Whether to return a checksum of the file in the return info (default sha1),
              use C(checksum_algorithm) to change from the default.
        type: bool
        default: yes
    hidden:
        description: Set this to include hidden files or folders.
        type: bool
        default: no
    paths:
        description:
            - List of paths of directories to search for files or folders in.
            - This can be supplied as a single path or a list of paths.
        type: list
        required: yes
    patterns:
        description:
            - One or more (powershell or regex) patterns to compare filenames with.
            - The type of pattern matching is controlled by C(use_regex) option.
            - The patterns restrict the list of files or folders to be returned based on the filenames.
            - For a file to be matched it only has to match with one pattern in a list provided.
        type: list
    recurse:
        description:
            - Will recursively descend into the directory looking for files or folders.
        type: bool
        default: no
    size:
        description:
            - Select files or folders whose size is equal to or greater than the specified size.
            - Use a negative value to find files equal to or less than the specified size.
            - You can specify the size with a suffix of the byte type i.e. kilo = k, mega = m...
            - Size is not evaluated for symbolic links.
        type: str
    use_regex:
        description:
            - Will set patterns to run as a regex check if set to C(yes).
        type: bool
        default: no
author:
- Jordan Borean (@jborean93)
'''

EXAMPLES = r'''
- name: Find files in path
  win_find:
    paths: D:\Temp

- name: Find hidden files in path
  win_find:
    paths: D:\Temp
    hidden: yes

- name: Find files in multiple paths
  win_find:
    paths:
    - C:\Temp
    - D:\Temp

- name: Find files in directory while searching recursively
  win_find:
    paths: D:\Temp
    recurse: yes

- name: Find files in directory while following symlinks
  win_find:
    paths: D:\Temp
    recurse: yes
    follow: yes

- name: Find files with .log and .out extension using powershell wildcards
  win_find:
    paths: D:\Temp
    patterns: [ '*.log', '*.out' ]

- name: Find files in path based on regex pattern
  win_find:
    paths: D:\Temp
    patterns: out_\d{8}-\d{6}.log

- name: Find files older than 1 day
  win_find:
    paths: D:\Temp
    age: 86400

- name: Find files older than 1 day based on create time
  win_find:
    paths: D:\Temp
    age: 86400
    age_stamp: ctime

- name: Find files older than 1 day with unit syntax
  win_find:
    paths: D:\Temp
    age: 1d

- name: Find files newer than 1 hour
  win_find:
    paths: D:\Temp
    age: -3600

- name: Find files newer than 1 hour with unit syntax
  win_find:
    paths: D:\Temp
    age: -1h

- name: Find files larger than 1MB
  win_find:
    paths: D:\Temp
    size: 1048576

- name: Find files larger than 1GB with unit syntax
  win_find:
    paths: D:\Temp
    size: 1g

- name: Find files smaller than 1MB
  win_find:
    paths: D:\Temp
    size: -1048576

- name: Find files smaller than 1GB with unit syntax
  win_find:
    paths: D:\Temp
    size: -1g

- name: Find folders/symlinks in multiple paths
  win_find:
    paths:
    - C:\Temp
    - D:\Temp
    file_type: directory

- name: Find files and return SHA256 checksum of files found
  win_find:
    paths: C:\Temp
    get_checksum: yes
    checksum_algorithm: sha256

- name: Find files and do not return the checksum
  win_find:
    paths: C:\Temp
    get_checksum: no
'''

RETURN = r'''
examined:
    description: The number of files/folders that was checked.
    returned: always
    type: int
    sample: 10
matched:
    description: The number of files/folders that match the criteria.
    returned: always
    type: int
    sample: 2
files:
    description: Information on the files/folders that match the criteria returned as a list of dictionary elements
      for each file matched. The entries are sorted by the path value alphabetically.
    returned: success
    type: complex
    contains:
        attributes:
            description: attributes of the file at path in raw form.
            returned: success, path exists
            type: str
            sample: "Archive, Hidden"
        checksum:
            description: The checksum of a file based on checksum_algorithm specified.
            returned: success, path exists, path is a file, get_checksum == True
            type: str
            sample: 09cb79e8fc7453c84a07f644e441fd81623b7f98
        creationtime:
            description: The create time of the file represented in seconds since epoch.
            returned: success, path exists
            type: float
            sample: 1477984205.15
        extension:
            description: The extension of the file at path.
            returned: success, path exists, path is a file
            type: str
            sample: ".ps1"
        isarchive:
            description: If the path is ready for archiving or not.
            returned: success, path exists
            type: bool
            sample: true
        isdir:
            description: If the path is a directory or not.
            returned: success, path exists
            type: bool
            sample: true
        ishidden:
            description: If the path is hidden or not.
            returned: success, path exists
            type: bool
            sample: true
        islnk:
            description: If the path is a symbolic link or junction or not.
            returned: success, path exists
            type: bool
            sample: true
        isreadonly:
            description: If the path is read only or not.
            returned: success, path exists
            type: bool
            sample: true
        isshared:
            description: If the path is shared or not.
            returned: success, path exists
            type: bool
            sample: true
        lastaccesstime:
            description: The last access time of the file represented in seconds since epoch.
            returned: success, path exists
            type: float
            sample: 1477984205.15
        lastwritetime:
            description: The last modification time of the file represented in seconds since epoch.
            returned: success, path exists
            type: float
            sample: 1477984205.15
        lnk_source:
            description: The target of the symbolic link, will return null if not a link or the link is broken.
            returned: success, path exists, path is a symbolic link
            type: str
            sample: C:\temp
        owner:
            description: The owner of the file.
            returned: success, path exists
            type: str
            sample: BUILTIN\Administrators
        path:
            description: The full absolute path to the file.
            returned: success, path exists
            type: str
            sample: BUILTIN\Administrators
        sharename:
            description: The name of share if folder is shared.
            returned: success, path exists, path is a directory and isshared == True
            type: str
            sample: file-share
        size:
            description: The size in bytes of a file or folder.
            returned: success, path exists, path is not a link
            type: int
            sample: 1024
'''
