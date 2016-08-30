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
module: ipadm_if
short_description: Manage IP interfaces  on Solaris/illumos systems.
description:
    - Create, delete, enable or disable IP interfaces on Solaris/illumos
      systems.
version_added: "2.2"
author: Adam Števko (@xen0l)
options:
    name:
        description:
            - IP interface name.
        required: true
    temporary:
        description:
            - Specifies that the IP interface is temporary. Temporary IP
              interfaces do not persist across reboots.
        required: false
        default: false
        choices: [ "true", "false" ]
    state:
        description:
            - Create or delete Solaris/illumos IP interfaces.
        required: false
        default: "present"
        choices: [ "present", "absent", "enabled", "disabled" ]
'''

EXAMPLES = '''
# Create vnic0 interface
ipadm_if: name=vnic0 state=enabled

# Disable vnic0 interface
ipadm_if: name=vnic0 state=disabled
'''

RETURN = '''
name:
    description: IP interface name
    returned: always
    type: string
    sample: "vnic0"
state:
    description: state of the target
    returned: always
    type: string
    sample: "present"
temporary:
    description: persistence of a IP interface
    returned: always
    type: boolean
    sample: "True"
'''


class IPInterface(object):

    def __init__(self, module):
        self.module = module

        self.name = module.params['name']
        self.temporary = module.params['temporary']
        self.state = module.params['state']

    def interface_exists(self):
        cmd = [self.module.get_bin_path('ipadm', True)]

        cmd.append('show-if')
        cmd.append(self.name)

        (rc, _, _) = self.module.run_command(cmd)
        if rc == 0:
            return True
        else:
            return False

    def interface_is_disabled(self):
        cmd = [self.module.get_bin_path('ipadm', True)]

        cmd.append('show-if')
        cmd.append('-o')
        cmd.append('state')
        cmd.append(self.name)

        (rc, out, err) = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(name=self.name, rc=rc, msg=err)

        return 'disabled' in out

    def create_interface(self):
        cmd = [self.module.get_bin_path('ipadm', True)]

        cmd.append('create-if')

        if self.temporary:
            cmd.append('-t')

        cmd.append(self.name)

        return self.module.run_command(cmd)

    def delete_interface(self):
        cmd = [self.module.get_bin_path('ipadm', True)]

        cmd.append('delete-if')

        if self.temporary:
            cmd.append('-t')

        cmd.append(self.name)

        return self.module.run_command(cmd)

    def enable_interface(self):
        cmd = [self.module.get_bin_path('ipadm', True)]

        cmd.append('enable-if')
        cmd.append('-t')
        cmd.append(self.name)

        return self.module.run_command(cmd)

    def disable_interface(self):
        cmd = [self.module.get_bin_path('ipadm', True)]

        cmd.append('disable-if')
        cmd.append('-t')
        cmd.append(self.name)

        return self.module.run_command(cmd)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            temporary=dict(default=False, type='bool'),
            state=dict(default='present', choices=['absent',
                                                   'present',
                                                   'enabled',
                                                   'disabled']),
        ),
        supports_check_mode=True
    )

    interface = IPInterface(module)

    rc = None
    out = ''
    err = ''
    result = {}
    result['name'] = interface.name
    result['state'] = interface.state
    result['temporary'] = interface.temporary

    if interface.state == 'absent':
        if interface.interface_exists():
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err) = interface.delete_interface()
            if rc != 0:
                module.fail_json(name=interface.name, msg=err, rc=rc)
    elif interface.state == 'present':
        if not interface.interface_exists():
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err) = interface.create_interface()

            if rc is not None and rc != 0:
                module.fail_json(name=interface.name, msg=err, rc=rc)

    elif interface.state == 'enabled':
        if interface.interface_is_disabled():
            (rc, out, err) = interface.enable_interface()

            if rc is not None and rc != 0:
                module.fail_json(name=interface.name, msg=err, rc=rc)

    elif interface.state == 'disabled':
        if not interface.interface_is_disabled():
            (rc, out, err) = interface.disable_interface()

            if rc is not None and rc != 0:
                module.fail_json(name=interface.name, msg=err, rc=rc)

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
