#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The iosxr_acl_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.iosxr.facts.facts import Facts
from ansible.module_utils.network.iosxr.utils.utils import normalize_interface, diff_list_of_dicts, pad_commands
from ansible.module_utils.network.common.utils \
    import (
        to_list,
        search_obj_in_list,
        remove_empties
    )


class Acl_interfaces(ConfigBase):
    """
    The iosxr_acl_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'acl_interfaces',
    ]

    def __init__(self, module):
        super(Acl_interfaces, self).__init__(module)

    def get_acl_interfaces_facts(self, data=None):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(
            self.gather_subset, self.gather_network_resources, data=data)
        acl_interfaces_facts = facts['ansible_network_resources'].get(
            'acl_interfaces')
        if not acl_interfaces_facts:
            return []
        return acl_interfaces_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()

        if self.state in self.ACTION_STATES:
            existing_acl_interfaces_facts = self.get_acl_interfaces_facts()
        else:
            existing_acl_interfaces_facts = []

        if self.state in self.ACTION_STATES or self.state == "rendered":
            commands.extend(self.set_config(existing_acl_interfaces_facts))

        if commands and self.state in self.ACTION_STATES:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result["changed"] = True

        if self.state in self.ACTION_STATES:
            result["commands"] = commands

        if self.state in self.ACTION_STATES or self.state == "gathered":
            changed_acl_interfaces_facts = self.get_acl_interfaces_facts()

        elif self.state == "rendered":
            result["rendered"] = commands

        elif self.state == "parsed":
            running_config = self._module.params["running_config"]
            if not running_config:
                self._module.fail_json(msg="value of running_config parameter must not be empty for state parsed")
            result["parsed"] = self.get_acl_interfaces_facts(
                data=running_config)

        if self.state in self.ACTION_STATES:
            result["before"] = existing_acl_interfaces_facts
            if result["changed"]:
                result["after"] = changed_acl_interfaces_facts

        elif self.state == "gathered":
            result["gathered"] = changed_acl_interfaces_facts

        result["warnings"] = warnings
        return result

    def set_config(self, existing_acl_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        if want:
            for item in want:
                item['name'] = normalize_interface(item['name'])
                if 'members' in want and want['members']:
                    for item in want['members']:
                        item.update({
                            'member':
                            normalize_interface(item['member']),
                            'mode':
                            item['mode']
                        })
        have = existing_acl_interfaces_facts
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
        commands = []

        if state in ('overridden', 'merged', 'replaced', 'rendered') and not want:
            self._module.fail_json(msg='value of config parameter must not be empty for state {0}'.format(state))

        if state == 'overridden':
            commands.extend(self._state_overridden(want, have))

        elif state == 'deleted':
            if not want:
                for intf in have:
                    commands.extend(self._state_deleted({}, intf))
            else:
                for item in want:
                    obj_in_have = search_obj_in_list(item['name'], have) or {}
                    commands.extend(
                        self._state_deleted(remove_empties(item), obj_in_have))

        else:
            # Instead of passing entire want and have
            # list of dictionaries to the respective
            # _state_* methods we are passing the want
            # and have dictionaries per interface
            for item in want:
                name = item['name']
                obj_in_have = search_obj_in_list(name, have) or {}

                if state == 'merged' or state == 'rendered':
                    commands.extend(self._state_merged(item, obj_in_have))

                elif state == 'replaced':
                    commands.extend(self._state_replaced(item, obj_in_have))

        return commands

    def _state_replaced(self, want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []

        want = remove_empties(want)

        delete_commands = []
        for have_afi in have.get('access_groups', []):
            want_afi = search_obj_in_list(have_afi['afi'],
                                          want.get('access_groups', []),
                                          key='afi') or {}
            afi = have_afi.get('afi')

            for acl in have_afi.get('acls', []):
                if acl not in want_afi.get('acls', []):
                    delete_commands.extend(
                        self._compute_commands(afi, [acl], remove=True))

        if delete_commands:
            pad_commands(delete_commands, want['name'])
            commands.extend(delete_commands)

        merged_commands = self._state_merged(want, have)
        if merged_commands and delete_commands:
            del merged_commands[0]

        commands.extend(merged_commands)

        return commands

    def _state_overridden(self, want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []

        for have_intf in have:
            want_intf = search_obj_in_list(have_intf['name'], want) or {}
            if not want_intf:
                commands.extend(self._state_deleted(want_intf, have_intf))

        for want_intf in want:
            have_intf = search_obj_in_list(want_intf['name'], have) or {}
            commands.extend(self._state_replaced(want_intf, have_intf))

        return commands

    def _state_merged(self, want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []

        want = remove_empties(want)

        for want_afi in want.get('access_groups', []):
            have_afi = search_obj_in_list(want_afi['afi'],
                                          have.get('access_groups', []),
                                          key='afi') or {}
            delta = diff_list_of_dicts(want_afi['acls'],
                                       have_afi.get('acls', []),
                                       key='direction')
            commands.extend(self._compute_commands(want_afi['afi'], delta))

        if commands:
            pad_commands(commands, want['name'])

        return commands

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []

        # This handles deletion for both empty/no config
        # and just interface name provided.
        if 'access_groups' not in want:
            for x in have.get('access_groups', []):
                afi = x.get('afi')
                for have_acl in x.get('acls', []):
                    commands.extend(
                        self._compute_commands(afi, [have_acl], remove=True))

        else:
            for want_afi in want['access_groups']:
                have_afi = search_obj_in_list(want_afi['afi'],
                                              have.get('access_groups', []),
                                              key='afi') or {}
                afi = have_afi.get('afi')

                # If only the AFI has be specified, we
                # delete all the access-groups for that AFI
                if 'acls' not in want_afi:
                    for have_acl in have_afi.get('acls', []):
                        commands.extend(
                            self._compute_commands(afi, [have_acl],
                                                   remove=True))

                # If one or more acl has been explicitly specified, we
                # delete that and leave the rest untouched
                else:
                    for acl in want_afi['acls']:
                        if acl in have_afi.get('acls', []):
                            commands.extend(
                                self._compute_commands(afi, [acl],
                                                       remove=True))

        if commands:
            pad_commands(commands, have['name'])

        return commands

    def _compute_commands(self, afi, delta, remove=False):
        updates = []
        map_dir = {'in': 'ingress', 'out': 'egress'}

        for x in delta:
            cmd = "{0} access-group {1} {2}".format(afi, x['name'],
                                                    map_dir[x['direction']])
            if remove:
                cmd = "no " + cmd
            updates.append(cmd)

        return updates
