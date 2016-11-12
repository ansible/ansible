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
module: nxos_snmp_community
version_added: "2.2"
short_description: Manages SNMP community configs.
description:
    - Manages SNMP community configuration.
extends_documentation_fragment: nxos
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
options:
    community:
        description:
            - Case-sensitive community string.
        required: true
    access:
        description:
            - Access type for community.
        required: false
        default: null
        choices: ['ro','rw']
    group:
        description:
            - Group to which the community belongs.
        required: false
        default: null
    acl:
        description:
            - ACL name to filter snmp requests.
        required: false
        default: 1
    state:
        description:
            - Manage the state of the resource.
        required: true
        default: present
        choices: ['present','absent']
    include_defaults:
        description:
            - Specify to use or not the complete runnning configuration
              for module operations.
        required: false
        default: false
        choices: ['true','false']
    config:
        description:
            - Configuration string to be used for module operations. If not
              specified, the module will use the current running configuration.
        required: false
        default: null
    save:
        description:
            - Specify to save the running configuration after
              module operations.
        required: false
        default: false
        choices: ['true','false']
'''

EXAMPLES = '''
# ensure snmp community is configured
- nxos_snmp_community:
    community: TESTING7
    group: network-operator
    state: present
    host: "{{ inventory_hostname }}"
    username: "{{ un }}"
    password: "{{ pwd }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"group": "network-operator"}
existing:
    description: k/v pairs of existing snmp community
    type: dict
    sample:  {}
end_state:
    description: k/v pairs of snmp community after module execution
    returned: always
    type: dict or null
    sample:  {"acl": "None", "group": "network-operator"}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["snmp-server community TESTING7 group network-operator"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

import json

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


def get_value(module, arg, config):
    existing = {}
    if arg == 'group':
        command = '.*snmp-server community {0} group (?P<group>\S+).*'.format(
                  module.params['community'])
        try:
            match_group = re.match(command, config, re.DOTALL)
            group = match_group.groupdict()['group']
            existing['group'] = group
            existing['community'] = module.params['community']
        except AttributeError:
            existing['group'] = ''
    elif arg == 'acl':
        command = '.*snmp-server community {0} use-acl (?P<acl>\S+).*'.format(
                  module.params['community'])
        try:
            match_acl = re.match(command, config, re.DOTALL)
            acl = match_acl.groupdict()['acl']
            existing['acl'] = acl
            existing['community'] = module.params['community']
        except AttributeError:
            existing['acl'] = ''
    return existing


def get_existing(module):
    existing = {}
    config = str(get_config(module))
    for arg in ['group', 'acl']:
        existing.update(get_value(module, arg, config))
    if existing.get('group') or existing.get('acl'):
        existing['community'] = module.params['community']
    existing = dict((key, value) for key, value in
                    existing.iteritems() if value)
    return existing


def state_absent(module, existing, proposed, candidate):
    commands = ['no snmp-server community {0}'.format(
                module.params['community'])]
    if commands:
        candidate.add(commands, parents=[])


def state_present(module, existing, proposed, candidate):
    CMDS = {
        'group': 'snmp-server community {0} group {1}',
        'acl': 'snmp-server community {0} use-acl {1}'
    }
    commands = []
    community = module.params['community']
    for key in ['group', 'acl']:
        if proposed.get(key):
            command = CMDS[key].format(community, proposed[key])
            commands.append(command)
    if commands:
        candidate.add(commands, parents=[])


def invoke(name, *args, **kwargs):
    func = globals().get(name)
    if func:
        return func(*args, **kwargs)


def main():
    argument_spec = dict(
            community=dict(required=True, type='str'),
            access=dict(choices=['ro', 'rw']),
            group=dict(type='str'),
            acl=dict(type='str'),
            state=dict(choices=['absent', 'present'], default='present'),
            include_defaults=dict(default=False),
            config=dict(),
            save=dict(type='bool', default=False)
    )
    module = get_network_module(argument_spec=argument_spec,
                                mutually_exclusive=[['access', 'group']],
                                supports_check_mode=True)

    access = module.params['access']
    group = module.params['group']
    state = module.params['state']

    if state == 'present':
        if not group and not access:
            module.fail_json(msg='group or access param must be '
                                 'used when state=present')

    if access:
        if access == 'ro':
            group = 'network-operator'
        elif access == 'rw':
            group = 'network-admin'

    args = ['community', 'acl']
    proposed = dict((k, v) for k, v in module.params.iteritems()
                    if v is not None and k in args)
    proposed['group'] = group
    existing = get_existing(module)
    end_state = existing

    result = {}
    if state == 'present' or (state == 'absent' and existing):
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
        end_state = invoke('get_existing', module)
        result['end_state'] = end_state
        result['existing'] = existing
        result['proposed'] = proposed

    module.exit_json(**result)


if __name__ == '__main__':
    main()
