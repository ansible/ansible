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
module: nxos_ospf
version_added: "2.2"
short_description: Manages configuration of an ospf instance.
description:
    - Manages configuration of an ospf instance.
author: Gabriele Gerbino (@GGabriele)
extends_documentation_fragment: nxos
options:
    ospf:
        description:
            - Name of the ospf instance.
        required: true
    state:
        description:
            - Determines whether the config should be present or not
              on the device.
        required: false
        default: present
        choices: ['present','absent']
'''

EXAMPLES = '''
- nxos_ospf:
    ospf: 1
    state: present
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"ospf": "1"}
existing:
    description: k/v pairs of existing configuration
    returned: verbose mode
    type: dict
    sample: {"ospf": ["2"]}
end_state:
    description: k/v pairs of configuration after module execution
    returned: verbose mode
    type: dict
    sample: {"ospf": ["1", "2"]}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["router ospf 1"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''


# COMMON CODE FOR MIGRATION
import re

import ansible.module_utils.nxos
from ansible.module_utils.basic import get_exception
from ansible.module_utils.netcfg import NetworkConfig, ConfigLine
from ansible.module_utils.network import NetworkModule
from ansible.module_utils.shell import ShellError


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

PARAM_TO_COMMAND_KEYMAP = {
    'ospf': 'router ospf'
}


def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)


def get_value(config, module):
    splitted_config = config.splitlines()
    value_list = []
    REGEX = '^router ospf\s(?P<ospf>\S+).*'
    for line in splitted_config:
        value = ''
        if 'router ospf' in line:
            try:
                match_ospf = re.match(REGEX, line, re.DOTALL)
                ospf_group = match_ospf.groupdict()
                value = ospf_group['ospf']
            except AttributeError:
                value = ''
            if value:
                value_list.append(value)

    return value_list


def get_existing(module):
    existing = {}
    config = str(get_config(module))

    value = get_value(config, module)
    if value:
        existing['ospf'] = value
    return existing


def apply_key_map(key_map, table):
    new_dict = {}
    for key, value in table.items():
        new_key = key_map.get(key)
        if new_key:
            value = table.get(key)
            if value:
                new_dict[new_key] = value
            else:
                new_dict[new_key] = value
    return new_dict


def state_present(module, proposed, candidate):
    commands = ['router ospf {0}'.format(proposed['ospf'])]
    candidate.add(commands, parents=[])


def state_absent(module, proposed, candidate):
    commands = ['no router ospf {0}'.format(proposed['ospf'])]
    candidate.add(commands, parents=[])


def main():
    argument_spec = dict(
            ospf=dict(required=True, type='str'),
            state=dict(choices=['present', 'absent'], default='present',
                       required=False),
            include_defaults=dict(default=True),
            config=dict(),
            save=dict(type='bool', default=False)
    )
    module = get_network_module(argument_spec=argument_spec,
                        supports_check_mode=True)

    state = module.params['state']
    ospf = str(module.params['ospf'])

    existing = invoke('get_existing', module)
    end_state = existing
    proposed = dict(ospf=ospf)

    if not existing:
        existing_list = []
    else:
        existing_list = existing['ospf']

    result = {}
    if (state == 'present' or (state == 'absent' and ospf in existing_list)):
        candidate = CustomNetworkConfig(indent=3)
        invoke('state_%s' % state, module, proposed, candidate)

        try:
            response = load_config(module, candidate)
            result.update(response)
        except ShellError:
            exc = get_exception()
            module.fail_json(msg=str(exc))
    else:
        result['updates'] = []

    result['connected'] = module.connected
    if module._verbosity > 0:
        end_state = invoke('get_existing', module)
        result['end_state'] = end_state
        result['existing'] = existing
        result['proposed'] = proposed

    module.exit_json(**result)


if __name__ == '__main__':
    main()
