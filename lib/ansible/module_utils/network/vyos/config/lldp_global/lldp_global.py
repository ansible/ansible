# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vyos_lldp_global class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list, dict_diff
from ansible.module_utils.network.vyos.facts.facts import Facts
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.vyos.utils.utils import get_lst_diff_for_dicts, list_diff_have_only


class Lldp_global(ConfigBase):
    """
    The vyos_lldp_global class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'lldp_global',
    ]

    params = ['enable', 'address', 'snmp', 'legacy_protocols']

    def __init__(self, module):
        super(Lldp_global, self).__init__(module)

    def get_lldp_global_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset,
                                                         self.gather_network_resources)
        lldp_global_facts = facts['ansible_network_resources'].get('lldp_global')
        if not lldp_global_facts:
            return {}
        return lldp_global_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
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
                  to the desired configuration
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
                  to the desired configuration
        """
        commands = []
        state = self._module.params['state']
        if state in ('merged', 'replaced') and not want:
            self._module.fail_json(msg='config is required for state {0}'.format(state))
        if state == 'deleted':
            commands.extend(self._state_deleted(want=None, have=have))
        elif state == 'merged':
            commands.extend(self._state_merged(want=want, have=have))
        elif state == 'replaced':
            commands.extend(self._state_replaced(want=want, have=have))
        return commands

    def _state_replaced(self, want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        if have:
            commands.extend(self._state_deleted(want, have))
        commands.extend(self._state_merged(want, have))
        return commands

    def _state_merged(self, want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        commands.extend(self._render_updates(want, have))
        return commands

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        if want:
            for item in Lldp_global.params:
                if item == 'legacy_protocols':
                    commands.extend(self._update_lldp_protocols(want, have))
                elif have.get(item) and not want.get(item) and item != 'enable':
                    commands.append(Lldp_global.del_cmd + item)
        elif have:
            for item in Lldp_global.params:
                if have.get(item):
                    if item == 'legacy_protocols':
                        commands.append(
                            self._compute_command('legacy-protocols', remove=True)
                        )
                    elif item == 'address':
                        commands.append(
                            self._compute_command('management-address', remove=True)
                        )
                    elif item == 'snmp':
                        commands.append(
                            self._compute_command(item, remove=True)
                        )

        return commands

    def _render_updates(self, want, have):
        commands = []
        if have:
            temp_have_legacy_protos = have.pop('legacy_protocols', None)
        else:
            have = {}
            temp_want_legacy_protos = want.pop('legacy_protocols', None)

        updates = dict_diff(have, want)

        if have and temp_have_legacy_protos:
            have['legacy_protocols'] = temp_have_legacy_protos
        if not have and temp_want_legacy_protos:
            want['legacy_protocols'] = temp_want_legacy_protos

        commands.extend(self._add_lldp_protocols(want, have))

        if updates:
            for key, value in iteritems(updates):
                if value:
                    if key == 'enable':
                        commands.append(
                            self._compute_command()
                        )
                    elif key == 'address':
                        commands.append(
                            self._compute_command('management-address', str(value))
                        )
                    elif key == 'snmp':
                        if value == 'disable':
                            commands.append(
                                self._compute_command(key, remove=True)
                            )
                        else:
                            commands.append(
                                self._compute_command(key, str(value))
                            )
        return commands

    def _add_lldp_protocols(self, want, have):
        commands = []
        diff_members = get_lst_diff_for_dicts(want, have, 'legacy_protocols')
        for key in diff_members:
            commands.append(
                self._compute_command('legacy-protocols', key)
            )
        return commands

    def _update_lldp_protocols(self, want_item, have_item):
        commands = []
        want_protocols = want_item.get('legacy_protocols') or []
        have_protocols = have_item.get('legacy_protocols') or []

        members_diff = list_diff_have_only(want_protocols, have_protocols)
        if members_diff:
            for member in members_diff:
                commands.append(
                    self._compute_command('legacy-protocols', member, remove=True)
                )
        return commands

    def _compute_command(self, key=None, value=None, remove=False):
        if remove:
            cmd = 'delete service lldp'
        else:
            cmd = 'set service lldp'
        if key:
            cmd += (' ' + key)

        if value:
            cmd += (" '" + value + "'")
        return cmd
