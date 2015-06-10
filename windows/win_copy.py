#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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
version_added: "2.0"
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
author: Michael DeHaan
notes:
   - The "win_copy" module recursively copy facility does not scale to lots (>hundreds) of files.
     Instead, you may find it better to create files locally, perhaps using win_template, and 
     then use win_get_url to put them in the correct location.
'''

EXAMPLES = '''
# Example from Ansible Playbooks
- win_copy: src=/srv/myfiles/foo.conf dest=c:\\TEMP\\foo.conf

'''

