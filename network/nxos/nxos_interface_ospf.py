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

DOCUMENTATION = '''
---
module: nxos_interface_ospf
version_added: "2.2"
short_description: Manages configuration of an OSPF interface instance.
description:
    - Manages configuration of an OSPF interface instance.
author: Gabriele Gerbino (@GGabriele)
extends_documentation_fragment: nxos
notes:
    - Default, where supported, restores params default value.
    - To remove an existing authentication configuration you should use
      C(message_digest_key_id=default) plus all other options matching their
      existing values.
    - C(state=absent) removes the whole OSPF interface configuration.
options:
    interface:
        description:
            - Name of this cisco_interface resource. Valid value is a string.
        required: true
    ospf:
        description:
            - Name of the ospf instance.
        required: true
    area:
        description:
            - Ospf area associated with this cisco_interface_ospf instance.
              Valid values are a string, formatted as an IP address
              (i.e. "0.0.0.0") or as an integer.
        required: true
    cost:
        description:
            - The cost associated with this cisco_interface_ospf instance.
        required: false
        default: null
    hello_interval:
        description:
            - Time between sending successive hello packets.
              Valid values are an integer or the keyword 'default'.
        required: false
        default: null
    dead_interval:
        description:
            - Time interval an ospf neighbor waits for a hello
              packet before tearing down adjacencies. Valid values are an
              integer or the keyword 'default'.
        required: false
        default: null
    passive_interface:
        description:
            - Setting to true will prevent this interface from receiving
              HELLO packets. Valid values are 'true' and 'false'.
        required: false
        choices: ['true','false']
        default: null
    message_digest:
        description:
            - Enables or disables the usage of message digest authentication.
              Valid values are 'true' and 'false'.
        required: false
        choices: ['true','false']
        default: null
    message_digest_key_id:
        description:
            - Md5 authentication key-id associated with the ospf instance.
              If this is present, message_digest_encryption_type,
              message_digest_algorithm_type and message_digest_password are
              mandatory. Valid value is an integer and 'default'.
        required: false
        default: null
    message_digest_algorithm_type:
        description:
            - Algorithm used for authentication among neighboring routers
              within an area. Valid values is 'md5'.
        required: false
        choices: ['md5']
        default: null
    message_digest_encryption_type:
        description:
            - Specifies the scheme used for encrypting message_digest_password.
              Valid values are '3des' or 'cisco_type_7' encryption.
        required: false
        choices: ['cisco_type_7','3des']
        default: null
    message_digest_password:
        description:
            - Specifies the message_digest password. Valid value is a string.
        required: false
        default: null
    state:
        description:
            - Determines whether the config should be present or not
              on the device.
        required: false
        default: present
        choices: ['present','absent']
'''
EXAMPLES = '''
- nxos_interface_ospf:
    interface: ethernet1/32
    ospf: 1
    area: 1
    cost=default
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: verbose mode
    type: dict
    sample: {"area": "1", "interface": "ethernet1/32", "ospf": "1"}
existing:
    description: k/v pairs of existing OSPF configuration
    returned: verbose mode
    type: dict
    sample: {"area": "", "cost": "", "dead_interval": "",
            "hello_interval": "", "interface": "ethernet1/32",
            "message_digest": false, "message_digest_algorithm_type": "",
            "message_digest_encryption_type": "",
            "message_digest_key_id": "", "message_digest_password": "",
            "ospf": "", "passive_interface": false}
end_state:
    description: k/v pairs of OSPF configuration after module execution
    returned: verbose mode
    type: dict
    sample: {"area": "0.0.0.1", "cost": "", "dead_interval": "",
            "hello_interval": "", "interface": "ethernet1/32",
            "message_digest": false, "message_digest_algorithm_type": "",
            "message_digest_encryption_type": "", "message_digest_key_id": "",
            "message_digest_password": "", "ospf": "1",
            "passive_interface": false}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["interface Ethernet1/32", "ip router ospf 1 area 0.0.0.1"]
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

BOOL_PARAMS = [
    'passive_interface',
    'message_digest'
]
PARAM_TO_COMMAND_KEYMAP = {
    'cost': 'ip ospf cost',
    'ospf': 'ip router ospf',
    'area': 'ip router ospf',
    'hello_interval': 'ip ospf hello-interval',
    'dead_interval': 'ip ospf dead-interval',
    'passive_interface': 'ip ospf passive-interface',
    'message_digest': 'ip ospf authentication message-digest',
    'message_digest_key_id': 'ip ospf message-digest-key',
    'message_digest_algorithm_type': 'ip ospf message-digest-key options',
    'message_digest_encryption_type': 'ip ospf message-digest-key options',
    'message_digest_password': 'ip ospf message-digest-key options',
}
PARAM_TO_DEFAULT_KEYMAP = {
}


def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)


def get_custom_value(arg, config, module):
    value = ''
    if arg == 'ospf':
        REGEX = re.compile(r'(?:ip router ospf\s)(?P<value>.*)$', re.M)
        value = ''
        if 'ip router ospf' in config:
            parsed = REGEX.search(config).group('value').split()
            value = parsed[0]

    elif arg == 'area':
        REGEX = re.compile(r'(?:ip router ospf\s)(?P<value>.*)$', re.M)
        value = ''
        if 'ip router ospf' in config:
            parsed = REGEX.search(config).group('value').split()
            value = parsed[2]

    elif arg.startswith('message_digest_'):
        REGEX = re.compile(r'(?:ip ospf message-digest-key\s)(?P<value>.*)$', re.M)
        value = ''
        if 'ip ospf message-digest-key' in config:
            value_list = REGEX.search(config).group('value').split()
            if arg == 'message_digest_key_id':
                value = value_list[0]
            elif arg == 'message_digest_algorithm_type':
                value = value_list[1]
            elif arg == 'message_digest_encryption_type':
                value = value_list[2]
                if value == '3':
                    value = '3des'
                elif value == '7':
                    value = 'cisco_type_7'
            elif arg == 'message_digest_password':
                value = value_list[3]

    elif arg == 'passive_interface':
        REGEX = re.compile(r'\s+{0}\s*$'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
        NO_REGEX = re.compile(r'\s+no\s+{0}\s*$'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
        value = False
        try:
            if NO_REGEX.search(config):
                value = False
            elif REGEX.search(config):
                value = True
        except TypeError:
            value = False

    return value


def get_value(arg, config, module):
    custom = [
        'ospf',
        'area',
        'message_digest_key_id',
        'message_digest_algorithm_type',
        'message_digest_encryption_type',
        'message_digest_password',
        'passive_interface'
    ]

    if arg in custom:
        value = get_custom_value(arg, config, module)
    elif arg in BOOL_PARAMS:
        REGEX = re.compile(r'\s+{0}\s*$'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
        value = False
        try:
            if REGEX.search(config):
                value = True
        except TypeError:
            value = False
    else:
        REGEX = re.compile(r'(?:{0}\s)(?P<value>.*)$'.format(PARAM_TO_COMMAND_KEYMAP[arg]), re.M)
        value = ''
        if PARAM_TO_COMMAND_KEYMAP[arg] in config:
            value = REGEX.search(config).group('value')
    return value


def get_existing(module, args):
    existing = {}
    netcfg = get_config(module)
    parents = ['interface {0}'.format(module.params['interface'].capitalize())]
    config = netcfg.get_section(parents)
    if 'ospf' in config:
        for arg in args:
            if arg not in ['interface']:
                existing[arg] = get_value(arg, config, module)
        existing['interface'] = module.params['interface']
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


def get_default_commands(existing, proposed, existing_commands, key, module):
    commands = list()
    existing_value = existing_commands.get(key)
    if key.startswith('ip ospf message-digest-key'):
        check = False
        for param in ['message_digest_encryption_type',
                      'message_digest_algorithm_type',
                      'message_digest_password']:
            if existing[param] == proposed[param]:
                check = True
        if check:
            if existing['message_digest_encryption_type'] == '3des':
                encryption_type = '3'
            elif existing['message_digest_encryption_type'] == 'cisco_type_7':
                encryption_type = '7'
            command = 'no {0} {1} {2} {3} {4}'.format(
                        key,
                        existing['message_digest_key_id'],
                        existing['message_digest_algorithm_type'],
                        encryption_type,
                        existing['message_digest_password'])
            commands.append(command)
    else:
        commands.append('no {0} {1}'.format(key, existing_value))
    return commands


def get_custom_command(existing_cmd, proposed, key, module):
    commands = list()

    if key == 'ip router ospf':
        command = '{0} {1} area {2}'.format(key, proposed['ospf'],
                                            proposed['area'])
        if command not in existing_cmd:
            commands.append(command)

    elif key.startswith('ip ospf message-digest-key'):
        if (proposed['message_digest_key_id'] != 'default' and
            'options' not in key):
            if proposed['message_digest_encryption_type'] == '3des':
                encryption_type = '3'
            elif proposed['message_digest_encryption_type'] == 'cisco_type_7':
                encryption_type = '7'
            command = '{0} {1} {2} {3} {4}'.format(
                                key,
                                proposed['message_digest_key_id'],
                                proposed['message_digest_algorithm_type'],
                                encryption_type,
                                proposed['message_digest_password'])
            commands.append(command)
    return commands


def state_present(module, existing, proposed, candidate):
    commands = list()
    proposed_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, proposed)
    existing_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, existing)

    for key, value in proposed_commands.iteritems():
        if value is True:
            commands.append(key)
        elif value is False:
            commands.append('no {0}'.format(key))
        elif value == 'default':
            if existing_commands.get(key):
                commands.extend(get_default_commands(existing, proposed,
                                                     existing_commands, key,
                                                     module))
        else:
            if (key == 'ip router ospf' or
                    key.startswith('ip ospf message-digest-key')):
                commands.extend(get_custom_command(commands, proposed,
                                                   key, module))
            else:
                command = '{0} {1}'.format(key, value.lower())
                commands.append(command)

    if commands:
        parents = ['interface {0}'.format(module.params['interface'].capitalize())]
        candidate.add(commands, parents=parents)


def state_absent(module, existing, proposed, candidate):
    commands = []
    parents = ['interface {0}'.format(module.params['interface'].capitalize())]
    existing_commands = apply_key_map(PARAM_TO_COMMAND_KEYMAP, existing)

    for key, value in existing_commands.iteritems():
        if value:
            if key.startswith('ip ospf message-digest-key'):
                if 'options' not in key:
                    if existing['message_digest_encryption_type'] == '3des':
                        encryption_type = '3'
                    elif existing['message_digest_encryption_type'] == 'cisco_type_7':
                        encryption_type = '7'
                    command = 'no {0} {1} {2} {3} {4}'.format(
                                        key,
                                        existing['message_digest_key_id'],
                                        existing['message_digest_algorithm_type'],
                                        encryption_type,
                                        existing['message_digest_password'])
                    commands.append(command)
            elif key in ['ip ospf authentication message-digest',
                         'ip ospf passive-interface']:
                if value:
                    commands.append('no {0}'.format(key))
            elif key == 'ip router ospf':
                command = 'no {0} {1} area {2}'.format(key, proposed['ospf'],
                                                    proposed['area'])
                if command not in commands:
                    commands.append(command)
            else:
                existing_value = existing_commands.get(key)
                commands.append('no {0} {1}'.format(key, existing_value))

    candidate.add(commands, parents=parents)


def normalize_area(area, module):
    try:
        area = int(area)
        area = '0.0.0.{0}'.format(area)
    except ValueError:
        splitted_area = area.split('.')
        if len(splitted_area) != 4:
            module.fail_json(msg='Incorrect Area ID format', area=area)
    return area


def main():
    argument_spec = dict(
            interface=dict(required=True, type='str'),
            ospf=dict(required=True, type='str'),
            area=dict(required=True, type='str'),
            cost=dict(required=False, type='str'),
            hello_interval=dict(required=False, type='str'),
            dead_interval=dict(required=False, type='str'),
            passive_interface=dict(required=False, type='bool'),
            message_digest=dict(required=False, type='bool'),
            message_digest_key_id=dict(required=False, type='str'),
            message_digest_algorithm_type=dict(required=False, type='str',
                                               choices=['md5']),
            message_digest_encryption_type=dict(required=False, type='str',
                                                choices=['cisco_type_7','3des']),
            message_digest_password=dict(required=False, type='str'),
            state=dict(choices=['present', 'absent'], default='present',
                       required=False),
            include_defaults=dict(default=True),
            config=dict(),
            save=dict(type='bool', default=False)
    )
    module = get_network_module(argument_spec=argument_spec,
                                required_together=[['message_digest_key_id',
                                                    'message_digest_algorithm_type',
                                                    'message_digest_encryption_type',
                                                    'message_digest_password']],
                                supports_check_mode=True)

    for param in ['message_digest_encryption_type',
                  'message_digest_algorithm_type',
                  'message_digest_password']:
        if module.params[param] == 'default':
            module.exit_json(msg='Use message_digest_key_id=default to remove'
                                 ' an existing authentication configuration')

    state = module.params['state']
    args =  [
            'interface',
            'ospf',
            'area',
            'cost',
            'hello_interval',
            'dead_interval',
            'passive_interface',
            'message_digest',
            'message_digest_key_id',
            'message_digest_algorithm_type',
            'message_digest_encryption_type',
            'message_digest_password'
        ]

    existing = invoke('get_existing', module, args)
    end_state = existing
    proposed_args = dict((k, v) for k, v in module.params.iteritems()
                    if v is not None and k in args)

    proposed = {}
    for key, value in proposed_args.iteritems():
        if key != 'interface':
            if str(value).lower() == 'true':
                value = True
            elif str(value).lower() == 'false':
                value = False
            elif str(value).lower() == 'default':
                value = PARAM_TO_DEFAULT_KEYMAP.get(key)
                if value is None:
                    value = 'default'
            if existing.get(key) or (not existing.get(key) and value):
                proposed[key] = value

    proposed['area'] = normalize_area(proposed['area'], module)
    result = {}
    if (state == 'present' or (state == 'absent' and
        existing.get('ospf') == proposed['ospf'] and
        existing.get('area') == proposed['area'])):

        candidate = CustomNetworkConfig(indent=3)
        invoke('state_%s' % state, module, existing, proposed, candidate)

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
        end_state = invoke('get_existing', module, args)
        result['end_state'] = end_state
        result['existing'] = existing
        result['proposed'] = proposed_args

    module.exit_json(**result)


if __name__ == '__main__':
    main()
