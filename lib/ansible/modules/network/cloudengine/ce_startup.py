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
module: ce_startup
version_added: "2.4"
short_description: Manages a system startup information on HUAWEI CloudEngine switches.
description:
    - Manages a system startup information on HUAWEI CloudEngine switches.
author:
    - Li Yanfeng (@QijunPan)
options:
    cfg_file:
        description:
            - Name of the configuration file that is applied for the next startup.
              The value is a string of 5 to 255 characters.
        default: present
    software_file:
        description:
            - File name of the system software that is applied for the next startup.
              The value is a string of 5 to 255 characters.
    patch_file:
        description:
            - Name of the patch file that is applied for the next startup.
    slot:
        description:
            - Position of the device.The value is a string of 1 to 32 characters.
              The possible value of slot is all, slave-board, or the specific slotID.
    action:
        description:
            - Display the startup information.
        choices: ['display']

'''

EXAMPLES = '''
- name: startup module test
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

  - name: Display startup information
    ce_startup:
      action: display
      provider: "{{ cli }}"

  - name: Set startup patch file
    ce_startup:
      patch_file: 2.PAT
      slot: all
      provider: "{{ cli }}"

  - name: Set startup software file
    ce_startup:
      software_file: aa.cc
      slot: 1
      provider: "{{ cli }}"

  - name: Set startup cfg file
    ce_startup:
      cfg_file: 2.cfg
      slot: 1
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
    sample: {"patch_file": "2.PAT",
             "slot": "all"}
existing:
    description: k/v pairs of existing aaa server
    returned: always
    type: dict
    sample: {
                "configSysSoft": "flash:/CE12800-V200R002C20_issuB071.cc",
                "curentPatchFile": "NULL",
                "curentStartupFile": "NULL",
                "curentSysSoft": "flash:/CE12800-V200R002C20_issuB071.cc",
                "nextPatchFile": "flash:/1.PAT",
                "nextStartupFile": "flash:/1.cfg",
                "nextSysSoft": "flash:/CE12800-V200R002C20_issuB071.cc",
                "position": "5"
            }
end_state:
    description: k/v pairs of aaa params after module execution
    returned: always
    type: dict
    sample: {"StartupInfos": null}
updates:
    description: command sent to the device
    returned: always
    type: list
    sample: {"startup patch 2.PAT all"}
