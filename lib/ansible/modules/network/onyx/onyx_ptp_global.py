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
module: onyx_ptp_global
version_added: "2.8"
author: "Anas Badaha (@anasb)"
short_description: Configures PTP Global parameters
description:
  - This module provides declarative management of PTP Global configuration
    on Mellanox ONYX network devices.
notes:
  - Tested on ONYX 3.6.8130
    ptp and ntp protocols cannot be enabled at the same time
options:
  ptp_state:
    description:
      - PTP state.
    choices: ['enabled', 'disabled']
    default: enabled
  ntp_state:
    description:
      - NTP state.
    choices: ['enabled', 'disabled']
  domain:
    description:
      - "set PTP domain number Range 0-127"
  primary_priority:
    description:
      - "set PTP primary priority Range 0-225"
  secondary_priority:
    description:
      - "set PTP secondary priority Range 0-225"
"""

EXAMPLES = """
- name: configure PTP
  onyx_ptp_global:
    ntp_state: enabled
    ptp_state: disabled
    domain: 127
    primary_priority: 128
    secondary_priority: 128
"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device.
  returned: always
  type: list
  sample:
    - no ntp enable
    - protocol ptp
    - ptp domain 127
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.onyx.onyx import show_cmd
from ansible.module_utils.network.onyx.onyx import BaseOnyxModule


class OnyxPtpGlobalModule(BaseOnyxModule):

    def init_module(self):
        """ initialize module
        """
        element_spec = dict(
            ntp_state=dict(choices=['enabled', 'disabled']),
            ptp_state=dict(choices=['enabled', 'disabled'], default='enabled'),
            domain=dict(type=int),
            primary_priority=dict(type=int),
            secondary_priority=dict(type=int)
        )
        argument_spec = dict()
        argument_spec.update(element_spec)
        self._module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True)

    def get_required_config(self):
        module_params = self._module.params
        self._required_config = dict(module_params)
        self._validate_param_values(self._required_config)

    def _validate_param_values(self, obj, param=None):
        super(OnyxPtpGlobalModule, self).validate_param_values(obj, param)
        if obj['ntp_state'] == 'enabled' and obj['ptp_state'] == 'enabled':
            self._module.fail_json(msg='PTP State and NTP State Can not be enabled at the same time')

    def validate_domain(self, value):
        if value and not 0 <= int(value) <= 127:
            self._module.fail_json(msg='domain must be between 0 and 127')

    def validate_primary_priority(self, value):
        if value and not 0 <= int(value) <= 255:
            self._module.fail_json(msg='Primary Priority must be between 0 and 255')

    def validate_secondary_priority(self, value):
        if value and not 0 <= int(value) <= 255:
            self._module.fail_json(msg='Secondary Priority must be between 0 and 255')

    def _set_ntp_config(self, ntp_config):
        ntp_config = ntp_config[0]
        if not ntp_config:
            return
        ntp_state = ntp_config.get('NTP enabled')
        if ntp_state == "yes":
            self._current_config['ntp_state'] = "enabled"
        else:
            self._current_config['ntp_state'] = "disabled"

    def _set_ptp_config(self, ptp_config):
        if ptp_config is None:
            self._current_config['ptp_state'] = 'disabled'
        else:
            self._current_config['ptp_state'] = 'enabled'
            self._current_config['domain'] = int(ptp_config['Domain'])
            self._current_config['primary_priority'] = int(ptp_config['Priority1'])
            self._current_config['secondary_priority'] = int(ptp_config['Priority2'])

    def _show_ntp_config(self):
        cmd = "show ntp configured"
        return show_cmd(self._module, cmd, json_fmt=True, fail_on_error=False)

    def _show_ptp_config(self):
        cmd = "show ptp clock"
        return show_cmd(self._module, cmd, json_fmt=True, fail_on_error=False)

    def load_current_config(self):
        self._current_config = dict()

        ntp_config = self._show_ntp_config()
        self._set_ntp_config(ntp_config)

        ptp_config = self._show_ptp_config()
        self._set_ptp_config(ptp_config)

    def generate_commands(self):
        ntp_state = self._required_config.get("ntp_state")
        if ntp_state == "enabled":
            self._enable_ntp()
        elif ntp_state == "disabled":
            self._disable_ntp()

        ptp_state = self._required_config.get("ptp_state", "enabled")
        if ptp_state == "enabled":
            self._enable_ptp()
        else:
            self._disable_ptp()

        domain = self._required_config.get("domain")
        if domain is not None:
            curr_domain = self._current_config.get("domain")
            if domain != curr_domain:
                self._commands.append('ptp domain %d' % domain)

        primary_priority = self._required_config.get("primary_priority")
        if primary_priority is not None:
            curr_primary_priority = self._current_config.get("primary_priority")
            if primary_priority != curr_primary_priority:
                self._commands.append('ptp priority1 %d' % primary_priority)

        secondary_priority = self._required_config.get("secondary_priority")
        if secondary_priority is not None:
            curr_secondary_priority = self._current_config.get("secondary_priority")
            if secondary_priority != curr_secondary_priority:
                self._commands.append('ptp priority2 %d' % secondary_priority)

    def _enable_ptp(self):
        curr_ptp_state = self._current_config['ptp_state']
        if curr_ptp_state == 'disabled':
            self._commands.append('protocol ptp')

    def _disable_ptp(self):
        curr_ptp_state = self._current_config['ptp_state']
        if curr_ptp_state == 'enabled':
            self._commands.append('no protocol ptp')

    def _enable_ntp(self):
        curr_ntp_state = self._current_config.get('ntp_state')
        if curr_ntp_state == 'disabled':
            self._commands.append('ntp enable')

    def _disable_ntp(self):
        curr_ntp_state = self._current_config['ntp_state']
        if curr_ntp_state == 'enabled':
            self._commands.append('no ntp enable')


def main():
    """ main entry point for module execution
    """
    OnyxPtpGlobalModule.main()


if __name__ == '__main__':
    main()
