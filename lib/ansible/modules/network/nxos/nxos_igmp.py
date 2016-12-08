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
module: nxos_igmp
version_added: "2.2"
short_description: Manages IGMP global configuration.
description:
    - Manages IGMP global configuration configuration settings.
extends_documentation_fragment: nxos
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
notes:
    - When C(state=default), all supported params will be reset to a
      default state.
    - If restart is set to true with other params set, the restart will happen
      last, i.e. after the configuration takes place.
options:
    flush_routes:
        description:
            - Removes routes when the IGMP process is restarted. By default,
              routes are not flushed.
        required: false
        default: null
        choices: ['true', 'false']
    enforce_rtr_alert:
        description:
            - Enables or disables the enforce router alert option check for
              IGMPv2 and IGMPv3 packets.
        required: false
        default: null
        choices: ['true', 'false']
    restart:
        description:
            - Restarts the igmp process (using an exec config command).
        required: false
        default: null
        choices: ['true', 'false']
    state:
        description:
            - Manages desired state of the resource.
        required: false
        default: present
        choices: ['present', 'default']
'''
EXAMPLES = '''
- name: Default igmp global params (all params except restart)
  nxos_igmp:
    state: default
    host: "{{ inventory_hostname }}"

- name: Ensure the following igmp global config exists on the device
  nxos_igmp:
    flush_routes: true
    enforce_rtr_alert: true
    host: "{{ inventory_hostname }}"

- name: Restart the igmp process
  nxos_igmp:
    restart: true
    host: "{{ inventory_hostname }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"enforce_rtr_alert": true, "flush_routes": true}
existing:
    description: k/v pairs of existing IGMP configuration
    returned: verbose mode
    type: dict
    sample: {"enforce_rtr_alert": true, "flush_routes": false}
end_state:
    description: k/v pairs of IGMP configuration after module execution
    returned: verbose mode
    type: dict
    sample: {"enforce_rtr_alert": true, "flush_routes": true}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["ip igmp flush-routes"]
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

PARAM_TO_COMMAND_KEYMAP = {
    'flush_routes': 'ip igmp flush-routes',
    'enforce_rtr_alert': 'ip igmp enforce-router-alert'
}


def get_value(arg, config):
    REGEX = re.compile(r'{0}\s*$'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
    value = False
    try:
        if REGEX.search(config):
            value = True
    except TypeError:
        value = False
    return value


def get_existing(module, args):
    existing = {}
    config = str(get_config(module))

    for arg in args:
        existing[arg] = get_value(arg, config)
    return existing


def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)


def get_commands(module, existing, proposed, candidate):
    commands = list()
    proposed_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, proposed)
    existing_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, existing)
    if module.params['state'] == 'default':
        for key, value in proposed_commands.iteritems():
            if existing_commands.get(key):
                commands.append('no {0}'.format(key))
    else:
        for key, value in proposed_commands.iteritems():
            if value is True:
                commands.append(key)
            else:
                if existing_commands.get(key):
                    commands.append('no {0}'.format(key))

    if module.params['restart']:
        commands.append('restart igmp')

    if commands:
        parents = []
        candidate.add(commands, parents=parents)


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


def main():
    argument_spec = dict(
            flush_routes=dict(type='bool'),
            enforce_rtr_alert=dict(type='bool'),
            restart=dict(type='bool', default=False),
            state=dict(choices=['present', 'default'], default='present'),
            include_defaults=dict(default=False),
            config=dict(),
            save=dict(type='bool', default=False)
    )
    module = get_network_module(argument_spec=argument_spec,
                        supports_check_mode=True)

    state = module.params['state']
    restart = module.params['restart']

    if (state == 'default' and (module.params['flush_routes'] is not None or
            module.params['enforce_rtr_alert'] is not None)):
        module.fail_json(msg='When state=default other params have no effect.')

    args =  [
            "flush_routes",
            "enforce_rtr_alert",
        ]

    existing = invoke('get_existing', module, args)
    end_state = existing

    proposed = dict((k, v) for k, v in module.params.iteritems()
                if v is not None and k in args)

    proposed_args = proposed.copy()
    if state == 'default':
        proposed_args = dict((k, False) for k in args)

    result = {}
    if (state == 'present' or (state == 'default' and
            True in existing.values()) or restart):
        candidate = CustomNetworkConfig(indent=3)
        invoke('get_commands', module, existing, proposed_args, candidate)

        try:
            response = load_config(module, candidate)
            result.update(response)
        except ShellError:
            exc = get_exception()
            module.fail_json(msg=str(exc))
    else:
        result['updates'] = []

    if restart:
        proposed['restart'] = restart
    result['connected'] = module.connected
    if module._verbosity > 0:
        end_state = invoke('get_existing', module, args)
        result['end_state'] = end_state
        result['existing'] = existing
        result['proposed'] = proposed

    module.exit_json(**result)


if __name__ == '__main__':
    main()
