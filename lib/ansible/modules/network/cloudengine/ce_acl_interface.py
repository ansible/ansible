#!/usr/bin/python
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ce_acl_interface
version_added: "2.4"
short_description: Manages applying ACLs to interfaces on HUAWEI CloudEngine switches.
description:
    - Manages applying ACLs to interfaces on HUAWEI CloudEngine switches.
author:
    - wangdezhuang (@CloudEngine-Ansible)
options:
    acl_name:
        description:
            - ACL number or name.
              For a numbered rule group, the value ranging from 2000 to 4999.
              For a named rule group, the value is a string of 1 to 32 case-sensitive characters starting
              with a letter, spaces not supported.
        required: true
    interface:
        description:
            - Interface name.
              Only support interface full name, such as "40GE2/0/1".
        required: true
    direction:
        description:
            - Direction ACL to be applied in on the interface.
        required: true
        choices: ['inbound', 'outbound']
    state:
        description:
            - Determines whether the config should be present or not on the device.
        required: false
        default: present
        choices: ['present', 'absent']
'''

EXAMPLES = '''

- name: CloudEngine acl interface test
  hosts: cloudengine
  connection: local
  gather_facts: no
  vars:
    cli:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ username }}"
      password: "{{ password }}"
      transport: cli

  tasks:

  - name: "Apply acl to interface"
    ce_acl_interface:
      state: present
      acl_name: 2000
      interface: 40GE1/0/1
      direction: outbound
      provider: "{{ cli }}"

  - name: "Undo acl from interface"
    ce_acl_interface:
      state: absent
      acl_name: 2000
      interface: 40GE1/0/1
      direction: outbound
      provider: "{{ cli }}"
'''

RETURN = '''
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"acl_name": "2000",
             "direction": "outbound",
             "interface": "40GE2/0/1",
             "state": "present"}
existing:
    description: k/v pairs of existing aaa server
    returned: always
    type: dict
    sample: {"acl interface": "traffic-filter acl lb inbound"}
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample: {"acl interface": ["traffic-filter acl lb inbound", "traffic-filter acl 2000 outbound"]}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["interface 40ge2/0/1",
             "traffic-filter acl 2000 outbound"]
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import get_config, load_config
from ansible.module_utils.network.cloudengine.ce import ce_argument_spec


class AclInterface(object):
    """ Manages acl interface configuration """

    def __init__(self, **kwargs):
        """ Class init """

        # argument spec
        argument_spec = kwargs["argument_spec"]
        self.spec = argument_spec
        self.module = AnsibleModule(argument_spec=self.spec, supports_check_mode=True)

        # config
        self.cur_cfg = dict()
        self.cur_cfg["acl interface"] = []

        # module args
        self.state = self.module.params['state']
        self.acl_name = self.module.params['acl_name']
        self.interface = self.module.params['interface']
        self.direction = self.module.params['direction']

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def check_args(self):
        """ Check args """

        if self.acl_name:
            if self.acl_name.isdigit():
                if int(self.acl_name) < 2000 or int(self.acl_name) > 4999:
                    self.module.fail_json(
                        msg='Error: The value of acl_name is out of [2000 - 4999].')
            else:
                if len(self.acl_name) < 1 or len(self.acl_name) > 32:
                    self.module.fail_json(
                        msg='Error: The len of acl_name is out of [1 - 32].')

        if self.interface:
            regular = "| ignore-case section include ^interface %s$" % self.interface
            result = self.cli_get_config(regular)
            if not result:
                self.module.fail_json(
                    msg='Error: The interface %s is not in the device.' % self.interface)

    def get_proposed(self):
        """ Get proposed config """

        self.proposed["state"] = self.state

        if self.acl_name:
            self.proposed["acl_name"] = self.acl_name

        if self.interface:
            self.proposed["interface"] = self.interface

        if self.direction:
            self.proposed["direction"] = self.direction

    def get_existing(self):
        """ Get existing config """

        regular = "| ignore-case section include ^interface %s$ | include traffic-filter" % self.interface
        result = self.cli_get_config(regular)

        end = []
        if result:
            tmp = result.split('\n')
            for item in tmp:
                end.append(item)
            self.cur_cfg["acl interface"] = end
            self.existing["acl interface"] = end

    def get_end_state(self):
        """ Get config end state """

        regular = "| ignore-case section include ^interface %s$ | include traffic-filter" % self.interface
        result = self.cli_get_config(regular)
        end = []
        if result:
            tmp = result.split('\n')
            for item in tmp:
                item = item[1:-1]
                end.append(item)
            self.end_state["acl interface"] = end

    def cli_load_config(self, commands):
        """ Cli method to load config """

        if not self.module.check_mode:
            load_config(self.module, commands)

    def cli_get_config(self, regular):
        """ Cli method to get config """

        flags = list()
        flags.append(regular)
        tmp_cfg = get_config(self.module, flags)

        return tmp_cfg

    def work(self):
        """ Work function """

        self.check_args()
        self.get_proposed()
        self.get_existing()

        cmds = list()
        tmp_cmd = "traffic-filter acl %s %s" % (self.acl_name, self.direction)
        undo_tmp_cmd = "undo traffic-filter acl %s %s" % (
            self.acl_name, self.direction)

        if self.state == "present":
            if tmp_cmd not in self.cur_cfg["acl interface"]:
                interface_cmd = "interface %s" % self.interface.lower()
                cmds.append(interface_cmd)
                cmds.append(tmp_cmd)

                self.cli_load_config(cmds)

                self.changed = True
                self.updates_cmd.append(interface_cmd)
                self.updates_cmd.append(tmp_cmd)

        else:
            if tmp_cmd in self.cur_cfg["acl interface"]:
                interface_cmd = "interface %s" % self.interface
                cmds.append(interface_cmd)
                cmds.append(undo_tmp_cmd)
                self.cli_load_config(cmds)

                self.changed = True
                self.updates_cmd.append(interface_cmd)
                self.updates_cmd.append(undo_tmp_cmd)

        self.get_end_state()

        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state
        self.results['updates'] = self.updates_cmd

        self.module.exit_json(**self.results)


def main():
    """ Module main """

    argument_spec = dict(
        state=dict(choices=['present', 'absent'], default='present'),
        acl_name=dict(type='str', required=True),
        interface=dict(type='str', required=True),
        direction=dict(choices=['inbound', 'outbound'], required=True)
    )

    argument_spec.update(ce_argument_spec)
    module = AclInterface(argument_spec=argument_spec)
    module.work()


if __name__ == '__main__':
    main()