'''

import re
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import get_nc_config, ce_argument_spec, run_commands


CE_NC_GET_STARTUP_INFO = """
<filter type="subtree">
  <cfg xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
    <startupInfos>
      <startupInfo>
        <position></position>
        <configedSysSoft></configedSysSoft>
        <curSysSoft></curSysSoft>
        <nextSysSoft></nextSysSoft>
        <curStartupFile></curStartupFile>
        <nextStartupFile></nextStartupFile>
        <curPatchFile></curPatchFile>
        <nextPatchFile></nextPatchFile>
      </startupInfo>
    </startupInfos>
  </cfg>
</filter>
"""


class StartUp(object):
    """
    Manages system startup information.
    """

    def __init__(self, argument_spec):
        self.spec = argument_spec
        self.module = None
        self.init_module()

        # module input info
        self.cfg_file = self.module.params['cfg_file']
        self.software_file = self.module.params['software_file']
        self.patch_file = self.module.params['patch_file']
        self.slot = self.module.params['slot']
        self.action = self.module.params['action']

        # state
        self.changed = False
        self.updates_cmd = list()
        self.results = dict()
        self.existing = dict()
        self.proposed = dict()
        self.end_state = dict()

        # system startup info
        self.startup_info = None

    def init_module(self):
        """ init module """

        self.module = AnsibleModule(
            argument_spec=self.spec, supports_check_mode=True)

    def check_response(self, xml_str, xml_name):
        """Check if response message is already succeed."""

        if "<ok/>" not in xml_str:
            self.module.fail_json(msg='Error: %s failed.' % xml_name)

    def get_startup_dict(self):
        """ get rollback attributes dict."""

        startup_info = dict()
        conf_str = CE_NC_GET_STARTUP_INFO
        xml_str = get_nc_config(self.module, conf_str)

        startup_info["StartupInfos"] = list()
        if "<data/>" in xml_str:
            return startup_info
        else:
            re_find = re.findall(r'.*<position>(.*)</position>.*\s*'
                                 r'<nextStartupFile>(.*)</nextStartupFile>.*\s*'
                                 r'<configedSysSoft>(.*)</configedSysSoft>.*\s*'
                                 r'<curSysSoft>(.*)</curSysSoft>.*\s*'
                                 r'<nextSysSoft>(.*)</nextSysSoft>.*\s*'
                                 r'<curStartupFile>(.*)</curStartupFile>.*\s*'
                                 r'<curPatchFile>(.*)</curPatchFile>.*\s*'
                                 r'<nextPatchFile>(.*)</nextPatchFile>.*', xml_str)
            for mem in re_find:
                startup_info["StartupInfos"].append(
                    dict(position=mem[0], nextStartupFile=mem[1], configSysSoft=mem[2], curentSysSoft=mem[3],
                         nextSysSoft=mem[4], curentStartupFile=mem[5], curentPatchFile=mem[6], nextPatchFile=mem[7]))
            return startup_info

    def get_cfg_filename_type(self, filename):
        """Gets the type of cfg filename, such as cfg, zip, dat..."""

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

    def get_pat_filename_type(self, filename):
        """Gets the type of patch filename, such as cfg, zip, dat..."""

        if filename is None:
            return None
        if ' ' in filename:
            self.module.fail_json(
                msg='Error: Patch file name include spaces.')

        iftype = None

        if filename.endswith('.PAT'):
            iftype = 'PAT'
        else:
            return None
        return iftype.upper()

    def get_software_filename_type(self, filename):
        """Gets the type of software filename, such as cfg, zip, dat..."""

        if filename is None:
            return None
        if ' ' in filename:
            self.module.fail_json(
                msg='Error: Software file name include spaces.')

        iftype = None

        if filename.endswith('.cc'):
            iftype = 'cc'
        else:
            return None
        return iftype.lower()

    def startup_next_cfg_file(self):
        """set next cfg file"""
        commands = list()
        cmd = {'output': None, 'command': ''}
        if self.slot:
            cmd['command'] = "startup saved-configuration %s slot %s" % (
                self.cfg_file, self.slot)
            commands.append(cmd)
            self.updates_cmd.append(
                "startup saved-configuration %s slot %s" % (self.cfg_file, self.slot))
            run_commands(self.module, commands)
            self.changed = True
        else:
            cmd['command'] = "startup saved-configuration %s" % self.cfg_file
            commands.append(cmd)
            self.updates_cmd.append(
                "startup saved-configuration %s" % self.cfg_file)
            run_commands(self.module, commands)
            self.changed = True

    def startup_next_software_file(self):
        """set next software file"""
        commands = list()
        cmd = {'output': None, 'command': ''}
        if self.slot:
            if self.slot == "all" or self.slot == "slave-board":
                cmd['command'] = "startup system-software %s %s" % (
                    self.software_file, self.slot)
                commands.append(cmd)
                self.updates_cmd.append(
                    "startup system-software %s %s" % (self.software_file, self.slot))
                run_commands(self.module, commands)
                self.changed = True
            else:
                cmd['command'] = "startup system-software %s slot %s" % (
                    self.software_file, self.slot)
                commands.append(cmd)
                self.updates_cmd.append(
                    "startup system-software %s slot %s" % (self.software_file, self.slot))
                run_commands(self.module, commands)
                self.changed = True

        if not self.slot:
            cmd['command'] = "startup system-software %s" % self.software_file
            commands.append(cmd)
            self.updates_cmd.append(
                "startup system-software %s" % self.software_file)
            run_commands(self.module, commands)
            self.changed = True

    def startup_next_pat_file(self):
        """set next patch file"""

        commands = list()
        cmd = {'output': None, 'command': ''}
        if self.slot:
            if self.slot == "all":
                cmd['command'] = "startup patch %s %s" % (
                    self.patch_file, self.slot)
                commands.append(cmd)
                self.updates_cmd.append(
                    "startup patch %s %s" % (self.patch_file, self.slot))
                run_commands(self.module, commands)
                self.changed = True
            else:
                cmd['command'] = "startup patch %s slot %s" % (
                    self.patch_file, self.slot)
                commands.append(cmd)
                self.updates_cmd.append(
                    "startup patch %s slot %s" % (self.patch_file, self.slot))
                run_commands(self.module, commands)
                self.changed = True

        if not self.slot:
            cmd['command'] = "startup patch %s" % self.patch_file
            commands.append(cmd)
            self.updates_cmd.append(
                "startup patch %s" % self.patch_file)
            run_commands(self.module, commands)
            self.changed = True

    def check_params(self):
        """Check all input params"""

        # cfg_file check
        if self.cfg_file:
            if not self.get_cfg_filename_type(self.cfg_file):
                self.module.fail_json(
                    msg='Error: Invalid cfg file name or cfg file name extension ( *.cfg, *.zip, *.dat ).')

        # software_file check
        if self.software_file:
            if not self.get_software_filename_type(self.software_file):
                self.module.fail_json(
                    msg='Error: Invalid software file name or software file name extension ( *.cc).')

        # patch_file check
        if self.patch_file:
            if not self.get_pat_filename_type(self.patch_file):
                self.module.fail_json(
                    msg='Error: Invalid patch file name or patch file name extension ( *.PAT ).')

        # slot check
        if self.slot:
            if self.slot.isdigit():
                if int(self.slot) <= 0 or int(self.slot) > 16:
                    self.module.fail_json(
                        msg='Error: The number of slot is not in the range from 1 to 16.')
            else:
                if len(self.slot) <= 0 or len(self.slot) > 32:
                    self.module.fail_json(
                        msg='Error: The length of slot is not in the range from 1 to 32.')

    def get_proposed(self):
        """get proposed info"""

        if self.cfg_file:
            self.proposed["cfg_file"] = self.cfg_file
        if self.software_file:
            self.proposed["system_file"] = self.software_file
        if self.patch_file:
            self.proposed["patch_file"] = self.patch_file
        if self.slot:
            self.proposed["slot"] = self.slot

    def get_existing(self):
        """get existing info"""

        if not self.startup_info:
            return
        self.existing["StartupInfos"] = self.startup_info["StartupInfos"]

    def get_end_state(self):
        """get end state info"""
        self.end_state["StartupInfos"] = None

    def work(self):
        """worker"""

        self.check_params()
        self.get_proposed()
        self.startup_info = self.get_startup_dict()
        self.get_existing()
        if self.cfg_file:
            self.startup_next_cfg_file()
        if self.software_file:
            self.startup_next_software_file()
        if self.patch_file:
            self.startup_next_pat_file()
        if self.action == "display":
            self.startup_info = self.get_startup_dict()

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
    """ Module main """

    argument_spec = dict(
        cfg_file=dict(type='str'),
        software_file=dict(type='str'),
        patch_file=dict(type='str'),
        slot=dict(type='str'),
        action=dict(type='str', choices=['display'])
    )
    argument_spec.update(ce_argument_spec)
    module = StartUp(argument_spec=argument_spec)
    module.work()


if __name__ == '__main__':
    main()
