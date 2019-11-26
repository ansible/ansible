#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The iosxr_lldp_global class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list, dict_diff, remove_empties
from ansible.module_utils.network.iosxr.facts.facts import Facts
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.iosxr. \
    utils.utils import flatten_dict, dict_delete


class Lldp_global(ConfigBase):
    """
    The iosxr_lldp class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'lldp_global',
    ]

    def __init__(self, module):
        super(Lldp_global, self).__init__(module)

    def get_lldp_global_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        lldp_facts = facts['ansible_network_resources'].get('lldp_global')
        if not lldp_facts:
            return {}
        return lldp_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()

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
                  to the desired configuration
        """
        want = self._module.params['config']
        if not want and self._module.params['state'] == 'deleted':
            want = {}
        have = existing_lldp_global_facts
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
        if state in ('merged', 'replaced') and not want:
            self._module.fail_json(msg='value of config parameter must not be empty for state {0}'.format(state))

        if state == 'deleted':
            commands = self._state_deleted(want, have)
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

        commands.extend(
            self._state_deleted(want, have)
        )

        commands.extend(
            self._state_merged(want, have)
        )

        return commands

    def _state_merged(self, want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        updates = dict_diff(have, want)
        if updates:
            for key, value in iteritems(flatten_dict(remove_empties(updates))):
                commands.append(self._compute_commands(key, value))

        return commands

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        for key, value in iteritems(flatten_dict(dict_delete(have, remove_empties(want)))):
            cmd = self._compute_commands(key, value, remove=True)
            if cmd:
                commands.append(cmd)

        return commands

    def _compute_commands(self, key, value=None, remove=False):
        if key in ['holdtime', 'reinit', 'timer']:
            cmd = 'lldp {0} {1}'.format(key, value)
            if remove:
                return 'no {0}'.format(cmd)
            else:
                return cmd

        elif key == 'subinterfaces':
            cmd = 'lldp subinterfaces enable'
            if (value and not remove):
                return cmd
            elif (not value and not remove) or (value and remove):
                return 'no {0}'.format(cmd)

        else:
            cmd = 'lldp tlv-select {0} disable'.format(key.replace('_', '-'))
            if (not value and not remove):
                return cmd
            elif (value and not remove) or (not value and remove):
                return 'no {0}'.format(cmd)
