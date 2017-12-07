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
                    'supported_by': 'network'}


DOCUMENTATION = '''
---
module: nxos_ping
extends_documentation_fragment: nxos
version_added: "2.1"
short_description: Tests reachability using ping from Nexus switch.
description:
    - Tests reachability using ping from switch to a remote destination.
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
    state:
        description:
            - Determines if the expected result is success or fail.
        choices: [ absent, present ]
        default: present
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
commands:
    description: Show the command sent
    returned: always
    type: list
    sample: ["ping 8.8.8.8 count 2 vrf management"]
rtt:
    description: Show RTT stats
    returned: always
    type: dict
    sample: {"avg": 6.264, "max": 6.564, "min": 5.978}
packets_rx:
    description: Packets successfully received
    returned: always
    type: int
    sample: 2
packets_tx:
    description: Packets successfully transmitted
    returned: always
    type: int
    sample: 2
packet_loss:
    description: Percentage of packets lost
    returned: always
    type: string
    sample: "0.00%"
'''
from ansible.module_utils.network.nxos.nxos import run_commands
from ansible.module_utils.network.nxos.nxos import nxos_argument_spec, check_args
from ansible.module_utils.basic import AnsibleModule


def get_summary(results_list, reference_point):
    summary_string = results_list[reference_point + 1]
    summary_list = summary_string.split(',')

    summary = dict(
        packets_tx=int(summary_list[0].split('packets')[0].strip()),
        packets_rx=int(summary_list[1].split('packets')[0].strip()),
        packet_loss=summary_list[2].split('packet')[0].strip(),
    )

    if 'bytes from' not in results_list[reference_point - 2]:
        ping_pass = False
    else:
        ping_pass = True

    return summary, ping_pass


def get_rtt(results_list, packet_loss, location):
    rtt = dict(min=None, avg=None, max=None)

    if packet_loss != '100.00%':
        rtt_string = results_list[location]
        base = rtt_string.split('=')[1]
        rtt_list = base.split('/')

        rtt['min'] = float(rtt_list[0].lstrip())
        rtt['avg'] = float(rtt_list[1])
        rtt['max'] = float(rtt_list[2][:-3])

    return rtt


def get_statistics_summary_line(response_as_list):
    for each in response_as_list:
        if '---' in each:
            index = response_as_list.index(each)
    return index


def get_ping_results(command, module):
    cmd = {'command': command, 'output': 'text'}
    ping = run_commands(module, [cmd])[0]

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
        rtt = get_rtt(splitted_ping, summary['packet_loss'], reference_point + 2)

    return (summary, rtt, ping_pass)


def main():
    argument_spec = dict(
        dest=dict(required=True),
        count=dict(required=False, default=2),
        vrf=dict(required=False),
        source=dict(required=False),
        state=dict(required=False, choices=['present', 'absent'], default='present'),
    )

    argument_spec.update(nxos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    destination = module.params['dest']
    count = module.params['count']
    state = module.params['state']

    if count and not 1 <= int(count) <= 655350:
        module.fail_json(msg="'count' must be an integer between 1 and 655350.", count=count)

    ping_command = 'ping {0}'.format(destination)
    for command in ['count', 'source', 'vrf']:
        arg = module.params[command]
        if arg:
            ping_command += ' {0} {1}'.format(command, arg)

    summary, rtt, ping_pass = get_ping_results(ping_command, module)

    results = summary
    results['rtt'] = rtt
    results['commands'] = [ping_command]

    if ping_pass and state == 'absent':
        module.fail_json(msg="Ping succeeded unexpectedly")
    elif not ping_pass and state == 'present':
        module.fail_json(msg="Ping failed unexpectedly")

    module.exit_json(**results)


if __name__ == '__main__':
    main()
