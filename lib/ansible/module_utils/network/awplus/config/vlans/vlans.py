#
# -*- coding: utf-8 -*-
# Copyright 2020 Allied Telesis
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The awplus_vlans class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.awplus.facts.facts import Facts
from ansible.module_utils.network.ios.utils.utils import dict_to_set


class Vlans(ConfigBase):
    """
    The awplus_vlans class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'vlans',
    ]

    def __init__(self, module):
        super(Vlans, self).__init__(module)

    def get_vlans_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(
            self.gather_subset, self.gather_network_resources)
        vlans_facts = facts['ansible_network_resources'].get('vlans')
        if not vlans_facts:
            return []
        return vlans_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()

        existing_vlans_facts = self.get_vlans_facts()
        commands.extend(self.set_config(existing_vlans_facts))
        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        changed_vlans_facts = self.get_vlans_facts()

        result['before'] = existing_vlans_facts
        if result['changed']:
            result['after'] = changed_vlans_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_vlans_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_vlans_facts
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
            self._module.fail_json(
                msg='value of config parameter must not be empty for state {0}'.format(state))

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
                if every.get('vlan_id') == each.get('vlan_id'):
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
        for each in want:
            for every in have:
                if each.get('vlan_id') == every.get('vlan_id'):
                    check = True
                    break
                else:
                    continue
            if check:
                commands.extend(self._set_config(each, every))
            else:
                commands.extend(self._set_config(each, dict()))

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

    def _set_config(self, want, have):
        # Set the interface config based on the want and have config
        commands = []
        vlan_id = want.get('vlan_id')

        # Get the diff b/w want n have
        want_dict = dict_to_set(want)
        have_dict = dict_to_set(have)
        diff = want_dict - have_dict

        if diff:
            commands.append('vlan database')
            name = dict(diff).get('name')
            state = dict(diff).get('state')
            if name:
                cmd = 'vlan {0} name {1}'.format(vlan_id, name)
                commands.append(cmd)
            if state:
                cmd = 'vlan {0} state {1}'.format(vlan_id, state)
                commands.append(cmd)

        return commands

    def _clear_config(self, want, have, state):
        # Delete the interface config based on the want and have config
        commands = []
        vlan_id = have.get('vlan_id')

        if have.get('vlan_id') and 'default' not in have.get('name')\
                and (have.get('vlan_id') != want.get('vlan_id') or state == 'deleted'):
            commands.append('vlan database')
            commands.append('no vlan {0}'.format(vlan_id))
        elif 'default' not in have.get('name'):
            if have.get('state') != want.get('state') and want.get('state'):
                commands.append('vlan database')
                commands.append('vlan {0} state {1}'.format(vlan_id, want.get('state')))
        return commands
