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
module: ce_rollback
version_added: "2.4"
short_description: Set a checkpoint or rollback to a checkpoint on HUAWEI CloudEngine switches.
description:
    - This module offers the ability to set a configuration checkpoint
      file or rollback to a configuration checkpoint file on HUAWEI CloudEngine switches.
author:
    - Li Yanfeng (@QijunPan)
notes:
    - Recommended connection is C(network_cli).
    - This module also works with C(local) connections for legacy playbooks.
options:
    commit_id:
        description:
            - Specifies the label of the configuration rollback point to which system configurations are
              expected to roll back.
              The value is an integer that the system generates automatically.
    label:
        description:
            - Specifies a user label for a configuration rollback point.
              The value is a string of 1 to 256 case-sensitive ASCII characters, spaces not supported.
              The value must start with a letter and cannot be presented in a single hyphen (-).
    filename:
        description:
            - Specifies a configuration file for configuration rollback.
              The value is a string of 5 to 64 case-sensitive characters in the format of *.zip, *.cfg, or *.dat,
              spaces not supported.
    last:
        description:
            - Specifies the number of configuration rollback points.
              The value is an integer that ranges from 1 to 80.
    oldest:
        description:
            - Specifies the number of configuration rollback points.
              The value is an integer that ranges from 1 to 80.
    action:
        description:
            - The operation of configuration rollback.
        required: true
        choices: ['rollback','clear','set','display','commit']
'''
EXAMPLES = '''
- name: rollback module test
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

- name: Ensure commit_id is exist, and specifies the label of the configuration rollback point to
        which system configurations are expected to roll back.
  ce_rollback:
    commit_id: 1000000748
    action: rollback
    provider: "{{ cli }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: sometimes
    type: dict
    sample: {"commit_id": "1000000748", "action": "rollback"}
