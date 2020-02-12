#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2020, Allied Telesis Ltd.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: awplus_ping
version_added: "2.10"
short_description: Tests reachability using ping from AlliedWare Plus network devices
description:
    - Tests reachability using ping from switch to a remote destination.
    - For a general purpose network module, see the M(net_ping) module.
    - For Windows targets, use the M(win_ping) module instead.
    - For targets running Python, use the M(ping) module instead.
author:
    - Cheng Yi Kok (@cyk19)
    - Isaac Daly (@dalyIsaac)
options:
    count:
        description:
            - Number of packets to send.
        default: 5
    dest:
        description:
            - The IP Address or hostname (resolvable by switch) of the remote node.
        required: true
    source:
        description:
            - The source IP Address.
    state:
        description:
            - Determines if the expected result is success or fail.
        choices: [ absent, present ]
        default: present
    vrf:
        description:
            - The VRF to use for forwarding.
        default: default
notes:
    - For a general purpose network module, see the M(net_ping) module.
    - For Windows targets, use the M(win_ping) module instead.
    - For targets running Python, use the M(ping) module instead.
    - Check mode is supported.
"""

EXAMPLES = """
- name: Test reachability to 10.30.30.30 using default vrf
awplus_ping:
    dest: 10.30.30.30
    state: absent

- name: Test reachability to 192.168.5.1
awplus_ping:
    dest: 192.168.5.1
    state: absent

- name: Test reachability tfrom ansible.module_utils.basic import AnsibleModule
awplus_ping:
    dest: 192.168.5.1
    vrf: red


- name: Test reachability to 192.168.5.89
awplus_ping:
    dest: 192.168.5.89
    state: present


- name: Test reachability to 192.168.5.1 setting count and source
awplus_ping:
    dest: 192.168.5.1
    source: vlan2
    count: 20
"""

RETURN = """
commands:
    description: Show the command sent.
    returned: always
    type: list
    sample: ['ping vrf prod 10.40.40.40 count 20 source loopback0']
packet_loss:
    description: Percentage of packets lost.
    returned: always
    type: str
    sample: '0%'
packets_rx:
    description: Packets successfully received.
    returned: always
    type: int
    sample: 20
packets_tx:
    description: Packets successfully transmitted.
    returned: always
    type: int
    sample: 20
rtt:
    description: Show RTT stats.
    returned: always
    type: dict
    sample: {'avg': 2, 'max': 8, 'min': 1}
"""


import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.awplus.awplus import run_commands
from ansible.module_utils.network.awplus.awplus import awplus_argument_spec


def parse_ping(ping_stats, fail):
    """
    Function used to parse the statistical information from the ping response.
    Example: "Success rate is 100 percent (5/5), round-trip min/avg/max = 1/2/8 ms"
    Returns the percent of packet loss, received packets, transmitted packets, and RTT dict.
    """

    if fail:
        rate = re.match(r'(?P<tx>\d+) packets transmitted, (?P<rx>\d+) received, \+\d+ errors, (?P<loss>\d+)% packet loss, .+',
                        ping_stats[0])
        rtt = None
    else:
        rate = re.match(r'(?P<tx>\d+) packets transmitted, (?P<rx>\d+) received, (?P<loss>\d+)% packet loss, .+',
                        ping_stats[0])
        rtt = re.match(
            r'rtt min/avg/max/mdev = (?P<min>\d+\.\d+)\/(?P<avg>\d+\.\d+)\/(?P<max>\d+\.\d+)', ping_stats[1])

    return rate.group('loss'), rate.group('rx'), rate.group('tx'), rtt


def build_ping(dest, count=None, source=None, vrf=None):
    """
    Function to build the command to send to the terminal for the switch
    to execute. All args come from the module's unique params.
    """
    if vrf is not None:
        cmd = 'ping vrf {0} {1}'.format(vrf, dest)
    else:
        cmd = 'ping {0}'.format(dest)

    if count is not None:
        cmd += ' repeat {0}'.format(str(count))

    if source is not None:
        cmd += ' source {0}'.format(source)

    return cmd


def validate_results(module, loss, results):
    """
    This function is used to validate whether the ping results were unexpected per 'state' param.
    """
    state = module.params['state']
    if state == 'present' and loss == 100:
        module.fail_json(msg='Ping failed unexpectedly', **results)
    elif state == 'absent' and loss < 100:
        module.fail_json(msg='Ping succeeded unexpectedly', **results)


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        count=dict(type='int'),
        dest=dict(type='str', required=True),
        source=dict(type='str'),
        state=dict(type='str', choices=[
                   'absent', 'present'], default='present'),
        vrf=dict(type='str')
    )

    argument_spec.update(awplus_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec)

    count = module.params['count']
    dest = module.params['dest']
    source = module.params['source']
    vrf = module.params['vrf']

    warnings = list()

    results = {}
    if warnings:
        results['warnings'] = warnings

    results['commands'] = [build_ping(dest, count, source, vrf)]

    ping_results = run_commands(module, commands=results['commands'])
    ping_results_list = ping_results[0].split('\n')

    stats = []
    fail = False
    for i in range(len(ping_results_list)):
        if 'transmitted' in ping_results_list[i]:
            if 'error' in ping_results_list[i]:
                fail = True
            stats.append(ping_results_list[i])
            stats.append(ping_results_list[i + 1])
            break

    if len(stats) == 0:
        module.fail_json(msg=ping_results_list)
    loss, rx, tx, rtt = parse_ping(stats, fail)

    results['packet_loss'] = str(loss) + '%'
    results['packets_rx'] = int(rx)
    results['packets_tx'] = int(tx)

    # Convert rtt values to int
    if rtt is not None:
        rtt_dict = rtt.groupdict()
        for k, v in rtt_dict.items():
            if rtt_dict[k] is not None:
                rtt_dict[k] = float(v)
        results['rtt'] = rtt_dict
    else:
        results['rtt'] = rtt

    validate_results(module, float(loss), results)
    module.exit_json(**results)


if __name__ == '__main__':
    main()
