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
    - Li Yanfeng (@CloudEngine-Ansible)
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
    type: boolean
    sample: true
end_state:
    description: k/v pairs of configuration after module execution
    returned: always
    type: dict
    sample: {"commitId": "1000000748", "userLabel": "abc"}
'''

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import get_nc_config, execute_nc_action, ce_argument_spec, run_commands


CE_NC_GET_CHECKPOINT = """
<filter type="subtree">
  <cfg xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <checkPointInfos>
      <checkPointInfo>
        <commitId></commitId>
        <userLabel></userLabel>
        <userName></userName>
        </checkPointInfo>
      </checkPointInfos>
  </cfg>
</filter>
"""

CE_NC_ACTION_ROLLBACK_COMMIT_ID = """
<action>
  <cfg xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <rollbackByCommitId>
      <commitId>%s</commitId>
    </rollbackByCommitId>
  </cfg>
</action>
"""

CE_NC_ACTION_ROLLBACK_LABEL = """
<action>
  <cfg xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <rollbackByUserLabel>
      <userLabel>%s</userLabel>
    </rollbackByUserLabel>
  </cfg>
</action>
"""

CE_NC_ACTION_ROLLBACK_LAST = """
<action>
  <cfg xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <rollbackByLastNum>
      <checkPointNum>%s</checkPointNum>
    </rollbackByLastNum>
  </cfg>
</action>
"""

CE_NC_ACTION_ROLLBACK_FILE = """
<action>
  <cfg xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <rollbackByFile>
      <fileName>%s</fileName>
    </rollbackByFile>
  </cfg>
</action>
"""

CE_NC_ACTION_SET_COMMIT_ID_LABEL = """
<action>
  <cfg xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <setUserLabelByCommitId>
      <commitId>%s</commitId>
      <userLabel>%s</userLabel>
    </setUserLabelByCommitId>
  </cfg>
</action>
"""

CE_NC_ACTION_CLEAR_COMMIT_ID_LABEL = """
<action>
  <cfg xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <resetUserLabelByCommitId>
      <commitId>%s</commitId>
    </resetUserLabelByCommitId>
  </cfg>
</action>
"""

CE_NC_ACTION_CLEAR_OLDEST_COMMIT_ID = """
<action>
  <cfg xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <delCheckPointByOldestNum>
      <checkPointNum>%s</checkPointNum>
    </delCheckPointByOldestNum>
  </cfg>
</action>
"""


class RollBack(object):
    """
    Manages rolls back the system from the current configuration state to a historical configuration state.
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

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

    def init_module(self):
        """ init module """

        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=True)

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_rollback_dict(self):
        """ get rollback attributes dict."""

        rollback_info = dict()
        conf_str = CE_NC_GET_CHECKPOINT
        xml_str = get_nc_config(self.module, conf_str)
        rollback_info["RollBackInfos"] = list()
        if "<data/>" in xml_str:
            return rollback_info
        else:
            re_find = re.findall(r'.*<commitId>(.*)</commitId>.*\s*'
                                 r'<userName>(.*)</userName>.*\s*'
                                 r'<userLabel>(.*)</userLabel>.*', xml_str)

            for mem in re_find:
                rollback_info["RollBackInfos"].append(
                    dict(commitId=mem[0], userLabel=mem[2]))
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

    def rollback_commit_id(self):
        """rollback comit_id"""

        cfg_xml = ""
        self.updates_cmd.append(
            "rollback configuration to commit-id %s" % self.commit_id)
        cfg_xml = CE_NC_ACTION_ROLLBACK_COMMIT_ID % self.commit_id
        recv_xml = execute_nc_action(self.module, cfg_xml)
        self.check_response(recv_xml, "ROLLBACK_COMMITID")
        self.changed = True

    def rollback_label(self):
        """rollback label"""

        cfg_xml = ""
        self.updates_cmd.append(
            "rollback configuration to label %s" % self.label)
        cfg_xml = CE_NC_ACTION_ROLLBACK_LABEL % self.label
        recv_xml = execute_nc_action(self.module, cfg_xml)
        self.check_response(recv_xml, "ROLLBACK_LABEL")
        self.changed = True

    def rollback_filename(self):
        """rollback filename"""

        cfg_xml = ""
        self.updates_cmd.append(
            "rollback configuration to file %s" % self.filename)
        cfg_xml = CE_NC_ACTION_ROLLBACK_FILE % self.filename
        recv_xml = execute_nc_action(self.module, cfg_xml)
        self.check_response(recv_xml, "ROLLBACK_FILENAME")
        self.changed = True

    def rollback_last(self):
        """rollback last"""

        cfg_xml = ""
        self.updates_cmd.append(
            "rollback configuration to last %s" % self.last)
        cfg_xml = CE_NC_ACTION_ROLLBACK_LAST % self.last
        recv_xml = execute_nc_action(self.module, cfg_xml)
        self.check_response(recv_xml, "ROLLBACK_LAST")
        self.changed = True

    def set_commitid_label(self):
        """set commitid label"""

        cfg_xml = ""
        self.updates_cmd.append(
            "set configuration commit %s label %s" % (self.commit_id, self.label))
        cfg_xml = CE_NC_ACTION_SET_COMMIT_ID_LABEL % (
            self.commit_id, self.label)
        recv_xml = execute_nc_action(self.module, cfg_xml)
        self.check_response(recv_xml, "SET_COMIMIT_LABEL")
        self.changed = True

    def clear_commitid_label(self):
        """clear commitid label"""

        cfg_xml = ""
        self.updates_cmd.append(
            "clear configuration commit %s label" % self.commit_id)
        cfg_xml = CE_NC_ACTION_CLEAR_COMMIT_ID_LABEL % self.commit_id
        recv_xml = execute_nc_action(self.module, cfg_xml)
        self.check_response(recv_xml, "CLEAR_COMMIT_LABEL")
        self.changed = True

    def clear_oldest(self):
        """clear oldest"""

        cfg_xml = ""
        self.updates_cmd.append(
            "clear configuration commit oldest %s" % self.oldest)
        cfg_xml = CE_NC_ACTION_CLEAR_OLDEST_COMMIT_ID % self.oldest
        recv_xml = execute_nc_action(self.module, cfg_xml)
        self.check_response(recv_xml, "CLEAR_COMMIT_OLDEST")
        self.changed = True

    def commit_label(self):
        """commit label"""

        commands = list()
        cmd1 = {'output': None, 'command': 'system-view'}
        commands.append(cmd1)

        cmd2 = {'output': None, 'command': ''}
        cmd2['command'] = "commit label %s" % self.label
        commands.append(cmd2)
        self.updates_cmd.append(
            "commit label %s" % self.label)
        run_commands(self.module, commands)
        self.changed = True

    def check_params(self):
        """Check all input params"""

        # commit_id check
        if self.commit_id:
            if not self.commit_id.isdigit():
                self.module.fail_json(
                    msg='Error: The parameter of commit_id is invalid.')

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
            return
        self.existing["RollBackInfos"] = self.rollback_info["RollBackInfos"]

    def get_end_state(self):
        """get end state info"""

        self.end_state = None

    def work(self):
        """worker"""

        self.check_params()
        self.get_proposed()
        # action mode
        if self.action == "rollback":
            if self.commit_id:
                self.rollback_commit_id()
            if self.label:
                self.rollback_label()
            if self.filename:
                self.rollback_filename()
            if self.last:
                self.rollback_last()
        elif self.action == "set":
            if self.commit_id and self.label:
                self.set_commitid_label()
        elif self.action == "clear":
            if self.commit_id:
                self.clear_commitid_label()
            if self.oldest:
                self.clear_oldest()
        elif self.action == "commit":
            if self.label:
                self.commit_label()
        elif self.action == "display":
            self.rollback_info = self.get_rollback_dict()

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
