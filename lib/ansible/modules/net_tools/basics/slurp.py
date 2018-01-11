#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
---
module: slurp
version_added: historical
short_description: Slurps a file from remote nodes
description:
     - This module works like M(fetch). It is used for fetching a base64-
       encoded blob containing the data in a remote file.
     - This module is also supported for Windows targets.
options:
  src:
    description:
      - The file on the remote system to fetch. This I(must) be a file, not a
        directory.
    required: true
notes:
   - This module returns an 'in memory' base64 encoded version of the file, take into account that this will require at least twice the RAM as the
     original file size.
   - This module is also supported for Windows targets.
   - "See also: M(fetch)"
author:
    - Ansible Core Team
    - Michael DeHaan (@mpdehaan)
'''

EXAMPLES = r'''
- name: Find out what the remote machine's mounts are
  slurp:
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
import os

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            src=dict(type='path', required=True, aliases=['path']),
        ),
        supports_check_mode=True,
    )
    source = module.params['src']

    if not os.path.exists(source):
        module.fail_json(msg="file not found: %s" % source)
    if not os.access(source, os.R_OK):
        module.fail_json(msg="file is not readable: %s" % source)

    data = base64.b64encode(open(source, 'rb').read())

    module.exit_json(content=data, source=source, encoding='base64')


if __name__ == '__main__':
    main()
