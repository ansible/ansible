#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: atomic_host
short_description: Manage the atomic host platform
description:
    - Manage the atomic host platform
    - Rebooting of Atomic host platform should be done outside this module
version_added: "2.2"
author: "Saravanan KR @krsacme"
notes:
    - Host should be an atomic platform (verified by existence of '/run/ostree-booted' file)
requirements:
  - atomic
  - "python >= 2.6"
options:
    revision:
        description:
          - The version number of the atomic host to be deployed. Providing C(latest) will upgrade to the latest available version.
        required: false
        default: latest
        aliases: ["version"]
'''

EXAMPLES = '''

# Upgrade the atomic host platform to the latest version (atomic host upgrade)
- atomic_host:
    revision: latest

# Deploy a specific revision as the atomic host (atomic host deploy 23.130)
- atomic_host:
    revision: 23.130
'''

RETURN = '''
msg:
    description: The command standard output
    returned: always
    type: string
    sample: 'Already on latest'
'''
import os
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def core(module):
    revision = module.params['revision']
    args = []

    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C')

    if revision == 'latest':
        args = ['atomic', 'host', 'upgrade']
    else:
        args = ['atomic', 'host', 'deploy', revision]

    out = {}
    err = {}
    rc = 0

    rc, out, err = module.run_command(args, check_rc=False)

    if rc == 77 and revision == 'latest':
        module.exit_json(msg="Already on latest", changed=False)
    elif rc != 0:
        module.fail_json(rc=rc, msg=err)
    else:
        module.exit_json(msg=out, changed=True)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            revision=dict(default='latest', required=False, aliases=["version"]),
            ),
        )

    # Verify that the platform is atomic host
    if not os.path.exists("/run/ostree-booted"):
        module.fail_json(msg="Module atomic_host is applicable for Atomic Host Platforms only")

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
