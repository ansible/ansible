# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = r"""
---
module: slurp
version_added: historical
short_description: Slurps a file from remote nodes
description:
     - This module works like M(ansible.builtin.fetch). It is used for fetching a base64-
       encoded blob containing the data in a remote file.
     - This module is also supported for Windows targets.
options:
  src:
    description:
      - The file on the remote system to fetch. This I(must) be a file, not a directory.
    type: path
    required: true
    aliases: [ path ]
extends_documentation_fragment:
    - action_common_attributes
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none
  platform:
    platforms: posix, windows
notes:
   - This module returns an 'in memory' base64 encoded version of the file, take
     into account that this will require at least twice the RAM as the original file size.
seealso:
- module: ansible.builtin.fetch
author:
    - Ansible Core Team
    - Michael DeHaan (@mpdehaan)
"""

EXAMPLES = r"""
- name: Find out what the remote machine's mounts are
  ansible.builtin.slurp:
    src: /proc/mounts
  register: mounts

- name: Print returned information
  ansible.builtin.debug:
    msg: "{{ mounts['content'] | b64decode }}"

# From the commandline, find the pid of the remote machine's sshd
# $ ansible host -m ansible.builtin.slurp -a 'src=/var/run/sshd.pid'
# host | SUCCESS => {
#     "changed": false,
#     "content": "MjE3OQo=",
#     "encoding": "base64",
#     "source": "/var/run/sshd.pid"
# }
# $ echo MjE3OQo= | base64 -d
# 2179
"""

RETURN = r"""
content:
    description: Encoded file content
    returned: success
    type: str
    sample: "MjE3OQo="
encoding:
    description: Type of encoding used for file
    returned: success
    type: str
    sample: "base64"
source:
    description: Actual path of file slurped
    returned: success
    type: str
    sample: "/var/run/sshd.pid"
"""

import base64
import errno

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            src=dict(type='path', required=True, aliases=['path']),
        ),
        supports_check_mode=True,
    )
    source = module.params['src']

    try:
        with open(source, 'rb') as source_fh:
            data = base64.b64encode(source_fh.read())
    except OSError as ex:
        if ex.errno == errno.ENOENT:
            msg = f"File not found: {source}"
        elif ex.errno == errno.EACCES:
            msg = f"File is not readable: {source}"
        elif ex.errno == errno.EISDIR:
            msg = f"Source is a directory and must be a file: {source}"
        else:
            msg = "Unable to slurp file: {source}"

        module.fail_json(msg, exception=ex)

    module.exit_json(content=data, source=source, encoding='base64')


if __name__ == '__main__':
    main()
