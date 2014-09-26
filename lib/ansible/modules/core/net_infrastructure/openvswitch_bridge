#!/usr/bin/python
#coding: utf-8 -*-

# (c) 2013, David Stygstra <david.stygstra@gmail.com>
#
# This file is part of Ansible
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: openvswitch_bridge
version_added: 1.4
author: David Stygstra
short_description: Manage Open vSwitch bridges
requirements: [ ovs-vsctl ]
description:
    - Manage Open vSwitch bridges
options:
    bridge:
        required: true
        description:
            - Name of bridge to manage
    state:
        required: false
        default: "present"
        choices: [ present, absent ]
        description:
            - Whether the bridge should exist
    timeout:
        required: false
        default: 5
        description:
            - How long to wait for ovs-vswitchd to respond
'''

EXAMPLES = '''
# Create a bridge named br-int
- openvswitch_bridge: bridge=br-int state=present
'''


class OVSBridge(object):
    def __init__(self, module):
        self.module = module
        self.bridge = module.params['bridge']
        self.state = module.params['state']
        self.timeout = module.params['timeout']

    def _vsctl(self, command):
        '''Run ovs-vsctl command'''
        return self.module.run_command(['ovs-vsctl', '-t', str(self.timeout)] + command)

    def exists(self):
        '''Check if the bridge already exists'''
        rc, _, err = self._vsctl(['br-exists', self.bridge])
        if rc == 0:  # See ovs-vsctl(8) for status codes
            return True
        if rc == 2:
            return False
        raise Exception(err)

    def add(self):
        '''Create the bridge'''
        rc, _, err = self._vsctl(['add-br', self.bridge])
        if rc != 0:
            raise Exception(err)

    def delete(self):
        '''Delete the bridge'''
        rc, _, err = self._vsctl(['del-br', self.bridge])
        if rc != 0:
            raise Exception(err)

    def check(self):
        '''Run check mode'''
        try:
            if self.state == 'absent' and self.exists():
                changed = True
            elif self.state == 'present' and not self.exists():
                changed = True
            else:
                changed = False
        except Exception, e:
            self.module.fail_json(msg=str(e))
        self.module.exit_json(changed=changed)

    def run(self):
        '''Make the necessary changes'''
        changed = False
        try:
            if self.state == 'absent':
                if self.exists():
                    self.delete()
                    changed = True
            elif self.state == 'present':
                if not self.exists():
                    self.add()
                    changed = True
        except Exception, e:
            self.module.fail_json(msg=str(e))
        self.module.exit_json(changed=changed)


def main():
    module = AnsibleModule(
        argument_spec={
            'bridge': {'required': True},
            'state': {'default': 'present', 'choices': ['present', 'absent']},
            'timeout': {'default': 5, 'type': 'int'}
        },
        supports_check_mode=True,
    )

    br = OVSBridge(module)
    if module.check_mode:
        br.check()
    else:
        br.run()


# import module snippets
from ansible.module_utils.basic import *
main()
