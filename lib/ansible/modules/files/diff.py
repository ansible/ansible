#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Dag Wieers <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
---
module: diff
version_added: '2.4'
short_description: Compare files
description:
- The C(diff) module compares 2 files, either a local or remote file with another
  file on the remote system.
requires:
- Python 2.7+
options:
  src:
    description:
      - Local path to a file to copy to the remote server; can be absolute or relative.
  content:
    description:
      - When used instead of I(src), sets the contents of a file directly to the specified value.
  dest:
    description:
      - Remote absolute path where the file should be copied to.
    required: yes
  remote_src:
    description:
      - If C(no), it will search for I(src) at originating/master machine.
      - If C(yes) it will go to the remote/target machine for the I(src). Default is C(no).
      - Currently I(remote_src) does not support recursive copying.
    type: bool
    default: 'no'
author:
- Dag Wieers (@dagwieers)
notes:
- For Windows targets, use the M(win_diff) module instead.
'''

EXAMPLES = r'''
- name: Compare 2 remote files
  diff:
    src: /tmp/foo.conf
    dest: /etc/foo.conf
    remote_src: yes
'''

RETURN = r'''
dest:
    description: destination file/path
    returned: success
    type: string
    sample: /path/to/file.txt
src:
    description: source file used for the copy on the target machine
    returned: changed
    type: string
    sample: /home/httpd/.ansible/tmp/ansible-tmp-1423796390.97-147729857856000/source
stdout:
    description: unified diff output
    returned: always
    type: string
identical
    description: whether source and destination are identical
    returned: always
    type: boolean
    sample: true
'''

import os
from difflib import unified_diff

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes, to_native


def main():

    module = AnsibleModule(
        argument_spec=dict(
            src=dict(type='path'),
            content=dict(type='str', no_log=True),
            dest=dict(type='path', required=True),
            remote_src=dict(type='bool'),
        ),
        supports_check_mode=True,
    )

    src = module.params['src']
    b_src = to_bytes(src, errors='surrogate_or_strict')
    dest = module.params['dest']
    b_dest = to_bytes(dest, errors='surrogate_or_strict')
    remote_src = module.params['remote_src']

    result = dict(
        changed=False,
        identical=False,
        stdout='',
    )

    if module._diff:
        result['diff'] = dict(prepared=''),

    if not os.path.exists(b_src):
        module.fail_json(msg="Source '%s' not found" % src, **result)
    if not os.access(b_src, os.R_OK):
        module.fail_json(msg="Source '%s' not readable" % src, **result)
    if os.path.isdir(b_src):
        module.fail_json(msg="Remote copy does not support recursive copy of directory: '%s'" % src, **result)

    if not os.path.exists(b_dest):
        module.fail_json(msg="Destination '%s' not found" % dest, **result)

    try:
        checksum_src = module.sha1(src)
    except IOError as e:
        module.fail_json(msg="Source '%s' cannot be read: %s" % (src, e), **result)
    result['checksum_src'] = checksum_src
    try:
        checksum_dest = module.sha1(dest)
    except IOError as e:
        module.fail_json(msg="Destination '%s' cannot be read: %s" % (dest, e), **result)
    result['checksum_dest'] = checksum_dest

    if checksum_src == checksum_dest:
        result['identical'] = True
    else:
        with open(src, 'rb') as s, open(dest, 'rb') as d:
            result['stdout'] = ''.join(unified_diff(s.readlines(), d.readlines(), fromfile=remote_src, tofile=dest))

            if module._diff:
                result['diff'] = dict(prepared=result['stdout'])

    module.exit_json(**result)

if __name__ == '__main__':
    main()
