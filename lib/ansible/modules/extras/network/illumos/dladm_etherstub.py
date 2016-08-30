#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Adam Števko <adam.stevko@gmail.com>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.
#

DOCUMENTATION = '''
---
module: dladm_etherstub
short_description: Manage etherstubs on Solaris/illumos systems.
description:
    - Create or delete etherstubs on Solaris/illumos systems.
version_added: "2.2"
author: Adam Števko (@xen0l)
options:
    name:
        description:
            - Etherstub name.
        required: true
    temporary:
        description:
            - Specifies that the etherstub is temporary. Temporary etherstubs
              do not persist across reboots.
        required: false
        default: false
        choices: [ "true", "false" ]
    state:
        description:
            - Create or delete Solaris/illumos etherstub.
        required: false
        default: "present"
        choices: [ "present", "absent" ]
'''

EXAMPLES = '''
# Create 'stub0' etherstub
dladm_etherstub: name=stub0 state=present

# Remove 'stub0 etherstub
dladm_etherstub: name=stub0 state=absent
'''

RETURN = '''
name:
    description: etherstub name
    returned: always
    type: string
    sample: "switch0"
state:
    description: state of the target
    returned: always
    type: string
    sample: "present"
temporary:
    description: etherstub's persistence
    returned: always
    type: boolean
    sample: "True"
'''


class Etherstub(object):

    def __init__(self, module):
        self.module = module

        self.name = module.params['name']
        self.temporary = module.params['temporary']
        self.state = module.params['state']

    def etherstub_exists(self):
        cmd = [self.module.get_bin_path('dladm', True)]

        cmd.append('show-etherstub')
        cmd.append(self.name)

        (rc, _, _) = self.module.run_command(cmd)

        if rc == 0:
            return True
        else:
            return False

    def create_etherstub(self):
        cmd = [self.module.get_bin_path('dladm', True)]

        cmd.append('create-etherstub')

        if self.temporary:
            cmd.append('-t')
        cmd.append(self.name)

        return self.module.run_command(cmd)

    def delete_etherstub(self):
        cmd = [self.module.get_bin_path('dladm', True)]

        cmd.append('delete-etherstub')

        if self.temporary:
            cmd.append('-t')
        cmd.append(self.name)

        return self.module.run_command(cmd)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            temporary=dict(default=False, type='bool'),
            state=dict(default='present', choices=['absent', 'present']),
        ),
        supports_check_mode=True
    )

    etherstub = Etherstub(module)

    rc = None
    out = ''
    err = ''
    result = {}
    result['name'] = etherstub.name
    result['state'] = etherstub.state
    result['temporary'] = etherstub.temporary

    if etherstub.state == 'absent':
        if etherstub.etherstub_exists():
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err) = etherstub.delete_etherstub()
            if rc != 0:
                module.fail_json(name=etherstub.name, msg=err, rc=rc)
    elif etherstub.state == 'present':
        if not etherstub.etherstub_exists():
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err) = etherstub.create_etherstub()

        if rc is not None and rc != 0:
            module.fail_json(name=etherstub.name, msg=err, rc=rc)

    if rc is None:
        result['changed'] = False
    else:
        result['changed'] = True

    if out:
        result['stdout'] = out
    if err:
        result['stderr'] = err

    module.exit_json(**result)

from ansible.module_utils.basic import *
main()
