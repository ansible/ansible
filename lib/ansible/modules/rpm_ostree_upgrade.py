#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: rpm_ostree_upgrade
short_description: Manage rpm-ostree upgrade transactions
description:
    - Manage an rpm-ostree upgrade transactions
version_added: "2.14"
author:
- Adam Miller (@maxamillion)
requirements:
  - rpm-ostree
options:
    os:
        description:
            - The OSNAME upon which to operate
        type: str
        default: ""
        required: false
    cache_only:
        description:
          - Perform the transaction using only pre-cached data, don't download
        type: bool
        default: false
        required: false
    allow_downgrade:
        description:
            - Allow for the upgrade to be a chronologically older tree
        type: bool
        default: false
        required: false
    peer:
        description:
            - Force peer-to-peer connection instead of using system message bus
        type: bool
        default: false
        required: false

'''

EXAMPLES = '''
- name: Upgrade the rpm-ostree image without options, accept all defaults
  ansible.builtin.rpm_ostree_upgrade:

- name: Upgrade the rpm-ostree image allowing downgrades
  ansible.builtin.rpm_ostree_upgrade:
    allow_downgrade: true
'''

RETURN = '''
msg:
    description: The command standard output
    returned: always
    type: str
    sample: 'No upgrade available.'
'''

import os
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native, to_text


def rpm_ostree_transaction(module):
    cmd = []
    cmd.append(module.get_bin_path("rpm-ostree"))
    cmd.append('upgrade')

    if module.params['os']:
        cmd += ['--os', module.params['os']]
    if module.params['cache_only']:
        cmd += ['--cache-only']
    if module.params['allow_downgrade']:
        cmd += ['--allow-downgrade']
    if module.params['peer']:
        cmd += ['--peer']

    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C')

    rc, out, err = module.run_command(cmd)

    if rc != 0:
        module.fail_json(rc=rc, msg=err)
    else:
        if to_text("No upgrade available.") in to_text(out):
            module.exit_json(msg=out, changed=False)
        else:
            module.exit_json(msg=out, changed=True)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            os=dict(type='str', default=''),
            cache_only=dict(type='bool', default=False),
            allow_downgrade=dict(type='bool', default=False),
            peer=dict(type='bool', default=False),
        ),
    )

    # Verify that the platform is an rpm-ostree based system
    if not os.path.exists("/run/ostree-booted"):
        module.fail_json(msg="Module rpm_ostree_upgrade is only applicable for rpm-ostree based systems.")

    try:
        rpm_ostree_transaction(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
