#!/usr/bin/python
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

# this is a windows documentation stub, actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = r'''
---
module: win_stat
version_added: "1.7"
short_description: returns information about a Windows file
description:
     - Returns information about a Windows file.
     - For non-Windows targets, use the M(stat) module instead.
options:
    path:
        description:
            - The full path of the file/object to get the facts of; both forward and
              back slashes are accepted.
        required: yes
    get_md5:
        description:
            - Whether to return the checksum sum of the file. Between Ansible 1.9
              and 2.2 this is no longer an MD5, but a SHA1 instead. As of Ansible
              2.3 this is back to an MD5. Will return None if host is unable to
              use specified algorithm.
            - This option is deprecated in Ansible 2.3 and is replaced with
              C(checksum_algorithm=md5).
        required: no
        default: True
    get_checksum:
        description:
            - Whether to return a checksum of the file (default sha1)
        required: no
        default: True
        version_added: "2.1"
    checksum_algorithm:
        description:
            - Algorithm to determine checksum of file. Will throw an error if
              the host is unable to use specified algorithm.
        required: no
        default: sha1
        choices: ['md5', 'sha1', 'sha256', 'sha384', 'sha512']
        version_added: "2.3"
notes:
     - For non-Windows targets, use the M(stat) module instead.
author: "Chris Church (@cchurch)"
'''

EXAMPLES = r'''
- name: Obtain information about a file
  win_stat:
    path: C:\foo.ini
  register: file_info

# Obtain information about a folder
- win_stat:
    path: C:\bar
  register: folder_info

# Get MD5 checksum of a file
- win_stat:
    path: C:\foo.ini
    get_checksum: yes
    checksum_algorithm: md5
  register: md5_checksum

- debug:
    var: md5_checksum.stat.checksum

# Get SHA1 checksum of file
- win_stat:
    path: C:\foo.ini
    get_checksum: yes
  register: sha1_checksum

- debug:
    var: sha1_checksum.stat.checksum

# Get SHA256 checksum of file
- win_stat:
    path: C:\foo.ini
    get_checksum: yes
    checksum_algorithm: sha256
  register: sha256_checksum

- debug:
    var: sha256_checksum.stat.checksum
'''

RETURN = r'''
changed:
    description: Whether anything was changed
    returned: always
    type: boolean
    sample: True
stat:
    description: dictionary containing all the stat data
    returned: success
    type: complex
    contains:
        attributes:
            description: attributes of the file at path in raw form
            returned: success, path exists
            type: string
            sample: "Archive, Hidden"
        checksum:
            description: The checksum of a file based on checksum_algorithm specified
            returned: success, path exist, path is a file, get_checksum == True
              checksum_algorithm specified is supported
            type: string
            sample: 09cb79e8fc7453c84a07f644e441fd81623b7f98
        creationtime:
            description: the create time of the file represented in seconds since epoch
            returned: success, path exists
            type: float
            sample: 1477984205.15
        exists:
            description: if the path exists or not
            returned: success
            type: boolean
            sample: True
        extension:
            description: the extension of the file at path
            returned: success, path exists, path is a file
            type: string
            sample: ".ps1"
        filename:
            description: the name of the file (without path)
            returned: success, path exists, path is a file
            type: string
            sammple: foo.ini
        isarchive:
            description: if the path is ready for archiving or not
            returned: success, path exists
            type: boolean
            sample: True
        isdir:
            description: if the path is a directory or not
            returned: success, path exists
            type: boolean
            sample: True
        ishidden:
            description: if the path is hidden or not
            returned: success, path exists
            type: boolean
            sample: True
        islnk:
            description: if the path is a symbolic link or junction or not
            returned: success, path exists
            type: boolean
            sample: True
        isreadonly:
            description: if the path is read only or not
            returned: success, path exists
            type: boolean
            sample: True
        isreg:
            description: if the path is a regular file
            returned: success, path exists
            type: boolean
            sample: True
        isshared:
            description: if the path is shared or not
            returned: success, path exists
            type: boolean
            sample: True
        lastaccesstime:
            description: the last access time of the file represented in seconds since epoch
            returned: success, path exists
            type: float
            sample: 1477984205.15
        lastwritetime:
            description: the last modification time of the file represented in seconds since epoch
            returned: success, path exists
            type: float
            sample: 1477984205.15
        lnk_source:
            description: the target of the symbolic link, will return null if not a link or the link is broken
            return: success, path exists, file is a symbolic link
            type: string
            sample: C:\temp
        md5:
            description: The MD5 checksum of a file (Between Ansible 1.9 and 2.2 this was returned as a SHA1 hash)
            returned: success, path exist, path is a file, get_md5 == True, md5 is supported
            type: string
            sample: 09cb79e8fc7453c84a07f644e441fd81623b7f98
        owner:
            description: the owner of the file
            returned: success, path exists
            type: string
            sample: BUILTIN\Administrators
        path:
            description: the full absolute path to the file
            returned: success, path exists, file exists
            type: string
            sample: C:\foo.ini
        sharename:
            description: the name of share if folder is shared
            returned: success, path exists, file is a directory and isshared == True
            type: string
            sample: file-share
        size:
            description: the size in bytes of a file or folder
            returned: success, path exists, file is not a link
            type: int
            sample: 1024
'''
