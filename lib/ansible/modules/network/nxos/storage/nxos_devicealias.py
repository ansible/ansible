#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = '''
module: nxos_devicealias
version_added: "2.10"
short_description: Configuration of device alias.
description:
    - Configuration of device alias for Cisco MDS NXOS.
author:
    - Suhas Bharadwaj (@srbharadwaj) (subharad@cisco.com)
notes:
  - Tested against NX-OS 8.4(1)
options:
    distribute:
        description:
            - Enable/Disable device-alias distribution
        type: bool
        default: False
    mode:
        description:
            - Mode of devices-alias, basic or enhanced
        choices: ['basic', 'enhanced']
        type: str
    da:
        description:
            - List of device-alias to be added or removed
        type: list
        suboptions:
            name:
                description:
                    - Name of the device-alias to be added or removed
                required:
                    True
                type: str
            pwwn:
                description:
                    - pwwn to which the name needs to be associated with
                type: str
            remove:
                description:
                    - Removes the device-alias if set to True
                type: bool
                default: False
    rename:
        description:
            - List of device-alias to be renamed
        type: list
        suboptions:
            old_name:
                description:
                    - Old name of the device-alias that needs to be renamed
                required:
                    True
                type: str
            new_name:
                description:
                    - New name of the device-alias
                required:
                    True
                type: str
'''

EXAMPLES = '''
---
- name: 'Test that device alias module works'
  nxos_devicealias:
    da:
      - name: test1_add
        pwwn: '56:2:22:11:22:88:11:67'
      - name: test2_add
        pwwn: '65:22:22:11:22:22:11:d'
      - name: dev1
        remove: true
      - name: dev2
        remove: true
    distribute: true
    mode: enhanced
    rename:
      - new_name: bcd
        old_name: abc
      - new_name: bcd1
        old_name: abc1


'''

RETURN = '''
commands:
  description: commands sent to the device
  returned: always
  type: list
  sample:
    - terminal dont-ask
    - device-alias database
    - device-alias name somename pwwn 10:00:00:00:89:a1:01:03
    - device-alias name somename1 pwwn 10:00:00:00:89:a1:02:03
    - device-alias commit
    - no terminal dont-ask
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.nxos.nxos import load_config, run_commands
import string

__metaclass__ = type


class showDeviceAliasStatus(object):
    """docstring for showDeviceAliasStatus"""

    def __init__(self, module):
        self.module = module
        self.distribute = ""
        self.mode = ""
        self.locked = False
        self.update()

    def execute_show_cmd(self, cmd):
        output = execute_show_command(cmd, self.module)[0]
        return output

    def update(self):
        command = 'show device-alias status'
        output = self.execute_show_cmd(command).split("\n")
        for o in output:
            if "Fabric Distribution" in o:
                self.distribute = o.split(":")[1].strip().lower()
            if "Mode" in o:
                self.mode = o.split("Mode:")[1].strip().lower()
            if "Locked" in o:
                self.locked = True

    def isLocked(self):
        return self.locked

    def getDistribute(self):
        return self.distribute

    def getMode(self):
        return self.mode


class showDeviceAliasDatabase(object):
    """docstring for showDeviceAliasDatabase"""

    def __init__(self, module):
        self.module = module
        self.da_dict = {}
        self.update()

    def execute_show_cmd(self, cmd):
        output = execute_show_command(cmd, self.module)[0]
        return output

    def update(self):
        command = 'show device-alias database'
        # output = execute_show_command(command, self.module)[0].split("\n")
        output = self.execute_show_cmd(command)
        self.da_list = output.split("\n")
        for eachline in self.da_list:
            if 'device-alias' in eachline:
                sv = eachline.strip().split()
                self.da_dict[sv[2]] = sv[4]

    def isNameInDaDatabase(self, name):
        return name in self.da_dict.keys()

    def isPwwnInDaDatabase(self, pwwn):
        newpwwn = ':'.join(["0" + str(ep) if len(ep) == 1 else ep for ep in pwwn.split(":")])
        return newpwwn in self.da_dict.values()

    def isNamePwwnPresentInDatabase(self, name, pwwn):
        newpwwn = ':'.join(["0" + str(ep) if len(ep) == 1 else ep for ep in pwwn.split(":")])
        if name in self.da_dict.keys():
            if newpwwn == self.da_dict[name]:
                return True
        return False

    def getPwwnByName(self, name):
        if name in self.da_dict.keys():
            return self.da_dict[name]
        else:
            return None

    def getNameByPwwn(self, pwwn):
        newpwwn = ':'.join(["0" + str(ep) if len(ep) == 1 else ep for ep in pwwn.split(":")])
        for n, p in self.da_dict.items():
            if p == newpwwn:
                return n
        return None


