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

import os
import time

DOCUMENTATION = '''
---
module: win_copy
version_added: "1.9.2"
short_description: Copies files to remote locations on windows hosts.
description:
     - The M(win_copy) module copies a file on the local box to remote windows locations.
options:
  src:
    description:
      - Local path to a file to copy to the remote server; can be absolute or relative.
        If path is a directory, it is copied recursively. In this case, if path ends
        with "/", only inside contents of that directory are copied to destination.
        Otherwise, if it does not end with "/", the directory itself with all contents
        is copied. This behavior is similar to Rsync.
    required: false
    default: null
    aliases: []
  dest:
    description:
      - Remote absolute path where the file should be copied to. If src is a directory,
        this must be a directory too. Use \\ for path separators.
    required: true
    default: null
author: "Jon Hawkesworth (@jhawkesworth)"
notes:
   - The "win_copy" module is best used for small files only.
     This module should **not** be used for files bigger than 3Mb as
     this will result in a 500 response from the winrm host
     and it will not be possible to connect via winrm again until the
     windows remote management service has been restarted on the 
     windows host.
     Files larger than 1Mb will take minutes to transfer.
     The recommended way to transfer large files is using win_get_url 
     or collecting from a windows file share folder.  
'''

EXAMPLES = '''
# Copy a single file
- win_copy: src=/srv/myfiles/foo.conf dest=c:\\TEMP\\foo.conf

# Copy the contents of files/temp_files dir into c:\temp\.  Includes any sub dirs under files/temp_files
# Note the use of unix style path in the dest.  
# This is necessary because \ is yaml escape sequence
- win_copy: src=files/temp_files/ dest=c:/temp/

# Copy the files/temp_files dir and any files or sub dirs into c:\temp
# Copies the folder because there is no trailing / on 'files/temp_files'
- win_copy: src=files/temp_files dest=c:/temp/

'''
RETURN = '''
dest:
    description: destination file/path
    returned: changed
    type: string
    sample: "c:/temp/"
src:
    description: source file used for the copy on the target machine
    returned: changed
    type: string
    sample: "/home/httpd/.ansible/tmp/ansible-tmp-1423796390.97-147729857856000/source"
checksum:
    description: checksum of the file after running copy
    returned: success
    type: string
    sample: "6e642bb8dd5c2e027bf21dd923337cbb4214f827"
size:
    description: size of the target, after execution
    returned: changed (single files only)
    type: int
    sample: 1220
operation:
    description: whether a single file copy took place or a folder copy
    returned: changed (single files only)
    type: string
    sample: "file_copy"
original_basename:
    description: basename of the copied file
    returned: changed (single files only)
    type: string
    sample: "foo.txt"
'''

