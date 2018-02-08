#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Bruce Smith <Bruce.Smith.IT@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: nictagadm
short_description: Manage NIC tags on SmartOS systems.
description:
  - Create of delete NIC tags on SmartOS systems.
version_added: "2.5"
author: Bruce Smith (@SmithX10)
options:
    name:
        description:
            - NIC tag name.
        required: true
    mac:
        description:
            - MAC Address to attach the NIC tag to when not using an etherstub. mac and etherstub are mutually exclusive.
        required: false
        default: None
    etherstub:
        description:
            - Specifies that the NIC tag will be attached to a created etherstub. etherstub is mutually exclusive with both mtu, and mac.
        required: false
        default: false
    mtu:
        description:
            - MTU size of the NIC tag. mtu and etherstub are mutually exclusive.
        required: false
        default: None
    force:
        description:
            - When State.Absent is set this switch will use the -f parameter and delete the NIC tag regardless of existing VMs
        default: false
    state:
        description:
            - Create or delete a SmartOS NIC tag.
        required: false
        default: "present"
        choices: [ "present", "absent" ]
'''

EXAMPLES = '''
- name: Create 'strage0' on '00:1b:21:a3:f5:4d'
  nictagadm: name=storage0 mac=00:1b:21:a3:f5:4d mtu=9000 state=present

- name: Remove 'storage0' NIC tag
  nictagadm: name=storage0 state=absent force=false
'''

RETURN = '''
name:
    description: NIC tag name
    returned: always
    type: string
    sample: storage0
mac:
    description: MAC Address that the nic tag was attached to.
    returned: always
    type: string
    sample: 00:1b:21:a3:f5:4d
etherstub:
    description: specifies if the NIC tag will create and attach to an etherstub.
    returned: always
    type: boolean
    sample: False
mtu:
    description: specifies which MTU size was passed during the nictagadm add command. mtu and etherstub are mutually exclusive.
    returned: always
    type: int
    sample: 1500
force:
    description: Shows if -f was used during the deletion of a NIC tag
    returned: always
    type: boolean
    sample: False
state:
    description: state of the target
    returned: always
    type: string
    sample: present
'''

import re

from ansible.module_utils.basic import AnsibleModule


class NICTAG(object):

    def __init__(self, module):
        self.module = module

        self.name = module.params['name']
        self.mac = module.params['mac']
        self.etherstub = module.params['etherstub']
        self.mtu = module.params['mtu']
        self.force = module.params['force']
        self.state = module.params['state']

    def is_valid_mac(self):
        if re.match("[0-9a-f]{2}([:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", self.mac.lower()):
            return True
        else:
            return False

    def nictag_exists(self):
        cmd = [self.module.get_bin_path('nictagadm', True)]

        cmd.append('exists')
        cmd.append(self.name)

        (rc, _, _) = self.module.run_command(cmd)

        if rc == 0:
            return True
        else:
            return False

    def add_nictag(self):
        cmd = [self.module.get_bin_path('nictagadm', True)]

        cmd.append('-v')
        cmd.append('add')

        if self.etherstub:
            cmd.append('-l')

        if self.mtu:
            cmd.append('-p')
            cmd.append('mtu=' + str(self.mtu))

        if self.mac:
            cmd.append('-p')
            cmd.append('mac=' + str(self.mac))

        cmd.append(self.name)

        return self.module.run_command(cmd)

    def delete_nictag(self):
        cmd = [self.module.get_bin_path('nictagadm', True)]

        cmd.append('-v')
        cmd.append('delete')

        if self.force:
            cmd.append('-f')

        cmd.append(self.name)

        return self.module.run_command(cmd)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, type='str'),
            mac=dict(default=None, type='str'),
            etherstub=dict(default=False, type='bool'),
            mtu=dict(default=None, type='int'),
            force=dict(default=False, type='bool'),
            state=dict(default='present', choices=['absent', 'present']),
        ),
        mutually_exclusive=[
            ['etherstub', 'mac'],
            ['etherstub', 'mtu'],
        ],
        required_if=[
            ['etherstub', False, ['name', 'mac']],
            ['state', 'absent', ['name', 'force']],
        ],
        supports_check_mode=True
    )

    nictag = NICTAG(module)

    rc = None
    out = ''
    err = ''
    result = {}
    result['name'] = nictag.name
    result['mac'] = nictag.mac
    result['etherstub'] = nictag.etherstub
    result['mtu'] = nictag.mtu
    result['force'] = nictag.force
    result['state'] = nictag.state

    if not nictag.is_valid_mac():
        module.fail_json(msg='Invalid MAC Address Value',
                         name=nictag.name,
                         mac=nictag.mac,
                         etherstub=nictag.etherstub,
                         mtu=nictag.mtu,
                         force=nictag.force,
                         state=nictag.state)
    result['mac'] = nictag.mac

    if nictag.state == 'absent':
        if nictag.nictag_exists():
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err) = nictag.delete_nictag()
            if rc != 0:
                module.fail_json(name=nictag.name, msg=err, rc=rc)
    elif nictag.state == 'present':
        if not nictag.nictag_exists():
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err) = nictag.add_nictag()
            if rc is not None and rc != 0:
                module.fail_json(name=nictag.name, msg=err, rc=rc)

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
