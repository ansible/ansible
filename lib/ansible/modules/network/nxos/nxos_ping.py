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
module: nxos_ping
version_added: "2.1"
short_description: Tests reachability using ping from Nexus switch.
description:
    - Tests reachability using ping from switch to a remote destination.
extends_documentation_fragment: nxos
author:
    - Jason Edelman (@jedelman8)
    - Gabriele Gerbino (@GGabriele)
options:
    dest:
        description:
            - IP address or hostname (resolvable by switch) of remote node.
        required: true
    count:
        description:
            - Number of packets to send.
        required: false
        default: 2
    source:
        description:
            - Source IP Address.
        required: false
        default: null
    vrf:
        description:
            - Outgoing VRF.
        required: false
        default: null
'''

EXAMPLES = '''
- name: Test reachability to 8.8.8.8 using mgmt vrf
  nxos_ping:
    dest: 8.8.8.8
    vrf: management
    host: 68.170.147.165

- name: Test reachability to a few different public IPs using mgmt vrf
  nxos_ping:
    dest: nxos_ping
    vrf: management
    host: 68.170.147.165
  with_items:
    - 8.8.8.8
    - 4.4.4.4
    - 198.6.1.4
'''

RETURN = '''
action:
    description:
        - Show what action has been performed
    returned: always
    type: string
    sample: "PING 8.8.8.8 (8.8.8.8): 56 data bytes"
updates:
    description: Show the command sent
    returned: always
    type: list
    sample: ["ping 8.8.8.8 count 2 vrf management"]
count:
    description: Show amount of packets sent
    returned: always
    type: string
    sample: "2"
dest:
    description: Show the ping destination
    returned: always
    type: string
    sample: "8.8.8.8"
rtt:
    description: Show RTT stats
    returned: always
    type: dict
    sample: {"avg": "6.264","max":"6.564",
            "min": "5.978"}
packets_rx:
    description: Packets successfully received
    returned: always
    type: string
    sample: "2"
packets_tx:
    description: Packets successfully transmitted
    returned: always
    type: string
    sample: "2"
packet_loss:
    description: Percentage of packets lost
    returned: always
    type: string
    sample: "0.00%"
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

def get_summary(results_list, reference_point):
    summary_string = results_list[reference_point+1]
    summary_list = summary_string.split(',')
    pkts_tx = summary_list[0].split('packets')[0].strip()
    pkts_rx = summary_list[1].split('packets')[0].strip()
    pkt_loss = summary_list[2].split('packet')[0].strip()
    summary = dict(packets_tx=pkts_tx,
                   packets_rx=pkts_rx,
                   packet_loss=pkt_loss)

    if 'bytes from' not in results_list[reference_point-2]:
        ping_pass = False
    else:
        ping_pass = True

    return summary, ping_pass


def get_rtt(results_list, packet_loss, location):
    if packet_loss != '100.00%':
        rtt_string = results_list[location]
        base = rtt_string.split('=')[1]
        rtt_list = base.split('/')
        min_rtt = rtt_list[0].lstrip()
        avg_rtt = rtt_list[1]
        max_rtt = rtt_list[2][:-3]
        rtt = dict(min=min_rtt, avg=avg_rtt, max=max_rtt)
    else:
        rtt = dict(min=None, avg=None, max=None)

    return rtt


def get_statistics_summary_line(response_as_list):
    for each in response_as_list:
        if '---' in each:
            index = response_as_list.index(each)
    return index


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
                module.cli.add_commands(cmds, output=command_type)
                response = module.cli.run_commands()
        except ShellError:
            clie = get_exception()
            module.fail_json(msg='Error sending {0}'.format(cmds),
                             error=str(clie))
    return response


def execute_show_command_ping(command, module, command_type='cli_show_ascii'):
    cmds = [command]
    if module.params['transport'] == 'cli':
        body = execute_show(cmds, module)
    elif module.params['transport'] == 'nxapi':
        body = execute_show(cmds, module, command_type=command_type)
    return body


def get_ping_results(command, module, transport):
    ping = execute_show_command_ping(command, module)[0]

    if not ping:
        module.fail_json(msg="An unexpected error occurred. Check all params.",
                         command=command, destination=module.params['dest'],
                         vrf=module.params['vrf'],
                         source=module.params['source'])

    elif "can't bind to address" in ping:
        module.fail_json(msg="Can't bind to source address.", command=command)
    elif "bad context" in ping:
        module.fail_json(msg="Wrong VRF name inserted.", command=command,
                         vrf=module.params['vrf'])
    else:
        splitted_ping = ping.split('\n')
        reference_point = get_statistics_summary_line(splitted_ping)
        summary, ping_pass = get_summary(splitted_ping, reference_point)
        rtt = get_rtt(splitted_ping, summary['packet_loss'], reference_point+2)

    return (splitted_ping, summary, rtt, ping_pass)


def main():
    argument_spec = dict(
            dest=dict(required=True),
            count=dict(required=False, default=2),
            vrf=dict(required=False),
            source=dict(required=False),
            state=dict(required=False, choices=['present', 'absent'],
                       default='present'),
            include_defaults=dict(default=False),
            config=dict(),
            save=dict(type='bool', default=False)
    )
    module = get_network_module(argument_spec=argument_spec,
                        supports_check_mode=True)

    destination = module.params['dest']
    count = module.params['count']
    vrf = module.params['vrf']
    source = module.params['source']
    state = module.params['state']

    if count:
        try:
            if int(count) < 1 or int(count) > 655350:
                raise ValueError
        except ValueError:
            module.fail_json(msg="'count' must be an integer between 1 "
                                 "and 655350.", count=count)

    OPTIONS = {
        'vrf': vrf,
        'count': count,
        'source': source
        }

    ping_command = 'ping {0}'.format(destination)
    for command, arg in OPTIONS.iteritems():
        if arg:
            ping_command += ' {0} {1}'.format(command, arg)

    ping_results, summary, rtt, ping_pass = get_ping_results(
                    ping_command, module, module.params['transport'])

    packet_loss = summary['packet_loss']
    packets_rx = summary['packets_rx']
    packets_tx = summary['packets_tx']

    results = {}
    results['updates'] = [ping_command]
    results['action'] = ping_results[1]
    results['dest'] = destination
    results['count'] = count
    results['packets_tx'] = packets_tx
    results['packets_rx'] = packets_rx
    results['packet_loss'] = packet_loss
    results['rtt'] = rtt
    results['state'] = module.params['state']

    if ping_pass and state == 'absent':
        module.fail_json(msg="Ping succeeded unexpectedly", results=results)
    elif not ping_pass and state == 'present':
        module.fail_json(msg="Ping failed unexpectedly", results=results)
    else:
        module.exit_json(**results)


if __name__ == '__main__':
    main()
