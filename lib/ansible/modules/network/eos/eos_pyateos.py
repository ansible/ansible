#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: eos_pyateos
version_added: "2.9"
author:
  - "Federico Olivieri (@Federico87)"

short_description: Operational status tests on Arista device.
description: A snapshot of the operational status of a switch is taken before a
    config or network change and compare against a second snapshot taken after the change.
    A diff file is generated in .json format.
extends_documentation_fragment: eos
options:
    test:
        description:
        - One ore more test to be run. Every test correspond to a specific "show" command
        i.e. ntp - show ntp associations.
        For more details: https://gitlab.com/networkAutomation/pyateos/-/blob/master/README.md
        choices: [
            'acl',
            'arp',
            'as_path',
            'bgp_evpn',
            'bgp_ipv4',
            'interface',
            'ip_route',
            'mac',
            'mlag',
            'ntp',
            'lldp',
            'prefix_list',
            'route_map',
            'snmp',
            'stp',
            'vlan',
            'vrf',
            'vxlan']
        type: list
    before:
        description:
            - Run pre-check tests defined under 'test' and generate .json.
            The fiename and directory path is the following: /tests/before/hostname/timestamp.json
        default: false
        type: bool
    after:
        description:
            - Run post-check tests defined under 'test'.
            The fiename and directory path is the following: /tests/after/hostname/timestamp.json
        default: false
        type: bool
    diff:
        description:
            - Run between vs. after diffs and save the result in .json format.
            The fiename and directory path is the following: /tests/diff/hostname/diff_timestamp_before_after.json
        default: false
        type: bool
    files:
        description:
            - List of before and after file IDs to compare in order to generate diff. Each file id
            is available under `result.before_file_ids` and `result.after_file_ids`
        type: list
    filter:
        description:
            - Valid only with `compare`. Filter reduces the output returning just the
            `insert` and `delete` in diff i.e. intrface - all interfaces counters are filtered.
        type: bool
        default: false
    group:
        description:
            - Pre set group of test. `group` and `test` are allowed togehter.
            For more details: https://gitlab.com/networkAutomation/pyateos/-/blob/master/README.md
        type: list
    choices: [
        'mgmt',
        'routing',
        'layer2',
        'ctr',
        'all'
        ]
    hostname:
        description:
            - Device hostname required for filesystem build
        type: str
        required: true
requirements:
    - jsondiff
    - jmespath
"""

EXAMPLES = """
---
- name: run BEFORE tests.
  eos_pyateos:
    before: true
    test:
      - acl
    group:
      - mgmt
      - layer2
    hostname: "{{ inventory_hostname }}"
    register: result

- name: save BEFORE file IDs.
  delegate_to: 127.0.0.1
  set_fact:
    before_ids: "{{ result.before_file_ids }}"

- name: change mgmt config on switch.
  eos_config:
    lines:
      - no ntp server vrf mgmt 10.75.33.5
      - ntp server vrf mgmt 216.239.35.4

- name: run AFTER tests.
  eos_pyateos:
    after: true
    test:
      - acl
    group:
      - mgmt
      - layer2
    hostname: "{{ inventory_hostname }}"
    register: result

- name: save AFTER file IDs.
  delegate_to: 127.0.0.1
  set_fact:
    before_ids: "{{ result.after_file_ids }}"

- name: run DIFF result.
  eos_pyateos:
    compare: true
    group:
      - mgmt
      - layer2
    test: "{{ tests }}"
    hostname: "{{ inventory_hostname }}"
    filter: true
    files:
      - "{{ before_ids }}"
      - "{{ after_ids }}"
