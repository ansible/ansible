#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: iosxr_interface
version_added: "2.4"
author:
    - "Ganesh Nalawade (@ganeshrn)"
    - "Kedar Kekan (@kedarX)"
short_description: Manage Interface on Cisco IOS XR network devices
description:
  - This module provides declarative management of Interfaces
    on Cisco IOS XR network devices.
extends_documentation_fragment: iosxr
notes:
  - Tested against IOS XRv 6.1.2
  - Preconfiguration of physical interfaces is not supported with C(netconf) transport.
options:
  name:
    description:
      - Name of the interface to configure in C(type + path) format. e.g. C(GigabitEthernet0/0/0/0)
    required: true
  description:
    description:
      - Description of Interface being configured.
  enabled:
    description:
      - Removes the shutdown configuration, which removes the forced administrative down on the interface,
        enabling it to move to an up or down state.
    type: bool
    default: True
  active:
    description:
      - Whether the interface is C(active) or C(preconfigured). Preconfiguration allows you to configure modular
        services cards before they are inserted into the router. When the cards are inserted, they are instantly
        configured. Active cards are the ones already inserted.
    choices: ['active', 'preconfigure']
    default: active
    version_added: 2.5
  speed:
    description:
      - Configure the speed for an interface. Default is auto-negotiation when not configured.
    choices: ['10', '100', '1000']
  mtu:
    description:
      - Sets the MTU value for the interface. Range is between 64 and 65535'
  duplex:
    description:
      - Configures the interface duplex mode. Default is auto-negotiation when not configured.
    choices: ['full', 'half']
  tx_rate:
    description:
      - Transmit rate in bits per second (bps).
      - This is state check parameter only.
      - Supports conditionals, see L(Conditionals in Networking Modules,../network/user_guide/network_working_with_command_output.html)
  rx_rate:
    description:
      - Receiver rate in bits per second (bps).
      - This is state check parameter only.
      - Supports conditionals, see L(Conditionals in Networking Modules,../network/user_guide/network_working_with_command_output.html)
  aggregate:
    description:
      - List of Interface definitions. Include multiple interface configurations together,
        one each on a seperate line
  delay:
    description:
      - Time in seconds to wait before checking for the operational state on remote
        device. This wait is applicable for operational state argument which are
        I(state) with values C(up)/C(down), I(tx_rate) and I(rx_rate).
    default: 10
  state:
    description:
      - State of the Interface configuration, C(up) means present and
        operationally up and C(down) means present and operationally C(down)
    default: present
    choices: ['present', 'absent', 'up', 'down']
"""

EXAMPLES = """
- name: configure interface
  iosxr_interface:
      name: GigabitEthernet0/0/0/2
      description: test-interface
      speed: 100
      duplex: half
      mtu: 512

- name: remove interface
  iosxr_interface:
    name: GigabitEthernet0/0/0/2
    state: absent

- name: make interface up
  iosxr_interface:
    name: GigabitEthernet0/0/0/2
    enabled: True

- name: make interface down
  iosxr_interface:
    name: GigabitEthernet0/0/0/2
    enabled: False

- name: Create interface using aggregate
  iosxr_interface:
    aggregate:
    - name: GigabitEthernet0/0/0/3
    - name: GigabitEthernet0/0/0/2
    speed: 100
    duplex: full
    mtu: 512
    state: present

- name: Create interface using aggregate along with additional params in aggregate
  iosxr_interface:
    aggregate:
    - { name: GigabitEthernet0/0/0/3, description: test-interface 3 }
    - { name: GigabitEthernet0/0/0/2, description: test-interface 2 }
    speed: 100
    duplex: full
    mtu: 512
    state: present

- name: Delete interface using aggregate
  iosxr_interface:
    aggregate:
    - name: GigabitEthernet0/0/0/3
    - name: GigabitEthernet0/0/0/2
    state: absent

- name: Check intent arguments
  iosxr_interface:
    name: GigabitEthernet0/0/0/5
    state: up
    delay: 20

- name: Config + intent
  iosxr_interface:
    name: GigabitEthernet0/0/0/5
    enabled: False
    state: down
    delay: 20
"""

RETURN = """
commands:
  description: The list of configuration mode commands sent to device with transport C(cli)
  returned: always (empty list when no commands to send)
  type: list
  sample:
  - interface GigabitEthernet0/0/0/2
  - description test-interface
  - duplex half
  - mtu 512

