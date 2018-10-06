#!/usr/bin/python
# (c) 2017, Arie Bregman <abregman@redhat.com>
#
# This file is a module for Ansible that interacts with ip-netns module
# of iproute.
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

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
        required: false
        description:
            - Name of the namespace
    state:
        required: false
        default: "present"
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

- name: Assign an id to a peer network namespace
  ip_netns:
    name: luigi
    netnsid: 14

- name: Run cmd in the named network namespace
  ip_netns:
    name: luigi
    command: "ip link set dev eth0 up"

- name: Delete a namespace named luigi
  ip_netns:
    name: luigi
    state: absent
'''

RETURN = '''
# Default return values
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_text


class Namespace(object):
    """Interface to network namespaces. """

    def __init__(self, module):
        self.module = module
        self.ip_bin = self.module.get_bin_path('ip', True)
        self.name = module.params['name']
        self.netnsid = module.params['netnsid']
        self.command = module.params['command']
        self.state = module.params['state']

    def _netns(self, command):
        '''Run ip nents command'''
        return self.module.run_command([self.ip_bin, 'netns'] + command)

    def exists(self):
        '''Check if the namespace already exists'''
        rc, out, err = self.module.run_command('ip netns list')
        if rc != 0:
            self.module.fail_json(msg=to_text(err))
        return self.name in out

    def add(self):
        '''Create network namespace'''
        rtc, out, err = self._netns(['add', self.name])

        if rtc != 0:
            self.module.fail_json(msg=err)

    def setnsid(self):
        '''Assign an id to a peer network namespace'''
        rtc, out, err = self._netns(['set', self.name, self.netnsid])

        if rtc != 0:
            self.module.fail_json(msg=err)

    def delete(self):
        '''Delete network namespace'''
        rtc, out, err = self._netns(['del', self.name])
        if rtc != 0:
            self.module.fail_json(msg=err)

    def nsexec(self):
        '''Run command in the named network namespace'''
        cmd = ['exec', self.name]

        cmd_list = self.command.split()
        for c in cmd_list:
            cmd.append(c)

        rtc, out, err = self._netns(cmd)
        if rtc != 0:
            self.module.fail_json(msg=err)

    def check(self):
        '''Run check mode'''
        changed = False

        if self.state == 'present' and self.exists():
                changed = True

        elif self.state == 'absent' and self.exists():
            changed = True
        elif self.state == 'present' and not self.exists():
            changed = True

        self.module.exit_json(changed=changed)

    def run(self):
        '''Make the necessary changes'''
        changed = False

        if self.state == 'absent':
            if self.exists():
                self.delete()
                changed = True
        elif self.state == 'present':
            if not self.exists():
                self.add()
                changed = True
            elif self.exists() and self.netnsid:
                self.setnsid()
                changed = True

        if self.command and self.exists():
            self.nsexec()
            changed = True

        self.module.exit_json(changed=changed)


def main():
    """Entry point."""
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(default=None, type='str'),
            netnsid=dict(default=None, type='str'),
            command=dict(default=None, type='str'),
            state=dict(default='present', choices=['present', 'absent'], type='str'),
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
