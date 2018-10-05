#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: onyx_linkagg
version_added: "2.5"
author: "Samer Deeb (@samerd)"
short_description: Manage link aggregation groups on Mellanox ONYX network devices
description:
  - This module provides declarative management of link aggregation groups
    on Mellanox ONYX network devices.
options:
  name:
    description:
      - Name of the link aggregation group.
    required: true
  mode:
    description:
      - Mode of the link aggregation group. A value of C(on) will enable LACP.
        C(active) configures the link to actively information about the state of the link,
        or it can be configured in C(passive) mode ie. send link state information only when
        received them from another link.
    default: on
    choices: ['on', 'active', 'passive']
  members:
    description:
      - List of members interfaces of the link aggregation group. The value can be
        single interface or list of interfaces.
    required: true
  aggregate:
    description: List of link aggregation definitions.
  purge:
    description:
      - Purge link aggregation groups not defined in the I(aggregate) parameter.
    default: false
    type: bool
  state:
    description:
      - State of the link aggregation group.
    default: present
    choices: ['present', 'absent', 'up', 'down']
"""

EXAMPLES = """
- name: configure link aggregation group
  onyx_linkagg:
    name: Po1
    members:
      - Eth1/1
      - Eth1/2

- name: remove configuration
  onyx_linkagg:
    name: Po1
    state: absent

- name: Create aggregate of linkagg definitions
  onyx_linkagg:
    aggregate:
        - { name: Po1, members: [Eth1/1] }
        - { name: Po2, members: [Eth1/2] }

- name: Remove aggregate of linkagg definitions
  onyx_linkagg:
    aggregate:
      - name: Po1
      - name: Po2
    state: absent
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always.
  type: list
  sample:
    - interface port-channel 1
    - exit
    - interface ethernet 1/1 channel-group 1 mode on
    - interface ethernet 1/2 channel-group 1 mode on