"""

RETURN = """
compare:
  description: before vs. after diff
  returned: always
  type: dict
  sample: {
    "delete": {
        "ns2.sys.cloudsys.tmcs": {
            "delay": 0.717,
            "jitter": 0.117,
            "lastReceived": 1583061550.0,
            "peerType": "unicast",
            "reachabilityHistory": [
                true,
                true
            ],
            "condition": "reject",
            "offset": 0.047,
            "peerIpAddr": "10.75.33.5",
            "pollInterval": 64,
            "refid": "169.254.0.1",
            "stratumLevel": 3
        }
    },
    "insert": {
        "time2.google.com": {
            "delay": 10.209,
            "jitter": 0.0,
            "lastReceived": 1583061584.0,
            "peerType": "unicast",
            "reachabilityHistory": [
                true
            ],
            "condition": "reject",
            "offset": -23.386,
            "peerIpAddr": "216.239.35.4",
            "pollInterval": 64,
            "refid": ".GOOG.",
            "stratumLevel": 1
        }
    }
}
"""
import os
import re
import sys
import json
import time
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.eos.eos import run_commands
from ansible.module_utils.network.eos.eos import eos_argument_spec
from ansible.module_utils.network.eos.eos import get_connection

try:
    from jsondiff import diff
    HAS_JSONDIFF = True
except ImportError:
    HAS_JSONDIFF = False

try:
    from jmespath import search
    HAS_JMESPATH = True
except ImportError:
    HAS_JMESPATH = False


class Test():
    def __init__(self, module):
        self.module = module

    def show(self, sh_cmd):
        cmd = {
            'command': sh_cmd,
            'output': 'json'}

        result = run_commands(self.module, [cmd])

        return result[0]


def run_test(module, test):

    before = module.params.get('before')
    after = module.params.get('after')
    host = module.params.get('hostname')
    file_name = round(time.time())

    if before:
        destination = './tests/before/{test}/{host}/'.format(
            test=test,
            host=host,
        )

    if after:
        destination = './tests/after/{test}/{host}/'.format(
            test=test,
            host=host,
        )

    if not os.path.exists(destination):
        os.makedirs(destination)

    cmds = {
        'ntp': 'show ntp associations',
        'snmp': 'show snmp host',
        'arp': 'show ip arp',
        'acl': 'show ip access-lists',
        'as_path': 'show ip as-path access-list',
        'bgp_evpn': 'show bgp evpn',
        'bgp_ipv4': 'show bgp ipv4 unicast',
        'interface': 'show interfaces',
        'ip_route': 'show ip route detail',
        'mac': 'show mac address-table',
        'lldp': 'show lldp neighbors',
        'mlag': 'show mlag',
        'prefix_list': 'show ip prefix-list',
        'route_map': 'show route-map',
        'stp': 'show spanning-tree topology status',
        'vlan': 'show vlan',
        'vrf': 'show vrf',
        'vxlan': 'show interfaces vxlan 1'
    }

    if test:
        result = Test(module).show(cmds.get(test))

    with open('{0}/{1}.json'.format(destination, file_name), 'w', encoding='utf-8') as file:
        json.dump(result, file, ensure_ascii=False, indent=4)

    return result, file_name


def run_compare(module, count, test):

    class CustomFilter():
        def filter_jmespath(self, test, legal_json_diff):
            plugins_filter = {
                'ntp': 'peers.{delete: delete, insert: insert}',
                'vlan': 'vlans.{delete: delete, insert: insert}',
                'as_path': 'activeIpAsPathLists.{delete: delete, insert: insert}',
                'lldp': 'lldpNeighbors.{delete: delete, insert: insert}'
            }

            if plugins_filter.get(test):
                final_diff = search(plugins_filter.get(test), legal_json_diff)
            elif test == 'interface':
                final_diff = CustomFilter().filter_iface_counters(legal_json_diff)
            elif test == 'acl':
                final_diff = CustomFilter().filter_acls_counters(legal_json_diff)
            else:
                final_diff = legal_json_diff

            return final_diff

        def filter_iface_counters(self, legal_json_diff):
            return_dict = {'interfaces': {}}

            for ifaces in legal_json_diff.values():
                for iface_name, iface_values in ifaces.items():

                    if iface_values.get('interfaceStatus'):
                        return_dict['interfaces'][iface_name] = legal_json_diff['interfaces'][iface_name]['interfaceStatus']

                    if iface_values.get('memberInterfaces'):
                        if iface_values['memberInterfaces'].get('delete') or iface_values['memberInterfaces'].get('insert'):
                            return_dict['interfaces'][iface_name] = legal_json_diff['interfaces'][iface_name]['memberInterfaces']

                    if iface_name == 'insert' or iface_name == 'delete':
                        return_dict['interfaces'][iface_name] = legal_json_diff['interfaces'][iface_name]

            return return_dict

        def filter_acls_counters(self, legal_json_diff):
            return_dict = {'aclList': {}}

            for acls in legal_json_diff.values():
                for acl_number, sequences in acls.items():
                    for seq_number in sequences.values():
                        for values in seq_number.values():
                            if values.get('ruleFilter'):
                                return_dict['aclList'][acl_number] = {'sequence': {}}
                                return_dict['aclList'][acl_number]['sequence'] = seq_number

                                return return_dict

    def replace(string, test):
        substitutions = {
            '\'': '\"',
            'insert': '"insert"',
            'delete': '"delete"',
            'True': 'true',
            'False': 'false',
            '(': '[',
            ')': ']',
        }

        skip_list = [
            'vrf',
        ]

        substrings = sorted(substitutions, key=len, reverse=True)
        regex = re.compile('|'.join(map(re.escape, substrings)))
        sub_applied = regex.sub(lambda match: substitutions[match.group(0)], string)

        if test not in skip_list:
            for integer in re.findall(r'\d+:\s', sub_applied):
                sub_applied = sub_applied.replace(integer, f'"{integer[:-1]}": ')

        return sub_applied

    before_file = module.params.get('files')[0]
    after_file = module.params.get('files')[1]
    filter_flag = module.params.get('filter')
    host = module.params.get('hostname')

    if len(before_file) == len(after_file):

        try:
            before = open('./tests/before/{test}/{host}/{before_file}.json'.format(
                test=test,
                host=host,
                before_file=str(before_file[count]),
            ), 'r')
        except FileNotFoundError as error:
            return error

        try:
            after = open('./tests/after/{test}/{host}/{after_file}.json'.format(
                test=test,
                host=host,
                after_file=str(after_file[count]),
            ), 'r')
        except FileNotFoundError as error:
            return error

        destination = './tests/diff/{test}/{host}/'.format(
            test=test,
            host=host,
        )

        if not os.path.exists(destination):
            os.makedirs(destination)

        json_diff = str(diff(before, after, load=True, syntax='symmetric'))
        legal_json_diff = replace(json_diff, test)

        if not filter_flag:
            final_diff = json.loads(legal_json_diff)

        if filter_flag:
            final_diff = CustomFilter().filter_jmespath(test, json.loads(legal_json_diff))

        diff_file_id = str((int(before_file[count]) - int(after_file[count])) * -1)

        with open('{destination}{diff_file_id}.json'.format(
            destination=destination,
            diff_file_id=diff_file_id,
        ), 'w', encoding='utf-8') as file:
            json.dump(final_diff, file, ensure_ascii=False, indent=4)

    return final_diff


def main():

    argument_spec = dict(
        test=dict(type='list', choices=[
            'acl',
            'arp',
            'as_path',
            'bgp_evpn',
            'bgp_ipv4',
            'interface',
            'ip_route',
            'mac',
            'mlag',
            'ntp',
            'lldp',
            'prefix_list',
            'route_map',
            'snmp',
            'stp',
            'vlan',
            'vrf',
            'vxlan',
        ]),
        before=dict(type='bool', default=False),
        after=dict(type='bool', default=False),
        compare=dict(type='bool', default=False),
        files=dict(type='list'),
        filter=dict(type='bool', default=False),
        group=dict(type='list', choices=[
            'mgmt',
            'routing',
            'layer2',
            'ctrl',
            'all',
        ]),
        hostname=dict(required=True),
    )

    argument_spec.update(eos_argument_spec)

    mutually_exclusive = [('before', 'after', 'compare')]
    required_if = [('compare', True, ['files'])]
    required_one_of = [('test', 'group'), ('before', 'after', 'compare')]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           required_if=required_if,
                           required_one_of=required_one_of
                           )

    if not HAS_JSONDIFF:
        return module.fail_json(msg="jsondiff is not installed, try 'pip install jsondiff'")

    if not HAS_JMESPATH:
        return module.fail_json(msg="jmespath is not installed, try 'pip install jmespath'")

    list_ids = list()
    group = module.params.get('group')

    if module.params.get('test'):
        test_run = module.params.get('test')

    if not module.params.get('test'):
        test_run = list()

    test_all = [
        'acl',
        'arp',
        'as_path',
        'bgp_evpn',
        'bgp_ipv4',
        'interface',
        'ip_route',
        'mac',
        'mlag',
        'ntp',
        'lldp',
        'prefix_list',
        'route_map',
        'snmp',
        'stp',
        'vlan',
        'vrf',
        'vxlan',
    ]

    if group:
        if 'mgmt' in group:
            test_run.extend(('ntp', 'snmp'))

        if 'routing' in group:
            test_run.extend(('bgp_evpn', 'bgp_ipv4', 'ip_route'))

        if 'layer2' in group:
            test_run.extend(('stp', 'vlan', 'vxlan', 'lldp', 'arp', 'mac'))

        if 'ctrl' in group:
            test_run.extend(('acl', 'as_path', 'prefix_list', 'route_map'))

        if 'all' in group:
            test_run = test_all

    result = {'changed': False}

    for count, test in enumerate(sorted(set(test_run))):

        if module.params['before']:
            result[test], file_id = run_test(module, test)
            list_ids.append(file_id)
            result['before_file_ids'] = list_ids

        if module.params['after']:
            result[test], file_id = run_test(module, test)
            list_ids.append(file_id)
            result['after_file_ids'] = list_ids

        if module.params['compare']:
            result['compare'] = run_compare(module, count, test)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
