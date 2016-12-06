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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: nxos_gir_profile
version_added: "2.2"
short_description: Create a maintenance-mode or normal-mode profile for GIR.
description:
    - Manage a maintenance-mode or normal-mode profile with configuration
      commands that can be applied during graceful removal
      or graceful insertion.
extends_documentation_fragment: nxos
author:
    - Gabriele Gerbino (@GGabriele)
notes:
    - This module is not idempotent when C(state=present).
    - C(state=absent) removes the whole profile.
options:
    commands:
        description:
            - List of commands to be included into the profile.
        required: false
        default: null
    mode:
        description:
            - Configure the profile as Maintenance or Normal mode.
        required: true
        choices: ['maintenance', 'normal']
    state:
        description:
            - Specify desired state of the resource.
        required: false
        default: present
        choices: ['present','absent']
    include_defaults:
        description:
            - Specify to retrieve or not the complete running configuration
              for module operations.
        required: false
        default: false
        choices: ['true','false']
    config:
        description:
            - Specify the configuration string to be used for module operations.
        required: false
        default: null
'''

EXAMPLES = '''
# Create a maintenance-mode profile
- nxos_gir_profile:
    mode: maintenance
    commands:
      - router eigrp 11
      - isolate
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
# Remove the maintenance-mode profile
- nxos_gir_profile:
    mode: maintenance
    state: absent
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
'''

RETURN = '''
proposed:
    description: list of commands passed into module.
    returned: verbose mode
    type: list
    sample: ["router eigrp 11", "isolate"]
existing:
    description: list of existing profile commands.
    returned: verbose mode
    type: list
    sample: ["router bgp 65535","isolate","router eigrp 10","isolate",
            "diagnostic bootup level complete"]
