#!/usr/bin/python
# -*- coding: utf-8 -*-

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
# You should have received a copy of the GNU General Public licenses
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION='''
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
                argument_spec = dict(
                    revision = dict(default='latest', required=False, aliases=["version"]),
                ),
            )

    # Verify that the platform is atomic host
    if not os.path.exists("/run/ostree-booted"):
        module.fail_json(msg="Module atomic_host is applicable for Atomic Host Platforms only")

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=str(e))


# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
