#!/usr/bin/python
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
---
module: exists
version_added: "2.5"
short_description: Check to see if a file or directory exists
description:
  - Checks to see if a file exists, and if so if it is a directory or a link
   similar to stat, but without calculating extra checksums.
options:
  path:
    description:
      - The full path of the file to check.
    required: true
  follow:
    description:
      - Whether to follow symlinks.
    type: bool
    default: 'no'
notes:
     - For Windows targets, use the M(win_stat) module instead.
author: Monty Taylor (@e_monty)
'''

EXAMPLES = '''
# Check if /etc/foo.conf exists.
- exists:
    path: /etc/foo.conf
  register: foo_exists
- fail:
    msg: "Whoops! /etc/foo.conf does not exist"
  when: not foo_exists.exists

# Determine if a path exists and is a directory.
- exists:
    path: /path/to/something
  register: p
- debug:
    msg: "Path exists and is a directory"
  when: p.isdir
'''

RETURN = r'''
exists:
    description: If the destination path exists and can be read
    returned: success
    type: boolean
    sample: True
is_dir:
    description: Tells you if the path is a directory
    returned: success
    type: boolean
    sample: False
is_link:
    description: Tells you if the path is a symbolic link
    returned: success
    type: boolean
    sample: False
path:
    description: The path to the file, or link target if follow is True
    returned: success
    type: string
    sample: '/etc/foo'
'''

import errno
import os
import stat

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(required=True, type='path'),
            follow=dict(type='bool', default='no'),
        ),
        supports_check_mode=True,
    )

    path = module.params.get('path')
    follow = module.params.get('follow')

    results = dict(
        changed=False, path=path,
        exists=False, is_dir=False, is_link=False)

    try:
        if follow:
            st = os.stat(b_path)
        else:
            st = os.lstat(b_path)
    except OSError as e:
        if e.errno == errno.ENOENT:
            module.exit_json(**results)

        module.fail_json(msg=e.strerror, **results)

    results['exists'] = True
    results['is_dir'] = stat.S_ISDIR(st.st_mode)
    results['is_link'] = stat.S_ISLINK(st.st_mode)
    if results['is_link'] and follow:
        results['path'] = os.readlink(path)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
