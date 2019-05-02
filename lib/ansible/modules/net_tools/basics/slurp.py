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
      - The file on the remote system to fetch. This I(must) be a file, not a directory.
    type: path
    required: true
    aliases: [ path ]
  chunk:
    description:
      - Sets the size of how much of the file should be read/encoded at a time, if not set or ``<= 0``, it will read the full file.
    type: int
    version_added: "2.9"
notes:
   - This module returns an 'in memory' base64 encoded version of the file, take into account that this will, by default,
     require at least twice the RAM as the original file size on the target, use the C(chunk) option to minimize this.
     It will also require x2 the RAM on the controller if you 'decode in memory', save to a base64 encoded file and decode the file to avoid this.
seealso:
- module: fetch
author:
    - Ansible Core Team
    - Michael DeHaan (@mpdehaan)
'''

EXAMPLES = r'''
- name: Find out what the remote machine's mounts are
  block:
   - name: slurp contents and register
     slurp:
        src: /proc/mounts
     register: mounts

    - name: display contents (needs to decode)
      debug:
        msg: "{{ mounts['content'] | b64decode }}"

- name: Display large file but read in 64k chunks
  block:
    - name: actually read file
      slurp:
        src: /home/user/bigfile
        chunk: 65535
      register: bigfile

    - debug:
      name: show contents of bigfile
        msg: "{{ bigfile['content'] | b64decode }}"

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
            chunk=dict(type='int'),
        ),
        supports_check_mode=True,
    )
    source = module.params['src']
    chunk = module.params['chunk']

    if not os.path.exists(source):
        module.fail_json(msg="file not found: %s" % source)
    if not os.access(source, os.R_OK):
        module.fail_json(msg="file is not readable: %s" % source)

    with open(source, 'rb') as source_fh:
        if chunk is None or chunk <= 0:
            data = base64.b64encode(source_fh.read())
        else:
            encoded = []
            while True:
                e_chunk = source_fh.read(chunk)
                if not e_chunk:
                    break
                encoded.append(base64.b64encode(e_chunk))

            data = ''.join(encoded)

    module.exit_json(content=data, source=source, path=source, encoding='base64')


if __name__ == '__main__':
    main()
