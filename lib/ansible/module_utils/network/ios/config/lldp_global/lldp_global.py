#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The ios_lldp_global class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to its desired end-state is
created
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.ios.facts.facts import Facts
from ansible.module_utils.network.ios.utils.utils import dict_to_set
from ansible.module_utils.network.ios.utils.utils import filter_dict_having_none_value


class Lldp_global(ConfigBase):
    """
    The ios_lldp_global class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'lldp_global',
    ]

    tlv_select_params = {'four_wire_power_management': '4-wire-power-management', 'mac_phy_cfg': 'mac-phy-cfg',
                         'management_address': 'management-address', 'port_description': 'port-description',
                         'port_vlan': 'port-vlan', 'power_management': 'power-management',
                         'system_capabilities': 'system-capabilities', 'system_description': 'system-description',
                         'system_name': 'system-name'}

    def __init__(self, module):
        super(Lldp_global, self).__init__(module)

    def get_lldp_global_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        lldp_global_facts = facts['ansible_network_resources'].get('lldp_global')
        if not lldp_global_facts:
            return {}

        return lldp_global_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from moduel execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()

        existing_lldp_global_facts = self.get_lldp_global_facts()
        commands.extend(self.set_config(existing_lldp_global_facts))

        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        changed_lldp_global_facts = self.get_lldp_global_facts()

        result['before'] = existing_lldp_global_facts
        if result['changed']:
            result['after'] = changed_lldp_global_facts
        result['warnings'] = warnings

        return result

    def set_config(self, existing_lldp_global_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the deisred configuration
        """
        want = self._module.params['config']
        have = existing_lldp_global_facts
        resp = self.set_state(want, have)
        return to_list(resp)

    def set_state(self, want, have):
        """ Select the appropriate function based on the state provided

        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the deisred configuration
        """
        commands = []
        state = self._module.params['state']
        if state in ('merged', 'replaced') and not want:
            self._module.fail_json(msg='value of config parameter must not be empty for state {0}'.format(state))

        if state == 'overridden':
            commands = self._state_overridden(want, have)
        elif state == 'deleted':
            commands = self._state_deleted(want, have)
        elif state == 'merged':
            commands = self._state_merged(want, have)
        elif state == 'replaced':
            commands = self._state_replaced(want, have)

        return commands

    def _state_replaced(self, want, have):
        """ The command generator when state is replaced

        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :param interface_type: interface type
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the deisred configuration
        """
        commands = []

        have_dict = filter_dict_having_none_value(want, have)
        commands.extend(self._clear_config(have_dict))
        commands.extend(self._set_config(want, have))

        return commands

    def _state_merged(self, want, have):
        """ The command generator when state is merged

        :param want: the additive configuration as a dictionary
        :param obj_in_have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []

        commands.extend(self._set_config(want, have))

        return commands

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted

        :param want: the objects from which the configuration should be removed
        :param obj_in_have: the current configuration as a dictionary
        :param interface_type: interface type
        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []

        commands.extend(self._clear_config(have))

        return commands

    def _remove_command_from_config_list(self, cmd, commands):
        if cmd not in commands:
            commands.append('no %s' % cmd)

    def add_command_to_config_list(self, cmd, commands):
        if cmd not in commands:
            commands.append(cmd)

    def _set_config(self, want, have):
        # Set the interface config based on the want and have config
        commands = []

        # Get the diff b/w want and have
        want_dict = dict_to_set(want)
        have_dict = dict_to_set(have)
        diff = want_dict - have_dict

        if diff:
            diff = dict(diff)
            holdtime = diff.get('holdtime')
            enabled = diff.get('enabled')
            timer = diff.get('timer')
            reinit = diff.get('reinit')
            tlv_select = diff.get('tlv_select')

            if holdtime:
                cmd = 'lldp holdtime {0}'.format(holdtime)
                self.add_command_to_config_list(cmd, commands)
            if enabled:
                cmd = 'lldp run'
                self.add_command_to_config_list(cmd, commands)
            if timer:
                cmd = 'lldp timer {0}'.format(timer)
                self.add_command_to_config_list(cmd, commands)
            if reinit:
                cmd = 'lldp reinit {0}'.format(reinit)
                self.add_command_to_config_list(cmd, commands)
            if tlv_select:
                tlv_selec_dict = dict(tlv_select)
                for k, v in iteritems(self.tlv_select_params):
                    if k in tlv_selec_dict and tlv_selec_dict[k]:
                        cmd = 'lldp tlv-select {0}'.format(v)
                        self.add_command_to_config_list(cmd, commands)

        return commands

    def _clear_config(self, have):
        # Delete the interface config based on the want and have config
        commands = []

        if have.get('holdtime'):
            cmd = 'lldp holdtime'
            self._remove_command_from_config_list(cmd, commands)
        if have.get('enabled'):
            cmd = 'lldp run'
            self._remove_command_from_config_list(cmd, commands)
        if have.get('timer'):
            cmd = 'lldp timer'
            self._remove_command_from_config_list(cmd, commands)
        if have.get('reinit'):
            cmd = 'lldp reinit'
            self._remove_command_from_config_list(cmd, commands)

        return commands
