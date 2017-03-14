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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: slurp
version_added: historical
short_description: Slurps a file from remote nodes
description:
     - This module works like M(fetch). It is used for fetching a base64-
       encoded blob containing the data in a remote file.
options:
  src:
    description:
      - The file on the remote system to fetch. This I(must) be a file, not a
        directory.
    required: true
    default: null
    aliases: []
notes:
   -  This module returns an 'in memory' base64 encoded version of the file, take into account that this will require at least twice the RAM as the original file size.
   - "See also: M(fetch)"
requirements: []
author:
    - "Ansible Core Team"
    - "Michael DeHaan"
'''

EXAMPLES = '''
# Find out what the remote machine's mounts are:
- slurp:
    src: /proc/mounts
  register: mounts

- debug:
    msg: "{{ mounts['content'] | b64decode }}"

# From the commandline, find the pid of the remote machine's sshd
# $ ansible host -m slurp -a 'src=/var/run/sshd.pid'
# host | SUCCESS => {
#     "changed": false,
#     "content": "MjE3OQo=",
#     "encoding": "base64",
#     "source": "/var/run/sshd.pid"
# }
# $ echo MjE3OQo= | base64 -d
# 2179
'''

import base64

def main():
    module = AnsibleModule(
        argument_spec = dict(
            src = dict(required=True, aliases=['path'], type='path'),
        ),
        supports_check_mode=True
    )
    source = module.params['src']

    if not os.path.exists(source):
        module.fail_json(msg="file not found: %s" % source)
    if not os.access(source, os.R_OK):
        module.fail_json(msg="file is not readable: %s" % source)

    data = base64.b64encode(open(source, 'rb').read())

    module.exit_json(content=data, source=source, encoding='base64')

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()

