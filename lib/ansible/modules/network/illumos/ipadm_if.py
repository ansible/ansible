#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Adam Števko <adam.stevko@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


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
        type: bool
    state:
        description:
            - Create or delete Solaris/illumos IP interfaces.
        required: false
        default: "present"
        choices: [ "present", "absent", "enabled", "disabled" ]
'''

EXAMPLES = '''
# Create vnic0 interface
- ipadm_if:
    name: vnic0
    state: enabled

# Disable vnic0 interface
- ipadm_if:
    name: vnic0
    state: disabled
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
from ansible.module_utils.basic import AnsibleModule


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


if __name__ == '__main__':
    main()