def isPwwnValid(pwwn):
    pwwnsplit = pwwn.split(":")
    if len(pwwnsplit) != 8:
        return False
    for eachpwwnsplit in pwwnsplit:
        if len(eachpwwnsplit) > 2 or len(eachpwwnsplit) < 1:
            return False
        if not all(c in string.hexdigits for c in eachpwwnsplit):
            return False
    return True


def isNameValid(name):
    if not name[0].isalpha():
        # Illegal first character. Name must start with a letter
        return False
    if len(name) > 64:
        return False
    return True


def execute_show_command(command, module, command_type='cli_show'):
    output = 'text'
    commands = [{
        'command': command,
        'output': output,
    }]
    out = run_commands(module, commands)
    return out


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def main():
    element_spec = dict(
        name=dict(required=True, type='str'),
        pwwn=dict(type='str'),
        remove=dict(type='bool', default=False)
    )

    element_spec_rename = dict(
        old_name=dict(required=True, type='str'),
        new_name=dict(required=True, type='str'),
    )

    argument_spec = dict(
        distribute=dict(type='bool'),
        mode=dict(type='str', choices=['enhanced', 'basic']),
        da=dict(type='list', elements='dict', options=element_spec),
        rename=dict(type='list', elements='dict', options=element_spec_rename)
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    warnings = list()
    messages = list()
    commands_to_execute = list()
    result = {'changed': False}

    distribute = module.params['distribute']
    mode = module.params['mode']
    da = module.params['da']
    rename = module.params['rename']

    # Step 0.0: Validate syntax of name and pwwn
    #       Also validate syntax of rename arguments
    if da is not None:
        for eachdict in da:
            name = eachdict['name']
            pwwn = eachdict['pwwn']
            remove = eachdict['remove']
            if pwwn is not None:
                pwwn = pwwn.lower()
            if not remove:
                if pwwn is None:
                    module.fail_json(
                        msg='This device alias name ' +
                        str(name) +
                        ' which needs to be added, doenst have pwwn specified . Please specify a valid pwwn')
                if not isNameValid(name):
                    module.fail_json(msg='This pwwn name is invalid : ' + str(name) +
                                     '. Note that name cannot be more than 64 chars and it should start with a letter')
                if not isPwwnValid(pwwn):
                    module.fail_json(msg='This pwwn is invalid : ' + str(pwwn) + '. Please check that its a valid pwwn')
    if rename is not None:
        for eachdict in rename:
            oldname = eachdict['old_name']
            newname = eachdict['new_name']
            if not isNameValid(oldname):
                module.fail_json(msg='This pwwn name is invalid : ' + str(oldname) +
                                 '. Note that name cannot be more than 64 chars and it should start with a letter')
            if not isNameValid(newname):
                module.fail_json(msg='This pwwn name is invalid : ' + str(newname) +
                                 '. Note that name cannot be more than 64 chars and it should start with a letter')

    # Step 0.1: Check DA status
    shDAStausObj = showDeviceAliasStatus(module)
    d = shDAStausObj.getDistribute()
    m = shDAStausObj.getMode()
    if shDAStausObj.isLocked():
        module.fail_json(msg='device-alias has acquired lock on the switch. Hence cannot procced.')

    # Step 1: Process distribute
    commands = []
    if distribute is not None:
        if distribute:
            # playbook has distribute as True(enabled)
            if d == "disabled":
                # but switch distribute is disabled(false), so set it to true(enabled)
                commands.append("device-alias distribute")
                messages.append('device-alias distribute changed from disabled to enabled')
            else:
                messages.append('device-alias distribute remains unchanged. current distribution mode is enabled')
        else:
            # playbook has distribute as False(disabled)
            if d == "enabled":
                # but switch distribute is enabled(true), so set it to false(disabled)
                commands.append("no device-alias distribute")
                messages.append('device-alias distribute changed from enabled to disabled')
            else:
                messages.append('device-alias distribute remains unchanged. current distribution mode is disabled')

    cmds = flatten_list(commands)
    if cmds:
        commands_to_execute = commands_to_execute + cmds
        if module.check_mode:
            # Check mode implemented at the da_add/da_remove stage
            pass
        else:
            result['changed'] = True
            load_config(module, cmds)

    # Step 2: Process mode
    commands = []
    if mode is not None:
        if mode == 'basic':
            # playbook has mode as basic
            if m == 'enhanced':
                # but switch mode is enhanced, so set it to basic
                commands.append("no device-alias mode enhanced")
                messages.append('device-alias mode changed from enhanced to basic')
            else:
                messages.append('device-alias mode remains unchanged. current mode is basic')

        else:
            # playbook has mode as enhanced
            if m == 'basic':
                # but switch mode is basic, so set it to enhanced
                commands.append("device-alias mode enhanced")
                messages.append('device-alias mode changed from basic to enhanced')
            else:
                messages.append('device-alias mode remains unchanged. current mode is enhanced')

    if commands:
        if distribute:
            commands.append("device-alias commit")
            commands = ["terminal dont-ask"] + commands + ["no terminal dont-ask"]
        else:
            if distribute is None and d == 'enabled':
                commands.append("device-alias commit")
                commands = ["terminal dont-ask"] + commands + ["no terminal dont-ask"]

    cmds = flatten_list(commands)

    if cmds:
        commands_to_execute = commands_to_execute + cmds
        if module.check_mode:
            # Check mode implemented at the end
            pass
        else:
            result['changed'] = True
            load_config(module, cmds)

    # Step 3: Process da
    commands = []
    shDADatabaseObj = showDeviceAliasDatabase(module)
    if da is not None:
        da_remove_list = []
        da_add_list = []
        for eachdict in da:
            name = eachdict['name']
            pwwn = eachdict['pwwn']
            remove = eachdict['remove']
            if pwwn is not None:
                pwwn = pwwn.lower()
            if remove:
                if shDADatabaseObj.isNameInDaDatabase(name):
                    commands.append("no device-alias name " + name)
                    da_remove_list.append(name)
                else:
                    messages.append(name + ' - This device alias name is not in switch device-alias database, hence cannot be removed.')
            else:
                if shDADatabaseObj.isNamePwwnPresentInDatabase(name, pwwn):
                    messages.append(name + ' : ' + pwwn + ' - This device alias name,pwwn is already in switch device-alias database, \
                        hence nothing to configure')
                else:
                    if shDADatabaseObj.isNameInDaDatabase(name):
                        module.fail_json(
                            msg=name +
                            ' - This device alias name is already present in switch device-alias database but assigned to another pwwn (' +
                            shDADatabaseObj.getPwwnByName(name) +
                            ') hence cannot be added')

                    elif shDADatabaseObj.isPwwnInDaDatabase(pwwn):
                        module.fail_json(
                            msg=pwwn +
                            ' - This device alias pwwn is already present in switch device-alias database but assigned to another name (' +
                            shDADatabaseObj.getNameByPwwn(pwwn) +
                            ') hence cannot be added')

                    else:
                        commands.append("device-alias name " + name + " pwwn " + pwwn)
                        da_add_list.append(name)

        if len(da_add_list) != 0 or len(da_remove_list) != 0:
            commands = ["device-alias database"] + commands
            if distribute:
                commands.append("device-alias commit")
                commands = ["terminal dont-ask"] + commands + ["no terminal dont-ask"]
            else:
                if distribute is None and d == 'enabled':
                    commands.append("device-alias commit")
                    commands = ["terminal dont-ask"] + commands + ["no terminal dont-ask"]

        cmds = flatten_list(commands)
        if cmds:
            commands_to_execute = commands_to_execute + cmds
            if module.check_mode:
                # Check mode implemented at the end
                pass
            else:
                result['changed'] = True
                load_config(module, cmds)
                if len(da_remove_list) != 0:
                    messages.append('the required device-alias were removed. ' + ','.join(da_remove_list))
                if len(da_add_list) != 0:
                    messages.append('the required device-alias were added. ' + ','.join(da_add_list))

    # Step 5: Process rename
    commands = []
    if rename is not None:
        for eachdict in rename:
            oldname = eachdict['old_name']
            newname = eachdict['new_name']
            if shDADatabaseObj.isNameInDaDatabase(newname):
                module.fail_json(
                    changed=False,
                    commands=cmds,
                    msg=newname +
                    " - this name is already present in the device-alias database, hence we cannot rename " +
                    oldname +
                    " with this one")
            if shDADatabaseObj.isNameInDaDatabase(oldname):
                commands.append('device-alias rename ' + oldname + ' ' + newname)
            else:
                module.fail_json(changed=False, commands=cmds, msg=oldname +
                                 " - this name is not present in the device-alias database, hence we cannot rename.")

        if len(commands) != 0:
            commands = ["device-alias database"] + commands
            if distribute:
                commands.append("device-alias commit")
                commands = ["terminal dont-ask"] + commands + ["no terminal dont-ask"]
            else:
                if distribute is None and d == 'enabled':
                    commands.append("device-alias commit")
                    commands = ["terminal dont-ask"] + commands + ["no terminal dont-ask"]
        cmds = flatten_list(commands)
        if cmds:
            commands_to_execute = commands_to_execute + cmds
            if module.check_mode:
                # Check mode implemented at the end
                pass
            else:
                result['changed'] = True
                load_config(module, cmds)

    # Step END: check for 'check' mode
    if module.check_mode:
        module.exit_json(changed=False, commands=commands_to_execute, msg="Check Mode: No cmds issued to the hosts")

    result['messages'] = messages
    result['commands'] = commands_to_execute
    result['warnings'] = warnings
    module.exit_json(**result)


if __name__ == '__main__':
    main()
