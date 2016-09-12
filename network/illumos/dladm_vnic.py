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
module: dladm_vnic
short_description: Manage VNICs on Solaris/illumos systems.
description:
    - Create or delete VNICs on Solaris/illumos systems.
version_added: "2.2"
author: Adam Števko (@xen0l)
options:
    name:
        description:
            - VNIC name.
        required: true
    link:
        description:
            - VNIC underlying link name.
        required: true
    temporary:
        description:
            - Specifies that the VNIC is temporary. Temporary VNICs
              do not persist across reboots.
        required: false
        default: false
        choices: [ "true", "false" ]
    mac:
        description:
            - Sets the VNIC's MAC address. Must be valid unicast MAC address.
        required: false
        default: false
        aliases: [ "macaddr" ]
    vlan:
        description:
            - Enable VLAN tagging for this VNIC. The VLAN tag will have id
              I(vlan).
        required: false
        default: false
        aliases: [ "vlan_id" ]
    state:
        description:
            - Create or delete Solaris/illumos VNIC.
        required: false
        default: "present"
        choices: [ "present", "absent" ]
'''

EXAMPLES = '''
# Create 'vnic0' VNIC over 'bnx0' link
dladm_vnic: name=vnic0 link=bnx0 state=present

# Create VNIC with specified MAC and VLAN tag over 'aggr0'
dladm_vnic: name=vnic1 link=aggr0 mac=00:00:5E:00:53:23 vlan=4

# Remove 'vnic0' VNIC
dladm_vnic: name=vnic0 link=bnx0 state=absent
'''

RETURN = '''
name:
    description: VNIC name
    returned: always
    type: string
    sample: "vnic0"
link:
    description: VNIC underlying link name
    returned: always
    type: string
    sample: "igb0"
state:
    description: state of the target
    returned: always
    type: string
    sample: "present"
temporary:
    description: VNIC's persistence
    returned: always
    type: boolean
    sample: "True"
mac:
    description: MAC address to use for VNIC
    returned: if mac is specified
    type: string
    sample: "00:00:5E:00:53:42"
vlan:
    description: VLAN to use for VNIC
    returned: success
    type: int
    sample: 42
'''

import re


class VNIC(object):

    UNICAST_MAC_REGEX = r'^[a-f0-9][2-9a-f0]:([a-f0-9]{2}:){4}[a-f0-9]{2}$'

    def __init__(self, module):
        self.module = module

        self.name = module.params['name']
        self.link = module.params['link']
        self.mac = module.params['mac']
        self.vlan = module.params['vlan']
        self.temporary = module.params['temporary']
        self.state = module.params['state']

    def vnic_exists(self):
        cmd = [self.module.get_bin_path('dladm', True)]

        cmd.append('show-vnic')
        cmd.append(self.name)

        (rc, _, _) = self.module.run_command(cmd)

        if rc == 0:
            return True
        else:
            return False

    def create_vnic(self):
        cmd = [self.module.get_bin_path('dladm', True)]

        cmd.append('create-vnic')

        if self.temporary:
            cmd.append('-t')

        if self.mac:
            cmd.append('-m')
            cmd.append(self.mac)

        if self.vlan:
            cmd.append('-v')
            cmd.append(self.vlan)

        cmd.append('-l')
        cmd.append(self.link)
        cmd.append(self.name)

        return self.module.run_command(cmd)

    def delete_vnic(self):
        cmd = [self.module.get_bin_path('dladm', True)]

        cmd.append('delete-vnic')

        if self.temporary:
            cmd.append('-t')
        cmd.append(self.name)

        return self.module.run_command(cmd)

    def is_valid_unicast_mac(self):

        mac_re = re.match(self.UNICAST_MAC_REGEX, self.mac)

        return mac_re is None

    def is_valid_vlan_id(self):

        return 0 <= self.vlan <= 4095


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            link=dict(required=True),
            mac=dict(default=None, aliases=['macaddr']),
            vlan=dict(default=None, aliases=['vlan_id']),
            temporary=dict(default=False, type='bool'),
            state=dict(default='present', choices=['absent', 'present']),
        ),
        supports_check_mode=True
    )

    vnic = VNIC(module)

    rc = None
    out = ''
    err = ''
    result = {}
    result['name'] = vnic.name
    result['link'] = vnic.link
    result['state'] = vnic.state
    result['temporary'] = vnic.temporary

    if vnic.mac is not None:
        if vnic.is_valid_unicast_mac():
            module.fail_json(msg='Invalid unicast MAC address',
                             mac=vnic.mac,
                             name=vnic.name,
                             state=vnic.state,
                             link=vnic.link,
                             vlan=vnic.vlan)
        result['mac'] = vnic.mac

    if vnic.vlan is not None:
        if vnic.is_valid_vlan_id():
            module.fail_json(msg='Invalid VLAN tag',
                             mac=vnic.mac,
                             name=vnic.name,
                             state=vnic.state,
                             link=vnic.link,
                             vlan=vnic.vlan)
        result['vlan'] = vnic.vlan

    if vnic.state == 'absent':
        if vnic.vnic_exists():
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err) = vnic.delete_vnic()
            if rc != 0:
                module.fail_json(name=vnic.name, msg=err, rc=rc)
    elif vnic.state == 'present':
        if not vnic.vnic_exists():
            if module.check_mode:
                module.exit_json(changed=True)
            (rc, out, err) = vnic.create_vnic()

        if rc is not None and rc != 0:
            module.fail_json(name=vnic.name, msg=err, rc=rc)

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
