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
module: ce_snmp_contact
version_added: "2.4"
short_description: Manages SNMP contact configuration on HUAWEI CloudEngine switches.
description:
    - Manages SNMP contact configurations on HUAWEI CloudEngine switches.
author:
    - wangdezhuang (@QijunPan)
notes:
    - Recommended connection is C(network_cli).
    - This module also works with C(local) connections for legacy playbooks.
options:
    contact:
        description:
            - Contact information.
        required: true
    state:
        description:
            - Manage the state of the resource.
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''

- name: CloudEngine snmp contact test
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

  - name: "Config SNMP contact"
    ce_snmp_contact:
      state: present
      contact: call Operator at 010-99999999
      provider: "{{ cli }}"

  - name: "Undo SNMP contact"
    ce_snmp_contact:
      state: absent
      contact: call Operator at 010-99999999
      provider: "{{ cli }}"
'''

RETURN = '''
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: true
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"contact": "call Operator at 010-99999999",
             "state": "present"}
existing:
    description: k/v pairs of existing aaa server
    returned: always
    type: dict
    sample: {}
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample: {"contact": "call Operator at 010-99999999"}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["snmp-agent sys-info contact call Operator at 010-99999999"]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import exec_command, load_config, ce_argument_spec


class SnmpContact(object):
    """ Manages SNMP contact configuration """

    def __init__(self, **kwargs):
        """ Class init """

        # module
        argument_spec = kwargs["argument_spec"]
        self.spec = argument_spec
        self.module = AnsibleModule(argument_spec=self.spec, supports_check_mode=True)

        # config
        self.cur_cfg = dict()

        # module args
        self.state = self.module.params['state']
        self.contact = self.module.params['contact']

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.proposed = dict()
        self.existing = dict()
        self.end_state = dict()

    def check_args(self):
        """ Check invalid args """

        if self.contact:
            if len(self.contact) > 255 or len(self.contact) < 1:
                self.module.fail_json(
                    msg='Error: The len of contact %s is out of [1 - 255].' % self.contact)
        else:
            self.module.fail_json(
                msg='Error: The len of contact is 0.')

    def get_config(self, flags=None):
        """Retrieves the current config from the device or cache
        """
        flags = [] if flags is None else flags

        cmd = 'display current-configuration '
        cmd += ' '.join(flags)
        cmd = cmd.strip()

        rc, out, err = exec_command(self.module, cmd)
        if rc != 0:
            self.module.fail_json(msg=err)
        cfg = str(out).strip()

        return cfg

    def get_proposed(self):
        """ Get proposed state """

        self.proposed["state"] = self.state

        if self.contact:
            self.proposed["contact"] = self.contact

    def get_existing(self):
        """ Get existing state """

        tmp_cfg = self.cli_get_config()
        if tmp_cfg:
            temp_data = tmp_cfg.split(r"contact ")
            if len(temp_data) > 1:
                self.cur_cfg["contact"] = temp_data[1]
                self.existing["contact"] = temp_data[1]

    def get_end_state(self):
        """ Get end state """

        tmp_cfg = self.cli_get_config()
        if tmp_cfg:
            temp_data = tmp_cfg.split(r"contact ")
            if len(temp_data) > 1:
                self.end_state["contact"] = temp_data[1]

    def cli_load_config(self, commands):
        """ Load configure by cli """

        if not self.module.check_mode:
            load_config(self.module, commands)

    def cli_get_config(self):
        """ Get configure by cli """

        regular = "| include snmp | include contact"
        flags = list()
        flags.append(regular)
        tmp_cfg = self.get_config(flags)

        return tmp_cfg

    def set_config(self):
        """ Set configure by cli """

        cmd = "snmp-agent sys-info contact %s" % self.contact
        self.updates_cmd.append(cmd)

        cmds = list()
        cmds.append(cmd)

        self.cli_load_config(cmds)
        self.changed = True

    def undo_config(self):
        """ Undo configure by cli """

        cmd = "undo snmp-agent sys-info contact"
        self.updates_cmd.append(cmd)

        cmds = list()
        cmds.append(cmd)

        self.cli_load_config(cmds)
        self.changed = True

    def work(self):
        """ Main work function """

        self.check_args()
        self.get_proposed()
        self.get_existing()

        if self.state == "present":
            if "contact" in self.cur_cfg.keys() and self.contact == self.cur_cfg["contact"]:
                pass
            else:
                self.set_config()
        else:
            if "contact" in self.cur_cfg.keys() and self.contact == self.cur_cfg["contact"]:
                self.undo_config()

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
        contact=dict(type='str', required=True)
    )

    argument_spec.update(ce_argument_spec)
    module = SnmpContact(argument_spec=argument_spec)
    module.work()


if __name__ == '__main__':
    main()
