#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The ios_static_routes class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.ios.facts.facts import Facts
from ansible.module_utils.network.ios.utils.utils import dict_to_set
import q

class Static_Routes(ConfigBase):
    """
    The ios_static_routes class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'static_routes',
    ]

    def __init__(self, module):
        super(Static_Routes, self).__init__(module)

    def get_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        interfaces_facts = facts['ansible_network_resources'].get('static_routes')
        if not interfaces_facts:
            return []
        return interfaces_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()

        existing_interfaces_facts = self.get_interfaces_facts()
        commands.extend(self.set_config(existing_interfaces_facts))
        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        changed_interfaces_facts = self.get_interfaces_facts()

        result['before'] = existing_interfaces_facts
        if result['changed']:
            result['after'] = changed_interfaces_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_interfaces_facts
        resp = self.set_state(want, have)
        return to_list(resp)

    def set_state(self, want, have):
        """ Select the appropriate function based on the state provided

        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        state = self._module.params['state']
        if state in ('overridden', 'merged', 'replaced') and not want:
            self._module.fail_json(msg='value of config parameter must not be empty for state {0}'.format(state))

        if state == 'overridden':
            commands = self._state_overridden(want, have, state)
        elif state == 'deleted':
            commands = self._state_deleted(want, have, state)
        elif state == 'merged':
            commands = self._state_merged(want, have)
        elif state == 'replaced':
            commands = self._state_replaced(want, have)
        return commands

    def _state_replaced(self, want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []

        check = False
        for each in want:
            for every in have:
                if every['vlan_id'] == each['vlan_id']:
                    check = True
                    break
            else:
                continue
            if check:
                commands.extend(self._set_config(each, every))
            else:
                commands.extend(self._set_config(each, dict()))

        return commands

    def _state_overridden(self, want, have, state):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []

        want_local = want
        for each in have:
            count = 0
            for every in want_local:
                if each['vlan_id'] == every['vlan_id']:
                    break
                count += 1
            else:
                # We didn't find a matching desired state, which means we can
                # pretend we recieved an empty desired state.
                commands.extend(self._clear_config(every, each, state))
                continue
            commands.extend(self._set_config(every, each))
            # as the pre-existing VLAN are now configured by
            # above set_config call, deleting the respective
            # VLAN entry from the want_local list
            del want_local[count]

        # Iterating through want_local list which now only have new VLANs to be
        # configured
        for each in want_local:
            commands.extend(self._set_config(each, dict()))

        return commands

    def _state_merged(self, want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        check = False
        q(want, have)
        for each in want:
            for every in have:
                if '/' in each['address_families'][0]['routes'][0]['dest']:
                    each_ip = each['address_families'][0]['routes'][0]['dest'].split('/')[0]
                else:
                    each_ip = each['address_families'][0]['routes'][0]['dest'][0]
                if each_ip:
                    if each_ip == every['address_families'][0]['routes'][0]['dest'].split(' ')[0]:
                        check = True
                        break
                    else:
                        continue
                else:
                    if each_ip == every.get('dest').split(' ')[0]:
                        check = True
                        break
                    else:
                        continue
            if check:
                commands.extend(self._set_config(each, every))
            else:
                commands.extend(self._set_config(each, dict()))
        q(commands)
        commands=[]
        return commands

    def _state_deleted(self, want, have, state):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []

        if want:
            check = False
            for each in want:
                for every in have:
                    if each.get('vlan_id') == every.get('vlan_id'):
                        check = True
                        break
                    else:
                        check = False
                        continue
                if check:
                    commands.extend(self._clear_config(each, every, state))
        else:
            for each in have:
                commands.extend(self._clear_config(dict(), each, state))

        return commands

    def remove_command_from_config_list(self, vlan, cmd, commands):
        if vlan not in commands and cmd != 'vlan':
            commands.insert(0, vlan)
        elif cmd == 'vlan':
            commands.append('no %s' % vlan)
            return commands
        commands.append('no %s' % cmd)
        return commands

    def add_command_to_config_list(self, vlan_id, cmd, commands):
        if vlan_id not in commands:
            commands.insert(0, vlan_id)
        if cmd not in commands:
            commands.append(cmd)

    def _set_config(self, want, have):
        # Set the interface config based on the want and have config
        commands = []

        q(want, have)
        # Get the diff b/w want n have
        # want_dict = dict_to_set(want)
        # have_dict = dict_to_set(have)
        # diff = want_dict - have_dict



        return commands

    def _clear_config(self, want, have, state):
        # Delete the interface config based on the want and have config
        commands = []


        return commands
