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


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = r'''
---
module: win_copy
version_added: "1.9.2"
short_description: Copies files to remote locations on windows hosts.
description:
- The C(win_copy) module copies a file on the local box to remote windows locations.
- For non-Windows targets, use the M(copy) module instead.
options:
  content:
    description:
    - When used instead of C(src), sets the contents of a file directly to the
      specified value. This is for simple values, for anything complex or with
      formatting please switch to the template module.
    version_added: "2.3"
  dest:
    description:
    - Remote absolute path where the file should be copied to. If src is a
      directory, this must be a directory too.
    - Use \ for path separators or \\ when in "double quotes".
    required: true
  force:
    version_added: "2.3"
    description:
    - If set to C(yes), the remote file will be replaced when content is
      different than the source.
    - If set to C(no), the remote file will only be transferred if the
      destination does not exist.
    default: True
    choices:
    - yes
    - no
  remote_src:
    description:
    - If False, it will search for src at originating/master machine, if True
      it will go to the remote/target machine for the src.
    default: False
    choices:
    - True
    - False
    version_added: "2.3"
  src:
    description:
    - Local path to a file to copy to the remote server; can be absolute or
      relative. If path is a directory, it is copied recursively. In this case,
      if path ends with "/", only inside contents of that directory are copied
      to destination. Otherwise, if it does not end with "/", the directory
      itself with all contents is copied. This behavior is similar to Rsync.
    required: true
notes:
- For non-Windows targets, use the M(copy) module instead.
author: "Jon Hawkesworth (@jhawkesworth)"
'''

EXAMPLES = r'''
- name: Copy a single file
  win_copy:
    src: /srv/myfiles/foo.conf
    dest: c:\Temp\foo.conf
- name: Copy files/temp_files to c:\temp
  win_copy:
    src: files/temp_files/
    dest: c:\Temp
- name: Copy a single file where the source is on the remote host
  win_copy:
    src: C:\temp\foo.txt
    dest: C:\ansible\foo.txt
    remote_src: True
- name: Copy a folder recursively where the source is on the remote host
  win_copy:
    src: C:\temp
    dest: C:\ansible
    remote_src: True
- name: Set the contents of a file
  win_copy:
    dest: C:\temp\foo.txt
    content: abc123
'''

RETURN = r'''
dest:
    description: destination file/path
    returned: changed
    type: string
    sample: C:\Temp\
src:
    description: source file used for the copy on the target machine
    returned: changed
    type: string
    sample: /home/httpd/.ansible/tmp/ansible-tmp-1423796390.97-147729857856000/source
checksum:
    description: sha1 checksum of the file after running copy
    returned: success, src is a file
    type: string
    sample: 6e642bb8dd5c2e027bf21dd923337cbb4214f827
size:
    description: size of the target, after execution
    returned: changed (src is a file or remote_src == True)
    type: int
    sample: 1220
operation:
    description: whether a single file copy took place or a folder copy
    returned: changed
    type: string
    sample: file_copy
original_basename:
    description: basename of the copied file
    returned: changed, src is a file
    type: string
    sample: foo.txt
'''