"""

import re
from copy import deepcopy

from ansible.module_utils.network.common.utils import remove_default_spec
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems

from ansible.module_utils.network.onyx.onyx import BaseOnyxModule
from ansible.module_utils.network.onyx.onyx import get_interfaces_config


class OnyxLinkAggModule(BaseOnyxModule):
    LAG_ID_REGEX = re.compile(r"^\d+ (Po\d+|Mpo\d+)\(([A-Z])\)$")
    LAG_NAME_REGEX = re.compile(r"^(Po|Mpo)(\d+)$")
    IF_NAME_REGEX = re.compile(r"^(Eth\d+\/\d+|Eth\d+\/\d+\/\d+)(.*)$")
    PORT_CHANNEL = 'port-channel'
    CHANNEL_GROUP = 'channel-group'
    MLAG_PORT_CHANNEL = 'mlag-port-channel'
    MLAG_CHANNEL_GROUP = 'mlag-channel-group'
    MLAG_SUMMARY = 'MLAG Port-Channel Summary'

    LAG_TYPE = 'lag'
    MLAG_TYPE = 'mlag'

    IF_TYPE_MAP = dict(
        lag=PORT_CHANNEL,
        mlag=MLAG_PORT_CHANNEL
    )

    _purge = False

    @classmethod
    def _get_element_spec(cls):
        return dict(
            name=dict(type='str'),
            members=dict(type='list'),
            mode=dict(default='on', choices=['active', 'on', 'passive']),
            state=dict(default='present', choices=['present', 'absent']),
        )

    @classmethod
    def _get_aggregate_spec(cls, element_spec):
        aggregate_spec = deepcopy(element_spec)
        aggregate_spec['name'] = dict(required=True)

        # remove default in aggregate spec, to handle common arguments
        remove_default_spec(aggregate_spec)
        return aggregate_spec

    def init_module(self):
        """ module initialization
        """
        element_spec = self._get_element_spec()
        aggregate_spec = self._get_aggregate_spec(element_spec)
        argument_spec = dict(
            aggregate=dict(type='list', elements='dict',
                           options=aggregate_spec),
            purge=dict(default=False, type='bool'),
        )
        argument_spec.update(element_spec)
        required_one_of = [['name', 'aggregate']]
        mutually_exclusive = [['name', 'aggregate']]
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            required_one_of=required_one_of,
            mutually_exclusive=mutually_exclusive,
            supports_check_mode=True)

    def _get_lag_type(self, lag_name):
        match = self.LAG_NAME_REGEX.match(lag_name)
        if match:
            prefix = match.group(1)
            if prefix == "Po":
                return self.LAG_TYPE
            return self.MLAG_TYPE
        self._module.fail_json(
            msg='invalid lag name: %s, lag name should start with Po or '
            'Mpo' % lag_name)

    def get_required_config(self):
        self._required_config = list()
        module_params = self._module.params
        aggregate = module_params.get('aggregate')
        self._purge = module_params.get('purge', False)
        if aggregate:
            for item in aggregate:
                for key in item:
                    if item.get(key) is None:
                        item[key] = module_params[key]
                self.validate_param_values(item, item)
                req_item = item.copy()
                req_item['type'] = self._get_lag_type(req_item['name'])
                self._required_config.append(req_item)
        else:
            params = {
                'name': module_params['name'],
                'state': module_params['state'],
                'members': module_params['members'],
                'mode': module_params['mode'],
                'type': self._get_lag_type(module_params['name']),
            }
            self.validate_param_values(params)
            self._required_config.append(params)

    @classmethod
    def _extract_lag_name(cls, header):
        match = cls.LAG_ID_REGEX.match(header)
        state = None
        lag_name = None
        if match:
            state = 'up' if match.group(2) == 'U' else 'down'
            lag_name = match.group(1)
        return lag_name, state

    @classmethod
    def _extract_if_name(cls, member):
        match = cls.IF_NAME_REGEX.match(member)
        if match:
            return match.group(1)

    @classmethod
    def _extract_lag_members(cls, lag_type, lag_item):
        members = ""
        if lag_type == cls.LAG_TYPE:
            members = cls.get_config_attr(lag_item, "Member Ports")
        else:
            for attr_name, attr_val in iteritems(lag_item):
                if attr_name.startswith('Local Ports'):
                    members = attr_val
        return [cls._extract_if_name(member) for member in members.split()]

    def _get_port_channels(self, if_type):
        return get_interfaces_config(self._module, if_type, flags="summary")

    def _parse_port_channels_summary(self, lag_type, lag_summary):
        if lag_type == self.MLAG_TYPE:
            if self._os_version >= self.ONYX_API_VERSION:
                found_summary = False
                for summary_item in lag_summary:
                    if self.MLAG_SUMMARY in summary_item:
                        lag_summary = summary_item[self.MLAG_SUMMARY]
                        if lag_summary:
                            lag_summary = lag_summary[0]
                        else:
                            lag_summary = dict()
                        found_summary = True
                        break
                if not found_summary:
                    lag_summary = dict()
            else:
                lag_summary = lag_summary.get(self.MLAG_SUMMARY, dict())
        for lag_key, lag_data in iteritems(lag_summary):
            lag_name, state = self._extract_lag_name(lag_key)
            if not lag_name:
                continue
            lag_members = self._extract_lag_members(lag_type, lag_data[0])
            lag_obj = dict(
                name=lag_name,
                state=state,
                members=lag_members
            )
            self._current_config[lag_name] = lag_obj

    def load_current_config(self):
        self._current_config = dict()
        self._os_version = self._get_os_version()
        lag_types = set([lag_obj['type'] for lag_obj in self._required_config])
        for lag_type in lag_types:
            if_type = self.IF_TYPE_MAP[lag_type]
            lag_summary = self._get_port_channels(if_type)
            if lag_summary:
                self._parse_port_channels_summary(lag_type, lag_summary)

    def _get_interface_command_suffix(self, if_name):
        if if_name.startswith('Eth'):
            return if_name.replace("Eth", "ethernet ")
        if if_name.startswith('Po'):
            return if_name.replace("Po", "port-channel ")
        if if_name.startswith('Mpo'):
            return if_name.replace("Mpo", "mlag-port-channel ")
        self._module.fail_json(
            msg='invalid interface name: %s' % if_name)

    def _get_channel_group(self, if_name):
        if if_name.startswith('Po'):
            return if_name.replace("Po", "channel-group ")
        if if_name.startswith('Mpo'):
            return if_name.replace("Mpo", "mlag-channel-group ")
        self._module.fail_json(
            msg='invalid interface name: %s' % if_name)

    def _generate_no_linkagg_commands(self, lag_name):
        suffix = self._get_interface_command_suffix(lag_name)
        command = 'no interface %s' % suffix
        self._commands.append(command)

    def _generate_linkagg_commands(self, lag_name, req_lag):
        curr_lag = self._current_config.get(lag_name, {})
        if not curr_lag:
            suffix = self._get_interface_command_suffix(lag_name)
            self._commands.append("interface %s" % suffix)
            self._commands.append("exit")
        curr_members = set(curr_lag.get('members', []))
        req_members = set(req_lag.get('members') or [])

        lag_mode = req_lag['mode']
        if req_members != curr_members:
            channel_group = self._get_channel_group(lag_name)
            channel_group_type = channel_group.split()[0]
            for member in req_members:
                if member in curr_members:
                    continue
                suffix = self._get_interface_command_suffix(member)
                self._commands.append(
                    "interface %s %s mode %s" %
                    (suffix, channel_group, lag_mode))
            for member in curr_members:
                if member in req_members:
                    continue
                suffix = self._get_interface_command_suffix(member)
                self._commands.append(
                    "interface %s no %s" % (suffix, channel_group_type))
        req_state = req_lag.get('state')
        if req_state in ('up', 'down'):
            curr_state = curr_lag.get('state')
            if curr_state != req_state:
                suffix = self._get_interface_command_suffix(lag_name)
                cmd = "interface %s " % suffix
                if req_state == 'up':
                    cmd += 'no shutdown'
                else:
                    cmd += 'shutdown'
                self._commands.append(cmd)

    def generate_commands(self):
        req_lags = set()
        for req_conf in self._required_config:
            state = req_conf['state']
            lag_name = req_conf['name']
            if state == 'absent':
                if lag_name in self._current_config:
                    self._generate_no_linkagg_commands(lag_name)
            else:
                req_lags.add(lag_name)
                self._generate_linkagg_commands(lag_name, req_conf)
        if self._purge:
            for lag_name in self._current_config:
                if lag_name not in req_lags:
                    self._generate_no_linkagg_commands(lag_name)

    def check_declarative_intent_params(self, result):
        pass


def main():
    """ main entry point for module execution
    """
    OnyxLinkAggModule.main()


if __name__ == '__main__':
    main()
