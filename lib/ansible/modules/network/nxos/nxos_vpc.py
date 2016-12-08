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
module: nxos_vpc
version_added: "2.2"
short_description: Manages global VPC configuration
description:
    - Manages global VPC configuration
extends_documentation_fragment: nxos
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
notes:
    - The feature vpc must be enabled before this module can be used
    - If not using management vrf, vrf must be globally on the device
      before using in the pkl config
    - Although source IP isn't required on the command line it is
      required when using this module.  The PKL VRF must also be configured
      prior to using this module.
    - Both pkl_src and pkl_dest are needed when changing PKL VRF.
options:
    domain:
        description:
            - VPC domain
        required: true
    role_priority:
        description:
            - Role priority for device. Remember lower is better.
        required: false
        default: null
    system_priority:
        description:
            - System priority device.  Remember they must match between peers.
        required: false
        default: null
    pkl_src:
        description:
            - Source IP address used for peer keepalive link
        required: false
        default: null
    pkl_dest:
        description:
            - Destination (remote) IP address used for peer keepalive link
        required: false
        default: null
    pkl_vrf:
        description:
            - VRF used for peer keepalive link
        required: false
        default: management
    peer_gw:
        description:
            - Enables/Disables peer gateway
        required: true
        choices: ['true','false']
    auto_recovery:
        description:
            - Enables/Disables auto recovery
        required: true
        choices: ['true','false']
    delay_restore:
        description:
            - manages delay restore command and config value in seconds
        required: false
        default: null
    state:
        description:
            - Manages desired state of the resource
        required: true
        choices: ['present','absent']
'''

EXAMPLES = '''
# configure a simple asn
- nxos_vpc:
    domain: 100
    role_priority: 1000
    system_priority: 2000
    pkl_dest: 192.168.100.4
    pkl_src: 10.1.100.20
    peer_gw: true
    auto_recovery: true
    username: "{{ un }}"
    password: "{{ pwd }}"
    host: "{{ inventory_hostname }}"
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module
    returned: always
    type: dict
    sample: {"auto_recovery": true, "domain": "100",
            "peer_gw": true, "pkl_dest": "192.168.100.4",
            "pkl_src": "10.1.100.20", "pkl_vrf": "management",
            "role_priority": "1000", "system_priority": "2000"}
existing:
    description: k/v pairs of existing VPC configuration
    type: dict
    sample: {"auto_recovery": true, "delay_restore": null,
            "domain": "100", "peer_gw": true,
            "pkl_dest": "192.168.100.2", "pkl_src": "10.1.100.20",
            "pkl_vrf": "management", "role_priority": "1000",
            "system_priority": "2000"}
end_state:
    description: k/v pairs of VPC configuration after module execution
    returned: always
    type: dict
    sample: {"auto_recovery": true, "domain": "100",
            "peer_gw": true, "pkl_dest": "192.168.100.4",
            "pkl_src": "10.1.100.20", "pkl_vrf": "management",
            "role_priority": "1000", "system_priority": "2000"}
updates:
    description: commands sent to the device
    returned: always
    type: list
    sample: ["vpc domain 100",
            "peer-keepalive destination 192.168.100.4 source 10.1.100.20 vrf management",
            "auto-recovery", "peer-gateway"]
changed:
    description: check to see if a change was made on the device
    returned: always
    type: boolean
    sample: true
