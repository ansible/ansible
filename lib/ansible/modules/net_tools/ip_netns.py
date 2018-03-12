#!/usr/bin/python
# (c) 2017, Arie Bregman <abregman@redhat.com>
#
# This file is a module for Ansible that interacts with Network Manager
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.    If not, see <http://www.gnu.org/licenses/>.
from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ip_netns
version_added: 2.5
author: "Arie Bregman (@bregman-arie)"
short_description: Manage network namespaces
requirements: [ ip ]
description:
    - Create or delete network namespaces using the ip command.
options:
    name:
        required: True
        description:
            - Name of the namespace
    interfaces:
        required: True
        default: None
        description:
            - List of interface names that need to be part of the namespace
    state:
        required: True
        choices: [ present, absent ]
        description:
            - Whether the namespace should exist
'''

EXAMPLES = '''
# Create a namespace named mario
- name: Create a namespace named mario
  ip_netns:
    name: mario
    state: present
# Create a namespace name mario and add eth1, eth2 interfaces to it
- name: Create a namespace named mario and add interfaces
  ip_netns:
    name: mario
    interfaces:
        - eth1
        - eth2
    operation: add
    state: present
- name: Delete a namespace named luigi
  ip_netns:
    name: luigi
    state: absent
- name: Create a namespace named mario and remove interfaces
  ip_netns:
    name: mario
    interfaces:
        - eth1
        - eth2
    operation: remove
    state: present
'''

RETURN = '''
# Default return values
'''

from ansible.module_utils.basic import AnsibleModule
import re

class Namespace(object):
    """ Interface to network namespaces. """

    def __init__(self, module):
        self.module = module
        self.name = module.params['name']
        self.interfaces = module.params['interfaces']
        self.operation = module.params['operation']
        self.state = module.params['state']

    def get_interfaces(self):
        ''' Fetch list of interface names present in namespace '''
        rc, ifconfig, err= self._netns_interface()
        if rc != 0:
            self.module.fail_json(msg=err)
        name = '^\d+:\s(\w+):\s.*'
	regex = re.compile(name, flags=re.MULTILINE)
        return  regex.findall(ifconfig.decode())

    def _netns(self, command):
        ''' Run ip nents command '''
        return self.module.run_command(['ip', 'netns'] + command)

    def _netns_interface(self, interface=None, op='ls'):
        ''' List or add or remove interfaces inside namespace '''
        if op.lower() == 'ls':
            ''' list interfaces in the namespace '''
            return self.module.run_command(['ip', 'netns', 'exec', self.name, 'ip', 'a', 's'])
        elif op.lower() == 'add':
            ''' Attach interfaces to the namespace '''
            return self.module.run_command(['ip', 'link', 'set', interface, 'netns', self.name])
        elif op.lower() == 'remove':
            ''' Delete interfaces from the namespace '''
            return self.module.run_command(['ip', 'netns', 'exec', self.name,  'ip', 'link', 'set', interface, 'netns', '1'])

    def exists(self):
        ''' Check if the namespace already exists '''
        rc, out, err = self._netns(['ls'])
        if rc != 0:
            self.module.fail_json(msg=err)
        return self.name in out.split('\n')

    def add(self):
        ''' Create network namespace '''
        rc, out, err = self._netns(['add', self.name])

        if rc != 0:
            self.module.fail_json(msg=err)

    def op_interfaces(self, operation='add'):
        ''' Add/Remove interfaces to/from the namespace '''
        interface_changed = False
        ns_interfaces = self.get_interfaces()
        for interface in self.interfaces:
            if operation == 'add':
                if interface not in ns_interfaces:
                    rc, out, err = self._netns_interface(interface, op='add')
                    if rc != 0:
                        self.module.fail_json(msg=err)
                    interface_changed = True
            elif operation == 'remove':
                if interface in ns_interfaces:
                    rc, out, err = self._netns_interface(interface, op='remove')
                    if rc != 0:
                        self.module.fail_json(msg=err)
                    interface_changed = True
                else:
                    self.module.fail_json(msg='Interface {0} is not associated with namespace {1}'.format(interface, self.name))

        return interface_changed

    def delete(self):
        ''' Delete network namespace '''
        rc, out, err = self._netns(['del', self.name])
        if rc != 0:
            self.module.fail_json(msg=err)

    def check(self):
        ''' Run check mode '''
        changed = False

        if self.state == 'present' and self.exists():
                changed = True

        elif self.state == 'absent' and self.exists():
            changed = True

        elif self.state == 'present' and not self.exists():
            changed = True

        self.module.exit_json(changed=changed)

    def run(self):
        ''' Make the necessary changes '''
        changed = False
        interface_changed = False

        if self.state == 'absent':
            if self.exists():
                self.delete()
                changed = True
        elif self.state == 'present':
            if not self.exists():
                self.add()
                changed = True
            if self.exists() and self.interfaces:
                if self.operation == 'add':
                    interface_changed = self.op_interfaces()
                elif self.operation == 'remove':
                    interface_changed = self.op_interfaces(operation='remove')

        self.module.exit_json(changed=changed or interface_changed)


def main():
    """ Entry point. """
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, type='str'),
            interfaces=dict(required=False, default=None, type='list'),
            operation=dict(required=False, default='add', choices=['add', 'remove']),
            state=dict(required=True, choices=['present', 'absent'], type='str'),
        ),
        required_together=(
            ['interfaces', 'operation']
        ),
        supports_check_mode=True,
    )

    network_namespace = Namespace(module)
    if module.check_mode:
        network_namespace.check()
    else:
        network_namespace.run()


if __name__ == '__main__':
    main()