end_state:
    description: list of profile entries after module execution.
    returned: verbose mode
    type: list
    sample: ["router bgp 65535","isolate","router eigrp 10","isolate",
            "diagnostic bootup level complete","router eigrp 11", "isolate"]
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["configure maintenance profile maintenance-mode",
             "router eigrp 11","isolate"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


# COMMON CODE FOR MIGRATION
import re

from ansible.module_utils.basic import get_exception
from ansible.module_utils.netcfg import NetworkConfig, ConfigLine
from ansible.module_utils.shell import ShellError

try:
    from ansible.module_utils.nxos import get_module
except ImportError:
    from ansible.module_utils.nxos import NetworkModule


def to_list(val):
     if isinstance(val, (list, tuple)):
         return list(val)
     elif val is not None:
         return [val]
     else:
         return list()


class CustomNetworkConfig(NetworkConfig):

    def expand_section(self, configobj, S=None):
        if S is None:
            S = list()
        S.append(configobj)
        for child in configobj.children:
            if child in S:
                continue
            self.expand_section(child, S)
        return S

    def get_object(self, path):
        for item in self.items:
            if item.text == path[-1]:
                parents = [p.text for p in item.parents]
                if parents == path[:-1]:
                    return item

    def to_block(self, section):
        return '\n'.join([item.raw for item in section])

    def get_section(self, path):
        try:
            section = self.get_section_objects(path)
            return self.to_block(section)
        except ValueError:
            return list()

    def get_section_objects(self, path):
        if not isinstance(path, list):
            path = [path]
        obj = self.get_object(path)
        if not obj:
            raise ValueError('path does not exist in config')
        return self.expand_section(obj)


    def add(self, lines, parents=None):
        """Adds one or lines of configuration
        """

        ancestors = list()
        offset = 0
        obj = None

        ## global config command
        if not parents:
            for line in to_list(lines):
                item = ConfigLine(line)
                item.raw = line
                if item not in self.items:
                    self.items.append(item)

        else:
            for index, p in enumerate(parents):
                try:
                    i = index + 1
                    obj = self.get_section_objects(parents[:i])[0]
                    ancestors.append(obj)

                except ValueError:
                    # add parent to config
                    offset = index * self.indent
                    obj = ConfigLine(p)
                    obj.raw = p.rjust(len(p) + offset)
                    if ancestors:
                        obj.parents = list(ancestors)
                        ancestors[-1].children.append(obj)
                    self.items.append(obj)
                    ancestors.append(obj)

            # add child objects
            for line in to_list(lines):
                # check if child already exists
                for child in ancestors[-1].children:
                    if child.text == line:
                        break
                else:
                    offset = len(parents) * self.indent
                    item = ConfigLine(line)
                    item.raw = line.rjust(len(line) + offset)
                    item.parents = ancestors
                    ancestors[-1].children.append(item)
                    self.items.append(item)


def get_network_module(**kwargs):
    try:
        return get_module(**kwargs)
    except NameError:
        return NetworkModule(**kwargs)

def get_config(module, include_defaults=False):
    config = module.params['config']
    if not config:
        try:
            config = module.get_config()
        except AttributeError:
            defaults = module.params['include_defaults']
            config = module.config.get_config(include_defaults=defaults)
    return CustomNetworkConfig(indent=2, contents=config)

def load_config(module, candidate):
    config = get_config(module)

    commands = candidate.difference(config)
    commands = [str(c).strip() for c in commands]

    save_config = module.params['save']

    result = dict(changed=False)

    if commands:
        if not module.check_mode:
            try:
                module.configure(commands)
            except AttributeError:
                module.config(commands)

            if save_config:
                try:
                    module.config.save_config()
                except AttributeError:
                    module.execute(['copy running-config startup-config'])

        result['changed'] = True
        result['updates'] = commands

    return result
# END OF COMMON CODE


def get_existing(module):
    existing = []
    netcfg = get_config(module)

    if module.params['mode'] == 'maintenance':
        parents = ['configure maintenance profile maintenance-mode']
    else:
        parents = ['configure maintenance profile normal-mode']

    config = netcfg.get_section(parents)
    if config:
        existing = config.splitlines()
        existing = [cmd.strip() for cmd in existing]
        existing.pop(0)

    return existing


def state_present(module, existing, commands):
    cmds = list()
    cmds.extend(commands)
    if module.params['mode'] == 'maintenance':
        cmds.insert(0, 'configure maintenance profile maintenance-mode')
    else:
        cmds.insert(0, 'configure maintenance profile normal-mode')

    return cmds


def state_absent(module, existing, commands):
    if module.params['mode'] == 'maintenance':
        cmds = ['no configure maintenance profile maintenance-mode']
    else:
        cmds = ['no configure maintenance profile normal-mode']
    return cmds


def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)


def execute_config_command(commands, module):
    try:
        module.configure(commands)
    except ShellError:
        clie = get_exception()
        module.fail_json(msg='Error sending CLI commands',
                         error=str(clie), commands=commands)
    except AttributeError:
        try:
            commands.insert(0, 'configure')
            module.cli.add_commands(commands, output='config')
            module.cli.run_commands()
        except ShellError:
            clie = get_exception()
            module.fail_json(msg='Error sending CLI commands',
                             error=str(clie), commands=commands)


def main():
    argument_spec = dict(
            commands=dict(required=False, type='list'),
            mode=dict(required=True, choices=['maintenance', 'normal']),
            state=dict(choices=['absent', 'present'],
                       default='present'),
            include_defaults=dict(default=False),
            config=dict()
    )
    module = get_network_module(argument_spec=argument_spec,
                                supports_check_mode=True)

    state = module.params['state']
    commands = module.params['commands'] or []

    if state == 'absent' and commands:
        module.fail_json(msg='when state is absent, no command can be used.')

    existing = invoke('get_existing', module)
    end_state = existing
    changed = False

    result = {}
    cmds = []
    if state == 'present' or (state == 'absent' and existing):
        cmds = invoke('state_%s' % state, module, existing, commands)

        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            execute_config_command(cmds, module)
            changed = True
            end_state = invoke('get_existing', module)

    result['connected'] = module.connected
    result['changed'] = changed
    if module._verbosity > 0:
        end_state = invoke('get_existing', module)
        result['end_state'] = end_state
        result['existing'] = existing
        result['proposed'] = commands
        result['updates'] = cmds

    module.exit_json(**result)


if __name__ == '__main__':
    main()