'''

import json
import collections

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


def get_cli_body_ssh(command, response, module):
    """Get response for when transport=cli.  This is kind of a hack and mainly
    needed because these modules were originally written for NX-API.  And
    not every command supports "| json" when using cli/ssh.
    """
    if '^' == response[0]:
        body = []
    elif 'running' in command:
        body = response
    else:
        if command in response[0]:
            response = [response[0].split(command)[1]]
        try:
            body = [json.loads(response[0])]
        except ValueError:
            module.fail_json(msg='Command does not support JSON output',
                             command=command)
    return body


def execute_show(cmds, module, command_type=None):
    command_type_map = {
        'cli_show': 'json',
        'cli_show_ascii': 'text'
    }

    try:
        if command_type:
            response = module.execute(cmds, command_type=command_type)
        else:
            response = module.execute(cmds)
    except ShellError:
        clie = get_exception()
        module.fail_json(msg='Error sending {0}'.format(cmds),
                         error=str(clie))
    except AttributeError:
        try:
            if command_type:
                command_type = command_type_map.get(command_type)
                module.cli.add_commands(cmds, output=command_type)
                response = module.cli.run_commands()
            else:
                module.cli.add_commands(cmds, raw=True)
                response = module.cli.run_commands()
        except ShellError:
            clie = get_exception()
            module.fail_json(msg='Error sending {0}'.format(cmds),
                             error=str(clie))
    return response


def execute_show_command(command, module, command_type='cli_show'):
    if module.params['transport'] == 'cli':
        if "section" not in command:
            command += ' | json'
        cmds = [command]
        response = execute_show(cmds, module)
        body = get_cli_body_ssh(command, response, module)
    elif module.params['transport'] == 'nxapi':
        cmds = [command]
        body = execute_show(cmds, module, command_type=command_type)

    return body


def flatten_list(command_lists):
    flat_command_list = []
    for command in command_lists:
        if isinstance(command, list):
            flat_command_list.extend(command)
        else:
            flat_command_list.append(command)
    return flat_command_list


def get_vrf_list(module):
    command = 'show vrf all'
    vrf_table = None

    body = execute_show_command(command, module)

    try:
        vrf_table = body[0]['TABLE_vrf']['ROW_vrf']
    except (KeyError, AttributeError):
        return []

    vrf_list = []
    if vrf_table:
        for each in vrf_table:
            vrf_list.append(str(each['vrf_name'].lower()))

    return vrf_list


def get_autorecovery(auto):
    auto_recovery = auto.split(' ')[0]
    if 'enabled' in auto_recovery.lower():
        return True
    else:
        return False


def get_vpc_running_config(module):
    command = 'show running section vpc'
    body = execute_show_command(command, module, command_type='cli_show_ascii')

    return body


def get_vpc(module):
    vpc = {}

    command = 'show vpc'
    body = execute_show_command(command, module)[0]
    domain = str(body['vpc-domain-id'])
    auto_recovery = get_autorecovery(str(
            body['vpc-auto-recovery-status']))

    if domain != 'not configured':
        delay_restore = None
        pkl_src = None
        role_priority = None
        system_priority = None
        pkl_dest = None
        pkl_vrf = None
        peer_gw = False

        run = get_vpc_running_config(module)[0]
        if run:
            vpc_list = run.split('\n')
            for each in vpc_list:
                if 'delay restore' in each:
                    line = each.split()
                    if len(line) == 5:
                        delay_restore = line[-1]
                if 'peer-keepalive destination' in each:
                    line = each.split()
                    pkl_dest = line[2]
                    for word in line:
                        if 'source' in word:
                            index = line.index(word)
                            pkl_src = line[index + 1]
                if 'role priority' in each:
                    line = each.split()
                    role_priority = line[-1]
                if 'system-priority' in each:
                    line = each.split()
                    system_priority = line[-1]
                if 'peer-gateway' in each:
                    peer_gw = True


        command = 'show vpc peer-keepalive'
        body = execute_show_command(command, module)[0]

        if body:
            pkl_dest = body['vpc-keepalive-dest']
            if 'N/A' in pkl_dest:
                pkl_dest = None
            elif len(pkl_dest) == 2:
                pkl_dest = pkl_dest[0]
            pkl_vrf = str(body['vpc-keepalive-vrf'])

        vpc['domain'] = domain
        vpc['auto_recovery'] = auto_recovery
        vpc['delay_restore'] = delay_restore
        vpc['pkl_src'] = pkl_src
        vpc['role_priority'] = role_priority
        vpc['system_priority'] = system_priority
        vpc['pkl_dest'] = pkl_dest
        vpc['pkl_vrf'] = pkl_vrf
        vpc['peer_gw'] = peer_gw
    else:
        vpc = {}

    return vpc


def get_commands_to_config_vpc(module, vpc, domain, existing):
    vpc = dict(vpc)

    domain_only = vpc.get('domain')
    pkl_src = vpc.get('pkl_src')
    pkl_dest = vpc.get('pkl_dest')
    pkl_vrf = vpc.get('pkl_vrf') or existing.get('pkl_vrf')
    vpc['pkl_vrf'] = pkl_vrf

    commands = []
    if pkl_src or pkl_dest:
        if pkl_src is None:
            vpc['pkl_src'] = existing.get('pkl_src')
        elif pkl_dest is None:
            vpc['pkl_dest'] = existing.get('pkl_dest')
        pkl_command = 'peer-keepalive destination {pkl_dest}'.format(**vpc) \
                      + ' source {pkl_src} vrf {pkl_vrf}'.format(**vpc)
        commands.append(pkl_command)
    elif pkl_vrf:
        pkl_src = existing.get('pkl_src')
        pkl_dest = existing.get('pkl_dest')
        if pkl_src and pkl_dest:
            pkl_command = ('peer-keepalive destination {0}'
                          ' source {1} vrf {2}'.format(pkl_dest, pkl_src, pkl_vrf))
            commands.append(pkl_command)

    if vpc.get('auto_recovery') == False:
        vpc['auto_recovery'] = 'no'
    else:
        vpc['auto_recovery'] = ''

    if vpc.get('peer_gw') == False:
        vpc['peer_gw'] = 'no'
    else:
        vpc['peer_gw'] = ''

    CONFIG_ARGS = {
        'role_priority': 'role priority {role_priority}',
        'system_priority': 'system-priority {system_priority}',
        'delay_restore': 'delay restore {delay_restore}',
        'peer_gw': '{peer_gw} peer-gateway',
        'auto_recovery': '{auto_recovery} auto-recovery',
        }

    for param, value in vpc.iteritems():
        command = CONFIG_ARGS.get(param, 'DNE').format(**vpc)
        if command and command != 'DNE':
            commands.append(command.strip())
        command = None

    if commands or domain_only:
        commands.insert(0, 'vpc domain {0}'.format(domain))
    return commands


def get_commands_to_remove_vpc_interface(portchannel, config_value):
    commands = []
    command = 'no vpc {0}'.format(config_value)
    commands.append(command)
    commands.insert(0, 'interface port-channel{0}'.format(portchannel))
    return commands


def main():
    argument_spec = dict(
            domain=dict(required=True, type='str'),
            role_priority=dict(required=False, type='str'),
            system_priority=dict(required=False, type='str'),
            pkl_src=dict(required=False),
            pkl_dest=dict(required=False),
            pkl_vrf=dict(required=False, default='management'),
            peer_gw=dict(required=True, type='bool'),
            auto_recovery=dict(required=True, type='bool'),
            delay_restore=dict(required=False, type='str'),
            state=dict(choices=['absent', 'present'], default='present'),
            include_defaults=dict(default=False),
            config=dict(),
            save=dict(type='bool', default=False)
    )
    module = get_network_module(argument_spec=argument_spec,
                                supports_check_mode=True)

    domain = module.params['domain']
    role_priority = module.params['role_priority']
    system_priority = module.params['system_priority']
    pkl_src = module.params['pkl_src']
    pkl_dest = module.params['pkl_dest']
    pkl_vrf = module.params['pkl_vrf']
    peer_gw = module.params['peer_gw']
    auto_recovery = module.params['auto_recovery']
    delay_restore = module.params['delay_restore']
    state = module.params['state']

    args = dict(domain=domain, role_priority=role_priority,
                system_priority=system_priority, pkl_src=pkl_src,
                pkl_dest=pkl_dest, pkl_vrf=pkl_vrf, peer_gw=peer_gw,
                auto_recovery=auto_recovery,
                delay_restore=delay_restore)

    if not (pkl_src and pkl_dest and pkl_vrf):
        # if only the source or dest is set, it'll fail and ask to set the
        # other
        if pkl_src or pkl_dest:
            module.fail_json(msg='source AND dest IP for pkl are required at '
                                 'this time (although source is technically not '
                                 ' required by the device.)')

        args.pop('pkl_src')
        args.pop('pkl_dest')
        args.pop('pkl_vrf')

    if pkl_vrf:
        if pkl_vrf.lower() not in get_vrf_list(module):
            module.fail_json(msg='The VRF you are trying to use for the peer '
                                 'keepalive link is not on device yet. Add it'
                                 ' first, please.')
    proposed = dict((k, v) for k, v in args.iteritems() if v is not None)
    changed = False
    existing = get_vpc(module)
    end_state = existing

    commands = []
    if state == 'present':
        delta = set(proposed.iteritems()).difference(existing.iteritems())
        if delta:
            command = get_commands_to_config_vpc(module, delta, domain, existing)
            commands.append(command)
    elif state == 'absent':
        if existing:
            if domain != existing['domain']:
                module.fail_json(msg="You are trying to remove a domain that "
                                     "does not exist on the device")
            else:
                commands.append('no vpc domain {0}'.format(domain))

    cmds = flatten_list(commands)

    if cmds:
        if module.check_mode:
            module.exit_json(changed=True, commands=cmds)
        else:
            changed = True
            execute_config_command(cmds, module)
            end_state = get_vpc(module)
            if 'configure' in cmds:
                cmds.pop(0)

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['end_state'] = end_state
    results['updates'] = cmds
    results['changed'] = changed

    module.exit_json(**results)


if __name__ == '__main__':
    main()