xml:
  description: NetConf rpc xml sent to device with transport C(netconf)
  returned: always (empty list when no xml rpc to send)
  type: list
  version_added: 2.5
  sample:
  - '<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <interface-configurations xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg">
    <interface-configuration xc:operation="merge">
    <active>act</active>
    <interface-name>GigabitEthernet0/0/0/0</interface-name>
    <description>test-interface-0</description>
    <mtus><mtu>
    <owner>GigabitEthernet</owner>
    <mtu>512</mtu>
    </mtu></mtus>
    <ethernet xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-drivers-media-eth-cfg">
    <speed>100</speed>
    <duplex>half</duplex>
    </ethernet>
    </interface-configuration>
    </interface-configurations></config>'
"""
import re
from time import sleep
from copy import deepcopy
import collections

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.iosxr.iosxr import get_config, load_config, build_xml
from ansible.module_utils.network.iosxr.iosxr import run_command, iosxr_argument_spec, get_oper
from ansible.module_utils.network.iosxr.iosxr import is_netconf, is_cliconf, etree_findall, etree_find
from ansible.module_utils.network.common.utils import conditional, remove_default_spec


def validate_mtu(value):
    if value and not 64 <= int(value) <= 65535:
        return False, 'mtu must be between 64 and 65535'
    return True, None


class ConfigBase(object):
    def __init__(self, module):
        self._module = module
        self._result = {'changed': False, 'warnings': []}
        self._want = list()
        self._have = list()

    def validate_param_values(self, param=None):
        for key, value in param.items():
            # validate the param value (if validator func exists)
            validator = globals().get('validate_%s' % key)
            if callable(validator):
                rc, msg = validator(value)
                if not rc:
                    self._module.fail_json(msg=msg)

    def map_params_to_obj(self):
        aggregate = self._module.params.get('aggregate')
        if aggregate:
            for item in aggregate:
                for key in item:
                    if item.get(key) is None:
                        item[key] = self._module.params[key]

                self.validate_param_values(item)
                d = item.copy()

                match = re.match(r"(^[a-z]+)([0-9/]+$)", d['name'], re.I)
                if match:
                    d['owner'] = match.groups()[0]

                if d['active'] == 'preconfigure':
                    d['active'] = 'pre'
                else:
                    d['active'] = 'act'

                self._want.append(d)

        else:
            self.validate_param_values(self._module.params)
            params = {
                'name': self._module.params['name'],
                'description': self._module.params['description'],
                'speed': self._module.params['speed'],
                'mtu': self._module.params['mtu'],
                'duplex': self._module.params['duplex'],
                'state': self._module.params['state'],
                'delay': self._module.params['delay'],
                'tx_rate': self._module.params['tx_rate'],
                'rx_rate': self._module.params['rx_rate'],
                'enabled': self._module.params['enabled'],
                'active': self._module.params['active'],
            }

            match = re.match(r"(^[a-z]+)([0-9/]+$)", params['name'], re.I)
            if match:
                params['owner'] = match.groups()[0]

                if params['active'] == 'preconfigure':
                    params['active'] = 'pre'
                else:
                    params['active'] = 'act'

            self._want.append(params)


class CliConfiguration(ConfigBase):
    def __init__(self, module):
        super(CliConfiguration, self).__init__(module)

    def parse_shutdown(self, intf_config):
        for cfg in intf_config:
            match = re.search(r'%s' % 'shutdown', cfg, re.M)
            if match:
                return True
        return False

    def parse_config_argument(self, intf_config, arg):
        for cfg in intf_config:
            match = re.search(r'%s (.+)$' % arg, cfg, re.M)
            if match:
                return match.group(1)

    def search_obj_in_list(self, name):
        for obj in self._have:
            if obj['name'] == name:
                return obj
        return None

    def map_config_to_obj(self):
        data = get_config(self._module, config_filter='interface')
        interfaces = data.strip().rstrip('!').split('!')

        if not interfaces:
            return list()

        for interface in interfaces:
            intf_config = interface.strip().splitlines()

            name = intf_config[0].strip().split()[1]

            active = 'act'
            if name == 'preconfigure':
                active = 'pre'
                name = intf_config[0].strip().split()[2]

            obj = {
                'name': name,
                'description': self.parse_config_argument(intf_config, 'description'),
                'speed': self.parse_config_argument(intf_config, 'speed'),
                'duplex': self.parse_config_argument(intf_config, 'duplex'),
                'mtu': self.parse_config_argument(intf_config, 'mtu'),
                'enabled': True if not self.parse_shutdown(intf_config) else False,
                'active': active,
                'state': 'present'
            }
            self._have.append(obj)

    def map_obj_to_commands(self):
        commands = list()

        args = ('speed', 'description', 'duplex', 'mtu')
        for want_item in self._want:
            name = want_item['name']
            disable = not want_item['enabled']
            state = want_item['state']

            obj_in_have = self.search_obj_in_list(name)
            interface = 'interface ' + name

            if state == 'absent' and obj_in_have:
                commands.append('no ' + interface)

            elif state in ('present', 'up', 'down'):
                if obj_in_have:
                    for item in args:
                        candidate = want_item.get(item)
                        running = obj_in_have.get(item)
                        if candidate != running:
                            if candidate:
                                cmd = interface + ' ' + item + ' ' + str(candidate)
                                commands.append(cmd)

                    if disable and obj_in_have.get('enabled', False):
                        commands.append(interface + ' shutdown')
                    elif not disable and not obj_in_have.get('enabled', False):
                        commands.append('no ' + interface + ' shutdown')
                else:
                    for item in args:
                        value = want_item.get(item)
                        if value:
                            commands.append(interface + ' ' + item + ' ' + str(value))
                    if not disable:
                        commands.append('no ' + interface + ' shutdown')
        self._result['commands'] = commands

        if commands:
            commit = not self._module.check_mode
            diff = load_config(self._module, commands, commit=commit)
            if diff:
                self._result['diff'] = dict(prepared=diff)
            self._result['changed'] = True

    def check_declarative_intent_params(self):
        failed_conditions = []
        for want_item in self._want:
            want_state = want_item.get('state')
            want_tx_rate = want_item.get('tx_rate')
            want_rx_rate = want_item.get('rx_rate')
            if want_state not in ('up', 'down') and not want_tx_rate and not want_rx_rate:
                continue

            if self._result['changed']:
                sleep(want_item['delay'])

            command = 'show interfaces {!s}'.format(want_item['name'])
            out = run_command(self._module, command)[0]

            if want_state in ('up', 'down'):
                match = re.search(r'%s (\w+)' % 'line protocol is', out, re.M)
                have_state = None
                if match:
                    have_state = match.group(1)
                    if have_state.strip() == 'administratively':
                        match = re.search(r'%s (\w+)' % 'administratively', out, re.M)
                        if match:
                            have_state = match.group(1)

                if have_state is None or not conditional(want_state, have_state.strip()):
                    failed_conditions.append('state ' + 'eq({!s})'.format(want_state))

            if want_tx_rate:
                match = re.search(r'%s (\d+)' % 'output rate', out, re.M)
                have_tx_rate = None
                if match:
                    have_tx_rate = match.group(1)

                if have_tx_rate is None or not conditional(want_tx_rate, have_tx_rate.strip(), cast=int):
                    failed_conditions.append('tx_rate ' + want_tx_rate)

            if want_rx_rate:
                match = re.search(r'%s (\d+)' % 'input rate', out, re.M)
                have_rx_rate = None
                if match:
                    have_rx_rate = match.group(1)

                if have_rx_rate is None or not conditional(want_rx_rate, have_rx_rate.strip(), cast=int):
                    failed_conditions.append('rx_rate ' + want_rx_rate)

        if failed_conditions:
            msg = 'One or more conditional statements have not been satisfied'
            self._module.fail_json(msg=msg, failed_conditions=failed_conditions)

    def run(self):
        self.map_params_to_obj()
        self.map_config_to_obj()
        self.map_obj_to_commands()
        self.check_declarative_intent_params()

        return self._result


class NCConfiguration(ConfigBase):
    def __init__(self, module):
        super(NCConfiguration, self).__init__(module)

        self._intf_meta = collections.OrderedDict()
        self._shut_meta = collections.OrderedDict()
        self._data_rate_meta = collections.OrderedDict()
        self._line_state_meta = collections.OrderedDict()

    def map_obj_to_xml_rpc(self):
        self._intf_meta.update([
            ('interface-configuration', {'xpath': 'interface-configurations/interface-configuration', 'tag': True, 'attrib': 'operation'}),
            ('a:active', {'xpath': 'interface-configurations/interface-configuration/active', 'operation': 'edit'}),
            ('a:name', {'xpath': 'interface-configurations/interface-configuration/interface-name'}),
            ('a:description', {'xpath': 'interface-configurations/interface-configuration/description', 'operation': 'edit'}),
            ('mtus', {'xpath': 'interface-configurations/interface-configuration/mtus', 'tag': True, 'operation': 'edit'}),
            ('mtu', {'xpath': 'interface-configurations/interface-configuration/mtus/mtu', 'tag': True, 'operation': 'edit'}),
            ('a:owner', {'xpath': 'interface-configurations/interface-configuration/mtus/mtu/owner', 'operation': 'edit'}),
            ('a:mtu', {'xpath': 'interface-configurations/interface-configuration/mtus/mtu/mtu', 'operation': 'edit'}),
            ('CEthernet', {'xpath': 'interface-configurations/interface-configuration/ethernet', 'tag': True, 'operation': 'edit', 'ns': True}),
            ('a:speed', {'xpath': 'interface-configurations/interface-configuration/ethernet/speed', 'operation': 'edit'}),
            ('a:duplex', {'xpath': 'interface-configurations/interface-configuration/ethernet/duplex', 'operation': 'edit'}),
        ])

        self._shut_meta.update([
            ('interface-configuration', {'xpath': 'interface-configurations/interface-configuration', 'tag': True}),
            ('a:active', {'xpath': 'interface-configurations/interface-configuration/active', 'operation': 'edit'}),
            ('a:name', {'xpath': 'interface-configurations/interface-configuration/interface-name'}),
            ('shutdown', {'xpath': 'interface-configurations/interface-configuration/shutdown', 'tag': True, 'operation': 'edit', 'attrib': 'operation'}),
        ])
        state = self._module.params['state']

        _get_filter = build_xml('interface-configurations', xmap=self._intf_meta, params=self._want, opcode="filter")

        running = get_config(self._module, source='running', config_filter=_get_filter)
        intfcfg_nodes = etree_findall(running, 'interface-configuration')

        intf_list = set()
        shut_list = set()
        for item in intfcfg_nodes:
            intf_name = etree_find(item, 'interface-name').text
            if intf_name is not None:
                intf_list.add(intf_name)

                if etree_find(item, 'shutdown') is not None:
                    shut_list.add(intf_name)

        intf_params = list()
        shut_params = list()
        noshut_params = list()
        for index, item in enumerate(self._want):
            if item['name'] in intf_list:
                intf_params.append(item)
            if not item['enabled']:
                shut_params.append(item)
            if item['name'] in shut_list and item['enabled']:
                noshut_params.append(item)

        opcode = None
        if state == 'absent':
            if intf_params:
                opcode = "delete"
        elif state in ('present', 'up', 'down'):
            intf_params = self._want
            opcode = 'merge'

        self._result['xml'] = []
        _edit_filter_list = list()
        if opcode:
            _edit_filter_list.append(build_xml('interface-configurations', xmap=self._intf_meta,
                                               params=intf_params, opcode=opcode))

            if opcode == 'merge':
                if len(shut_params):
                    _edit_filter_list.append(build_xml('interface-configurations', xmap=self._shut_meta,
                                                       params=shut_params, opcode='merge'))
                if len(noshut_params):
                    _edit_filter_list.append(build_xml('interface-configurations', xmap=self._shut_meta,
                                                       params=noshut_params, opcode='delete'))
            diff = None
            if len(_edit_filter_list):
                commit = not self._module.check_mode
                diff = load_config(self._module, _edit_filter_list, commit=commit, running=running,
                                   nc_get_filter=_get_filter)

            if diff:
                if self._module._diff:
                    self._result['diff'] = dict(prepared=diff)

                self._result['xml'] = _edit_filter_list
                self._result['changed'] = True

    def check_declarative_intent_params(self):
        failed_conditions = []

        self._data_rate_meta.update([
            ('interfaces', {'xpath': 'infra-statistics/interfaces', 'tag': True}),
            ('interface', {'xpath': 'infra-statistics/interfaces/interface', 'tag': True}),
            ('a:name', {'xpath': 'infra-statistics/interfaces/interface/interface-name'}),
            ('cache', {'xpath': 'infra-statistics/interfaces/interface/cache', 'tag': True}),
            ('data-rate', {'xpath': 'infra-statistics/interfaces/interface/cache/data-rate', 'tag': True}),
            ('input-data-rate', {'xpath': 'infra-statistics/interfaces/interface/cache/data-rate/input-data-rate', 'tag': True}),
            ('output-data-rate', {'xpath': 'infra-statistics/interfaces/interface/cache/data-rate/output-data-rate', 'tag': True}),
        ])

        self._line_state_meta.update([
            ('data-nodes', {'xpath': 'interface-properties/data-nodes', 'tag': True}),
            ('data-node', {'xpath': 'interface-properties/data-nodes/data-node', 'tag': True}),
            ('system-view', {'xpath': 'interface-properties/data-nodes/data-node/system-view', 'tag': True}),
            ('interfaces', {'xpath': 'interface-properties/data-nodes/data-node/system-view/interfaces', 'tag': True}),
            ('interface', {'xpath': 'interface-properties/data-nodes/data-node/system-view/interfaces/interface', 'tag': True}),
            ('a:name', {'xpath': 'interface-properties/data-nodes/data-node/system-view/interfaces/interface/interface-name'}),
            ('line-state', {'xpath': 'interface-properties/data-nodes/data-node/system-view/interfaces/interface/line-state', 'tag': True}),
        ])

        _rate_filter = build_xml('infra-statistics', xmap=self._data_rate_meta, params=self._want, opcode="filter")
        out = get_oper(self._module, filter=_rate_filter)
        data_rate_list = etree_findall(out, 'interface')
        data_rate_map = dict()
        for item in data_rate_list:
            data_rate_map.update({etree_find(item, 'interface-name').text: dict()})
            data_rate_map[etree_find(item, 'interface-name').text].update({'input-data-rate': etree_find(item, 'input-data-rate').text,
                                                                           'output-data-rate': etree_find(item, 'output-data-rate').text})

        _line_state_filter = build_xml('interface-properties', xmap=self._line_state_meta, params=self._want, opcode="filter")
        out = get_oper(self._module, filter=_line_state_filter)
        line_state_list = etree_findall(out, 'interface')
        line_state_map = dict()
        for item in line_state_list:
            line_state_map.update({etree_find(item, 'interface-name').text: etree_find(item, 'line-state').text})

        for want_item in self._want:
            want_state = want_item.get('state')
            want_tx_rate = want_item.get('tx_rate')
            want_rx_rate = want_item.get('rx_rate')
            if want_state not in ('up', 'down') and not want_tx_rate and not want_rx_rate:
                continue

            if self._result['changed']:
                sleep(want_item['delay'])

            if want_state in ('up', 'down'):
                if want_state not in line_state_map[want_item['name']]:
                    failed_conditions.append('state ' + 'eq({!s})'.format(want_state))

            if want_tx_rate:
                if want_tx_rate != data_rate_map[want_item['name']]['output-data-rate']:
                    failed_conditions.append('tx_rate ' + want_tx_rate)

            if want_rx_rate:
                if want_rx_rate != data_rate_map[want_item['name']]['input-data-rate']:
                    failed_conditions.append('rx_rate ' + want_rx_rate)

        if failed_conditions:
            msg = 'One or more conditional statements have not been satisfied'
            self._module.fail_json(msg=msg, failed_conditions=failed_conditions)

    def run(self):
        self.map_params_to_obj()
        self.map_obj_to_xml_rpc()
        self.check_declarative_intent_params()
        return self._result


def main():
    """ main entry point for module execution
    """
    element_spec = dict(
        name=dict(type='str'),
        description=dict(type='str'),
        speed=dict(choices=['10', '100', '1000']),
        mtu=dict(),
        duplex=dict(choices=['full', 'half']),
        enabled=dict(default=True, type='bool'),
        active=dict(default='active', type='str', choices=['active', 'preconfigure']),
        tx_rate=dict(),
        rx_rate=dict(),
        delay=dict(default=10, type='int'),
        state=dict(default='present',
                   choices=['present', 'absent', 'up', 'down'])
    )

    aggregate_spec = deepcopy(element_spec)
    aggregate_spec['name'] = dict(required=True)

    # remove default in aggregate spec, to handle common arguments
    remove_default_spec(aggregate_spec)

    argument_spec = dict(
        aggregate=dict(type='list', elements='dict', options=aggregate_spec),
    )

    argument_spec.update(element_spec)
    argument_spec.update(iosxr_argument_spec)

    required_one_of = [['name', 'aggregate']]
    mutually_exclusive = [['name', 'aggregate']]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=required_one_of,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    config_object = None
    if is_cliconf(module):
        module.deprecate("cli support for 'iosxr_interface' is deprecated. Use transport netconf instead",
                         version='4 releases from v2.5')
        config_object = CliConfiguration(module)
    elif is_netconf(module):
        if module.params['active'] == 'preconfigure':
            module.fail_json(msg="Physical interface pre-configuration is not supported with transport 'netconf'")
        config_object = NCConfiguration(module)

    result = {}
    if config_object:
        result = config_object.run()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
