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
module: onyx_igmp
version_added: "2.7"
author: "Samer Deeb (@samerd)"
short_description: Configures IGMP globl parameters
description:
  - This module provides declarative management of IGMP protocol params
    on Mellanox ONYX network devices.
notes:
  - Tested on ONYX 3.6.6107
options:
  state:
    description:
      - IGMP state.
    required: true
    choices: ['enabled', 'disabled']
  last_member_query_interval:
    description:
      - Configure the last member query interval, range 1-25
  mrouter_timeout:
    description:
      - Configure the mrouter timeout, range 60-600
  port_purge_timeout:
    description:
      - Configure the host port purge timeout, range 130-1225
  proxy_reporting:
    description:
      - Configure ip igmp snooping proxy and enable reporting mode
    choices: ['enabled', 'disabled']
  report_suppression_interval:
    description:
      - Configure the report suppression interval, range 1-25
  unregistered_multicast:
    description:
      - Configure the unregistered multicast mode
        Flood unregistered multicast
        Forward unregistered multicast to mrouter ports
    choices: ['flood', 'forward-to-mrouter-ports']
  default_version:
    description:
      - Configure the default operating version of the IGMP snooping
    choices: ['V2','V3']
"""

EXAMPLES = """
- name: configure igmp
  onyx_igmp:
    state: enabled
    unregistered_multicast: flood
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - ip igmp snooping
    - ip igmp snooping last-member-query-interval 10
    - ip igmp snooping mrouter-timeout 150
    - ip igmp snooping port-purge-timeout 150
"""

import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems

from ansible.module_utils.network.onyx.onyx import show_cmd
from ansible.module_utils.network.onyx.onyx import BaseOnyxModule


class OnyxIgmpModule(BaseOnyxModule):
    TIME_INTERVAL_REGEX = re.compile(r'^(\d+)\s+seconds')

    _RANGE_INTERVALS = dict(
        last_member_query_interval=(1, 25, 'Last member query interval'),
        mrouter_timeout=(60, 600, 'Mrouter timeout'),
        port_purge_timeout=(130, 1225, 'Port purge timeout'),
        report_suppression_interval=(1, 25, 'Report suppression interval'),
    )

    def init_module(self):
        """ initialize module
        """
        element_spec = dict(
            state=dict(choices=['enabled', 'disabled'], required=True),
            last_member_query_interval=dict(type='int'),
            mrouter_timeout=dict(type='int'),
            port_purge_timeout=dict(type='int'),
            proxy_reporting=dict(choices=['enabled', 'disabled']),
            report_suppression_interval=dict(type='int'),
            unregistered_multicast=dict(
                choices=['flood', 'forward-to-mrouter-ports']),
            default_version=dict(choices=['V2', 'V3']),
        )
        argument_spec = dict()
        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True)

    def _validate_key(self, param, key):
        interval_params = self._RANGE_VALIDATORS.get(key)
        if interval_params:
            min_val, max_val = interval_params[0], interval_params[1]
            value = param.get(key)
            self._validate_range(key, min_val, max_val, value)
        else:
            super(OnyxIgmpModule, self)._validate_key(param, key)

    def get_required_config(self):
        module_params = self._module.params
        self._required_config = dict(module_params)
        self.validate_param_values(self._required_config)

    def _set_igmp_config(self, igmp_config):
        igmp_config = igmp_config[0]
        if not igmp_config:
            return
        self._current_config['state'] = igmp_config.get(
            'IGMP snooping globally', 'disabled')
        self._current_config['proxy_reporting'] = igmp_config.get(
            'Proxy-reporting globally', 'disabled')
        self._current_config['default_version'] = igmp_config.get(
            'IGMP default version for new VLAN', 'V3')
        self._current_config['unregistered_multicast'] = igmp_config.get(
            'IGMP snooping unregistered multicast', 'flood')

        for interval_name, interval_params in iteritems(self._RANGE_INTERVALS):
            display_str = interval_params[2]
            value = igmp_config.get(display_str, '')
            match = self.TIME_INTERVAL_REGEX.match(value)
            if match:
                interval_value = int(match.group(1))
            else:
                interval_value = None
            self._current_config[interval_name] = interval_value

    def _show_igmp(self):
        cmd = "show ip igmp snooping"
        return show_cmd(self._module, cmd, json_fmt=True, fail_on_error=False)

    def load_current_config(self):
        self._current_config = dict()
        igmp_config = self._show_igmp()
        if igmp_config:
            self._set_igmp_config(igmp_config)

    def generate_commands(self):
        state = self._required_config['state']
        if state == 'enabled':
            self._generate_igmp_cmds()
        else:
            self._generate_no_igmp_cmds()

    def _generate_igmp_cmds(self):
        curr_state = self._current_config.get('state', 'disabled')
        if curr_state == 'disabled':
            self._commands.append('ip igmp snooping')
        for interval_name in self._RANGE_INTERVALS:
            req_val = self._required_config.get(interval_name)
            if not req_val:
                continue
            curr_value = self._current_config.get(interval_name)
            if curr_value == req_val:
                continue
            interval_cmd = interval_name.replace('_', '-')
            self._commands.append(
                'ip igmp snooping %s %s' % (interval_cmd, req_val))

        req_val = self._required_config.get('unregistered_multicast')
        if req_val:
            curr_value = self._current_config.get(
                'unregistered_multicast', 'flood')
            if req_val != curr_value:
                self._commands.append(
                    'ip igmp snooping unregistered multicast %s' % req_val)

        req_val = self._required_config.get('proxy_reporting')
        if req_val:
            curr_value = self._current_config.get(
                'proxy_reporting', 'disabled')
            if req_val != curr_value:
                cmd = 'ip igmp snooping proxy reporting'
                if req_val == 'disabled':
                    cmd = 'no %s' % cmd
                self._commands.append(cmd)

        req_val = self._required_config.get('default_version')
        if req_val:
            curr_value = self._current_config.get(
                'default_version', 'V3')
            if req_val != curr_value:
                version = req_val[1]  # remove the 'V' and take the number only
                self._commands.append(
                    'ip igmp snooping version %s' % version)

    def _generate_no_igmp_cmds(self):
        curr_state = self._current_config.get('state', 'disabled')
        if curr_state != 'disabled':
            self._commands.append('no ip igmp snooping')


def main():
    """ main entry point for module execution
    """
    OnyxIgmpModule.main()


if __name__ == '__main__':
    main()
