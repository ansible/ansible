#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The iosxr_lacp_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.iosxr.facts.facts import Facts
from ansible.module_utils.network.common.utils import dict_diff, remove_empties
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.utils import search_obj_in_list
from ansible.module_utils.network.iosxr.utils.utils import dict_delete, pad_commands, flatten_dict


class Lacp_interfaces(ConfigBase):
    """
    The iosxr_lacp_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'lacp_interfaces',
    ]

    def __init__(self, module):
        super(Lacp_interfaces, self).__init__(module)

    def get_lacp_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        lacp_interfaces_facts = facts['ansible_network_resources'].get('lacp_interfaces')
        if not lacp_interfaces_facts:
            return []
        return lacp_interfaces_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()

        existing_lacp_interfaces_facts = self.get_lacp_interfaces_facts()
        commands.extend(self.set_config(existing_lacp_interfaces_facts))
        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        changed_lacp_interfaces_facts = self.get_lacp_interfaces_facts()

        result['before'] = existing_lacp_interfaces_facts
        if result['changed']:
            result['after'] = changed_lacp_interfaces_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_lacp_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_lacp_interfaces_facts
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
        commands = []
        state = self._module.params['state']

        if state in ('overridden', 'merged', 'replaced') and not want:
            self._module.fail_json(msg='value of config parameter must not be empty for state {0}'.format(state))

        if state == 'overridden':
            commands.extend(
                Lacp_interfaces._state_overridden(
                    want, have
                )
            )

        elif state == 'deleted':
            if not want:
                for intf in have:
                    commands.extend(
                        Lacp_interfaces._state_deleted(
                            {'name': intf['name']},
                            intf
                        )
                    )
            else:
                for item in want:
                    obj_in_have = search_obj_in_list(item['name'], have)
                    commands.extend(
                        Lacp_interfaces._state_deleted(
                            item, obj_in_have
                        )
                    )

        else:
            for item in want:
                name = item['name']
                obj_in_have = search_obj_in_list(name, have)

                if state == 'merged':
                    commands.extend(
                        Lacp_interfaces._state_merged(
                            item, obj_in_have
                        )
                    )

                elif state == 'replaced':
                    commands.extend(
                        Lacp_interfaces._state_replaced(
                            item, obj_in_have
                        )
                    )

        return commands

    @staticmethod
    def _state_replaced(want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        replaced_commands = []
        merged_commands = []

        if have:
            replaced_commands = Lacp_interfaces._state_deleted(want, have)

        merged_commands = Lacp_interfaces._state_merged(want, have)

        if merged_commands and replaced_commands:
            del merged_commands[0]

        commands.extend(replaced_commands)
        commands.extend(merged_commands)

        return commands

    @staticmethod
    def _state_overridden(want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        for intf in have:
            intf_in_want = search_obj_in_list(intf['name'], want)
            if not intf_in_want:
                commands.extend(Lacp_interfaces._state_deleted({'name': intf['name']}, intf))

        for intf in want:
            intf_in_have = search_obj_in_list(intf['name'], have)
            commands.extend(Lacp_interfaces._state_replaced(intf, intf_in_have))

        return commands

    @staticmethod
    def _state_merged(want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []

        if not have:
            have = {'name': want['name']}

        for key, value in iteritems(flatten_dict(remove_empties(dict_diff(have, want)))):
            commands.append(Lacp_interfaces._compute_commands(key, value))

        if commands:
            pad_commands(commands, want['name'])

        return commands

    @staticmethod
    def _state_deleted(want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []

        for key, value in iteritems(flatten_dict(dict_delete(have, remove_empties(want)))):
            commands.append(Lacp_interfaces._compute_commands(key, value, remove=True))

        if commands:
            pad_commands(commands, have['name'])

        return commands

    @staticmethod
    def _compute_commands(key, value, remove=False):
        if key == "churn_logging":
            cmd = "lacp churn logging {0}".format(value)

        elif key == "collector_max_delay":
            cmd = "lacp collector-max-delay {0}".format(value)

        elif key == "period":
            cmd = "lacp period {0}".format(value)

        elif key == "switchover_suppress_flaps":
            cmd = "lacp switchover suppress-flaps {0}".format(value)

        elif key == 'mac':
            cmd = "lacp system mac {0}".format(value)

        elif key == 'priority':
            cmd = "lacp system priority {0}".format(value)

        if remove:
            cmd = "no " + cmd

        return cmd
