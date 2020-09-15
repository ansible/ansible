#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The iosxr_lag_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from copy import deepcopy
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.iosxr.facts.facts import Facts
from ansible.module_utils.network.common.utils \
    import (
        to_list,
        dict_diff,
        remove_empties,
        search_obj_in_list,
        param_list_to_dict
    )
from ansible.module_utils.network.iosxr.utils.utils \
    import (
        diff_list_of_dicts,
        pad_commands,
        flatten_dict,
        dict_delete,
        normalize_interface
    )


class Lag_interfaces(ConfigBase):
    """
    The iosxr_lag_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'lag_interfaces',
    ]

    def __init__(self, module):
        super(Lag_interfaces, self).__init__(module)

    def get_lag_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(
            self.gather_subset, self.gather_network_resources)
        lag_interfaces_facts = facts['ansible_network_resources'].get(
            'lag_interfaces')
        if not lag_interfaces_facts:
            return []
        return lag_interfaces_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        commands = list()

        existing_lag_interfaces_facts = self.get_lag_interfaces_facts()
        commands.extend(self.set_config(existing_lag_interfaces_facts))
        if commands:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True
        result['commands'] = commands

        changed_lag_interfaces_facts = self.get_lag_interfaces_facts()

        result['before'] = existing_lag_interfaces_facts
        if result['changed']:
            result['after'] = changed_lag_interfaces_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_lag_interfaces_facts):
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
                            'member': normalize_interface(item['member']),
                            'mode': item['mode']
                        })
        have = existing_lag_interfaces_facts
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

        if state in ('overridden', 'merged', 'replaced') and not want:
            self._module.fail_json(msg='value of config parameter must not be empty for state {0}'.format(state))

        if state == 'overridden':
            commands.extend(self._state_overridden(want, have))

        elif state == 'deleted':
            commands.extend(self._state_deleted(want, have))

        else:
            # Instead of passing entire want and have
            # list of dictionaries to the respective
            # _state_* methods we are passing the want
            # and have dictionaries per interface
            for item in want:
                name = item['name']
                obj_in_have = search_obj_in_list(name, have)

                if state == 'merged':
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
        if have:
            commands.extend(self._render_bundle_del_commands(want, have))
        commands.extend(self._render_bundle_updates(want, have))

        if commands or have == {}:
            pad_commands(commands, want['name'])

        if have:
            commands.extend(self._render_interface_del_commands(want, have))
        commands.extend(self._render_interface_updates(want, have))

        return commands

    def _state_overridden(self, want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        for have_intf in have:
            intf_in_want = search_obj_in_list(have_intf['name'], want)
            if not intf_in_want:
                commands.extend(self._purge_attribs(have_intf))

        for intf in want:
            intf_in_have = search_obj_in_list(intf['name'], have)
            commands.extend(self._state_replaced(intf, intf_in_have))

        return commands

    def _state_merged(self, want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        commands.extend(self._render_bundle_updates(want, have))

        if commands or have == {}:
            pad_commands(commands, want['name'])

        commands.extend(self._render_interface_updates(want, have))

        return commands

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []

        if not want:
            for item in have:
                commands.extend(self._purge_attribs(intf=item))
        else:
            for item in want:
                name = item['name']
                obj_in_have = search_obj_in_list(name, have)
                if not obj_in_have:
                    self._module.fail_json(
                        msg=('interface {0} does not exist'.format(name)))
                commands.extend(self._purge_attribs(intf=obj_in_have))

        return commands

    def _render_bundle_updates(self, want, have):
        """ The command generator for updates to bundles
         :rtype: A list
        :returns: the commands necessary to update bundles
        """
        commands = []
        if not have:
            have = {'name': want['name']}

        want_copy = deepcopy(want)
        have_copy = deepcopy(have)

        want_copy.pop('members', [])
        have_copy.pop('members', [])

        bundle_updates = dict_diff(have_copy, want_copy)

        if bundle_updates:
            for key, value in iteritems(
                    flatten_dict(remove_empties(bundle_updates))):
                commands.append(self._compute_commands(key=key, value=value))

        return commands

    def _render_interface_updates(self, want, have):
        """ The command generator for updates to member
            interfaces
        :rtype: A list
        :returns: the commands necessary to update member
                  interfaces
        """
        commands = []

        if not have:
            have = {'name': want['name']}

        member_diff = diff_list_of_dicts(want['members'],
                                         have.get('members', []))

        for diff in member_diff:
            diff_cmd = []
            bundle_cmd = 'bundle id {0}'.format(
                want['name'].split('Bundle-Ether')[1])
            if diff.get('mode'):
                bundle_cmd += ' mode {0}'.format(diff.get('mode'))
            diff_cmd.append(bundle_cmd)
            pad_commands(diff_cmd, diff['member'])
            commands.extend(diff_cmd)

        return commands

    def _render_bundle_del_commands(self, want, have):
        """ The command generator for delete commands
            w.r.t bundles
        :rtype: A list
        :returns: the commands necessary to update member
                  interfaces
        """
        commands = []
        if not want:
            want = {'name': have['name']}

        want_copy = deepcopy(want)
        have_copy = deepcopy(have)
        want_copy.pop('members', [])
        have_copy.pop('members', [])

        to_delete = dict_delete(have_copy, remove_empties(want_copy))
        if to_delete:
            for key, value in iteritems(flatten_dict(
                    remove_empties(to_delete))):
                commands.append(
                    self._compute_commands(key=key, value=value, remove=True))

        return commands

    def _render_interface_del_commands(self, want, have):
        """ The command generator for delete commands
            w.r.t member interfaces
        :rtype: A list
        :returns: the commands necessary to update member
                  interfaces
        """
        commands = []
        if not want:
            want = {}
        have_members = have.get('members')

        if have_members:
            have_members = param_list_to_dict(deepcopy(have_members), unique_key='member')
            want_members = param_list_to_dict(deepcopy(want).get('members', []), unique_key='member')

            for key in have_members:
                if key not in want_members:
                    member_cmd = ['no bundle id']
                    pad_commands(member_cmd, key)
                    commands.extend(member_cmd)

        return commands

    def _purge_attribs(self, intf):
        """ The command generator for purging attributes
        :rtype: A list
        :returns: the commands necessary to purge attributes
        """
        commands = []
        have_copy = deepcopy(intf)
        members = have_copy.pop('members', [])

        to_delete = dict_delete(have_copy, remove_empties({'name': have_copy['name']}))
        if to_delete:
            for key, value in iteritems(flatten_dict(remove_empties(to_delete))):
                commands.append(self._compute_commands(key=key, value=value, remove=True))

        if commands:
            pad_commands(commands, intf['name'])

        if members:
            members = param_list_to_dict(deepcopy(members), unique_key='member')
            for key in members:
                member_cmd = ['no bundle id']
                pad_commands(member_cmd, key)
                commands.extend(member_cmd)

        return commands

    def _compute_commands(self, key, value, remove=False):
        """ The method generates LAG commands based on the
            key, value passed. When remove is set to True,
            the command is negated.
        :rtype: str
        :returns: a command based on the `key`, `value` pair
                  passed and the value of `remove`
        """
        if key == "mode":
            cmd = "lacp mode {0}".format(value)

        elif key == "load_balancing_hash":
            cmd = "bundle load-balancing hash {0}".format(value)

        elif key == "max_active":
            cmd = "bundle maximum-active links {0}".format(value)

        elif key == "min_active":
            cmd = "bundle minimum-active links {0}".format(value)

        if remove:
            cmd = "no {0}".format(cmd)

        return cmd