existing:
    description: k/v pairs of existing rollback
    returned: sometimes
    type: dict
    sample: {"commitId": "1000000748", "userLabel": "abc"}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: ["rollback configuration to file a.cfg",
             "set configuration commit 1000000783 label ddd",
             "clear configuration commit 1000000783 label",
             "display configuration commit list"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: bool
    sample: true
end_state:
    description: k/v pairs of configuration after module execution
    returned: always
    type: dict
    sample: {"commitId": "1000000748", "userLabel": "abc"}
'''

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import ce_argument_spec, exec_command, run_commands
from ansible.module_utils.network.common.utils import ComplexList


class RollBack(object):
    """
    Manages rolls back the system from the current configuration state to a historical configuration state.
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = AnsibleModule(argument_spec=self.spec, supports_check_mode=True)
        self.commands = list()
        # module input info
        self.commit_id = self.module.params['commit_id']
        self.label = self.module.params['label']
        self.filename = self.module.params['filename']
        self.last = self.module.params['last']
        self.oldest = self.module.params['oldest']
        self.action = self.module.params['action']

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.existing = dict()
        self.proposed = dict()
        self.end_state = dict()

        # configuration rollback points info
        self.rollback_info = None
        self.init_module()

    def init_module(self):
        """ init module """

        required_if = [('action', 'set', ['commit_id', 'label']), ('action', 'commit', ['label'])]
        mutually_exclusive = None
        required_one_of = None
        if self.action == "rollback":
            required_one_of = [['commit_id', 'label', 'filename', 'last']]
        elif self.action == "clear":
            required_one_of = [['commit_id', 'oldest']]
        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=True, required_if=required_if, mutually_exclusive=mutually_exclusive, required_one_of=required_one_of)

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def cli_add_command(self, command, undo=False):
        """add command to self.update_cmd and self.commands"""
        self.commands.append("return")
        self.commands.append("mmi-mode enable")

        if self.action == "commit":
            self.commands.append("sys")

        self.commands.append(command)
        self.updates_cmd.append(command)

    def cli_load_config(self, commands):
        """load config by cli"""

        if not self.module.check_mode:
            run_commands(self.module, commands)

    def get_config(self, flags=None):
        """Retrieves the current config from the device or cache
        """
        flags = [] if flags is None else flags

        cmd = 'display configuration '
        cmd += ' '.join(flags)
        cmd = cmd.strip()

        rc, out, err = exec_command(self.module, cmd)
        if rc != 0:
            self.module.fail_json(msg=err)
        cfg = str(out).strip()

        return cfg

    def get_rollback_dict(self):
        """ get rollback attributes dict."""

        rollback_info = dict()
        rollback_info["RollBackInfos"] = list()

        flags = list()
        exp = "commit list"
        flags.append(exp)
        cfg_info = self.get_config(flags)
        if not cfg_info:
            return rollback_info

        cfg_line = cfg_info.split("\n")
        for cfg in cfg_line:
            if re.findall(r'^\d', cfg):
                pre_rollback_info = cfg.split()
                rollback_info["RollBackInfos"].append(dict(commitId=pre_rollback_info[1], userLabel=pre_rollback_info[2]))

        return rollback_info

    def get_filename_type(self, filename):
        """Gets the type of filename, such as cfg, zip, dat..."""

        if filename is None:
            return None
        if ' ' in filename:
            self.module.fail_json(
                msg='Error: Configuration file name include spaces.')

        iftype = None

        if filename.endswith('.cfg'):
            iftype = 'cfg'
        elif filename.endswith('.zip'):
            iftype = 'zip'
        elif filename.endswith('.dat'):
            iftype = 'dat'
        else:
            return None
        return iftype.lower()

    def set_config(self):

        if self.action == "rollback":
            if self.commit_id:
                cmd = "rollback configuration to commit-id %s" % self.commit_id
                self.cli_add_command(cmd)
            if self.label:
                cmd = "rollback configuration to label %s" % self.label
                self.cli_add_command(cmd)
            if self.filename:
                cmd = "rollback configuration to file %s" % self.filename
                self.cli_add_command(cmd)
            if self.last:
                cmd = "rollback configuration last %s" % self.last
                self.cli_add_command(cmd)
        elif self.action == "set":
            if self.commit_id and self.label:
                cmd = "set configuration commit %s label %s" % (self.commit_id, self.label)
                self.cli_add_command(cmd)
        elif self.action == "clear":
            if self.commit_id:
                cmd = "clear configuration commit %s label" % self.commit_id
                self.cli_add_command(cmd)
            if self.oldest:
                cmd = "clear configuration commit oldest %s" % self.oldest
                self.cli_add_command(cmd)
        elif self.action == "commit":
            if self.label:
                cmd = "commit label %s" % self.label
                self.cli_add_command(cmd)

        elif self.action == "display":
            self.rollback_info = self.get_rollback_dict()
        if self.commands:
            self.commands.append('return')
            self.commands.append('undo mmi-mode enable')
            self.cli_load_config(self.commands)
            self.changed = True

    def check_params(self):
        """Check all input params"""

        # commit_id check
        rollback_info = self.rollback_info["RollBackInfos"]
        if self.commit_id:
            if not self.commit_id.isdigit():
                self.module.fail_json(
                    msg='Error: The parameter of commit_id is invalid.')

            info_bool = False
            for info in rollback_info:
                if info.get("commitId") == self.commit_id:
                    info_bool = True
            if not info_bool:
                self.module.fail_json(
                    msg='Error: The parameter of commit_id is not exist.')

            if self.action == "clear":
                info_bool = False
                for info in rollback_info:
                    if info.get("commitId") == self.commit_id:
                        if info.get("userLabel") == "-":
                            info_bool = True
                if info_bool:
                    self.module.fail_json(
                        msg='Error: This commit_id does not have a label.')

        # filename check
        if self.filename:
            if not self.get_filename_type(self.filename):
                self.module.fail_json(
                    msg='Error: Invalid file name or file name extension ( *.cfg, *.zip, *.dat ).')
        # last check
        if self.last:
            if not self.last.isdigit():
                self.module.fail_json(
                    msg='Error: Number of configuration checkpoints is not digit.')
            if int(self.last) <= 0 or int(self.last) > 80:
                self.module.fail_json(
                    msg='Error: Number of configuration checkpoints is not in the range from 1 to 80.')

        # oldest check
        if self.oldest:
            if not self.oldest.isdigit():
                self.module.fail_json(
                    msg='Error: Number of configuration checkpoints is not digit.')
            if int(self.oldest) <= 0 or int(self.oldest) > 80:
                self.module.fail_json(
                    msg='Error: Number of configuration checkpoints is not in the range from 1 to 80.')

        # label check
        if self.label:
            if self.label[0].isdigit():
                self.module.fail_json(
                    msg='Error: Commit label which should not start with a number.')
            if len(self.label.replace(' ', '')) == 1:
                if self.label == '-':
                    self.module.fail_json(
                        msg='Error: Commit label which should not be "-"')
            if len(self.label.replace(' ', '')) < 1 or len(self.label) > 256:
                self.module.fail_json(
                    msg='Error: Label of configuration checkpoints is a string of 1 to 256 characters.')

            if self.action == "rollback":
                info_bool = False
                for info in rollback_info:
                    if info.get("userLabel") == self.label:
                        info_bool = True
                if not info_bool:
                    self.module.fail_json(
                        msg='Error: The parameter of userLabel is not exist.')

            if self.action == "commit":
                info_bool = False
                for info in rollback_info:
                    if info.get("userLabel") == self.label:
                        info_bool = True
                if info_bool:
                    self.module.fail_json(
                        msg='Error: The parameter of userLabel is existing.')

            if self.action == "set":
                info_bool = False
                for info in rollback_info:
                    if info.get("commitId") == self.commit_id:
                        if info.get("userLabel") != "-":
                            info_bool = True
                if info_bool:
                    self.module.fail_json(
                        msg='Error: The userLabel of this commitid is present and can be reset after deletion.')

    def get_proposed(self):
        """get proposed info"""

        if self.commit_id:
            self.proposed["commit_id"] = self.commit_id
        if self.label:
            self.proposed["label"] = self.label
        if self.filename:
            self.proposed["filename"] = self.filename
        if self.last:
            self.proposed["last"] = self.last
        if self.oldest:
            self.proposed["oldest"] = self.oldest

    def get_existing(self):
        """get existing info"""
        if not self.rollback_info:
            self.existing["RollBackInfos"] = None
        else:
            self.existing["RollBackInfos"] = self.rollback_info["RollBackInfos"]

    def get_end_state(self):
        """get end state info"""

        rollback_info = self.get_rollback_dict()
        if not rollback_info:
            self.end_state["RollBackInfos"] = None
        else:
            self.end_state["RollBackInfos"] = rollback_info["RollBackInfos"]

    def work(self):
        """worker"""

        self.rollback_info = self.get_rollback_dict()
        self.check_params()
        self.get_proposed()

        self.set_config()

        self.get_existing()
        self.get_end_state()

        self.results['changed'] = self.changed
        self.results['proposed'] = self.proposed
        self.results['existing'] = self.existing
        self.results['end_state'] = self.end_state
        if self.changed:
            self.results['updates'] = self.updates_cmd
        else:
            self.results['updates'] = list()

        self.module.exit_json(**self.results)


def main():
    """Module main"""

    argument_spec = dict(
        commit_id=dict(required=False),
        label=dict(required=False, type='str'),
        filename=dict(required=False, type='str'),
        last=dict(required=False, type='str'),
        oldest=dict(required=False, type='str'),
        action=dict(required=False, type='str', choices=[
            'rollback', 'clear', 'set', 'commit', 'display']),
    )
    argument_spec.update(ce_argument_spec)
    module = RollBack(argument_spec)
    module.work()


if __name__ == '__main__':
    main()
