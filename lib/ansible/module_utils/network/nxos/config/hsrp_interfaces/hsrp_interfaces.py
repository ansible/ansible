#
# -*- coding: utf-8 -*-
# Copyright 2019 Cisco and/or its affiliates.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The nxos hsrp_interfaces class
This class creates a command set to bring the current device configuration
to a desired end-state. The command set is based on a comparison of the
current configuration (as dict) and the provided configuration (as dict).
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import dict_diff, to_list, remove_empties
from ansible.module_utils.network.nxos.facts.facts import Facts
from ansible.module_utils.network.nxos.utils.utils import flatten_dict, get_interface_type, normalize_interface, search_obj_in_list, vlan_range_to_list


class Hsrp_interfaces(ConfigBase):
    """
    The nxos_hsrp_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'hsrp_interfaces',
    ]

    def __init__(self, module):
        super(Hsrp_interfaces, self).__init__(module)

    def get_hsrp_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        hsrp_interfaces_facts = facts['ansible_network_resources'].get('hsrp_interfaces', [])
        return hsrp_interfaces_facts

    def edit_config(self, commands):
        return self._connection.edit_config(commands)

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()
        cmds = list()

        existing_hsrp_interfaces_facts = self.get_hsrp_interfaces_facts()
        cmds.extend(self.set_config(existing_hsrp_interfaces_facts))
        if cmds:
            if not self._module.check_mode:
                self.edit_config(cmds)
            result['changed'] = True
        result['commands'] = cmds
        changed_hsrp_interfaces_facts = self.get_hsrp_interfaces_facts()

        result['before'] = existing_hsrp_interfaces_facts
        if result['changed']:
            result['after'] = changed_hsrp_interfaces_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_hsrp_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        config = self._module.params['config']
        want = []
        if config:
            for w in config:
                w.update({'name': normalize_interface(w['name'])})
                want.append(w)
        have = existing_hsrp_interfaces_facts
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
        # check for 'config' keyword in play
        if state in ('overridden', 'merged', 'replaced') and not want:
            self._module.fail_json(msg='config is required for state {0}'.format(state))

        cmds = list()
        if state == 'overridden':
            cmds.extend(self._state_overridden(want, have))
        elif state == 'deleted':
            cmds.extend(self._state_deleted(want, have))
        else:
            for w in want:
                if state == 'merged':
                    cmds.extend(self._state_merged(flatten_dict(w), have))
                elif state == 'replaced':
                    cmds.extend(self._state_replaced(flatten_dict(w), have))
        return cmds

    def _state_replaced(self, want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        cmds = []
        obj_in_have = search_obj_in_list(want['name'], have, 'name')
        if obj_in_have:
            diff = dict_diff(want, obj_in_have)
        else:
            diff = want
        merged_cmds = self.set_commands(want, have)
        if 'name' not in diff:
            diff['name'] = want['name']

        replaced_cmds = []
        if obj_in_have:
            replaced_cmds = self.del_attribs(diff)
        if replaced_cmds or merged_cmds:
            for cmd in set(replaced_cmds).intersection(set(merged_cmds)):
                merged_cmds.remove(cmd)
            cmds.extend(replaced_cmds)
            cmds.extend(merged_cmds)
        return cmds

    def _state_overridden(self, want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        cmds = []
        for h in have:
            # Check existing states, set to default if not in want or different than want
            h = flatten_dict(h)
            obj_in_want = search_obj_in_list(h['name'], want, 'name')
            if obj_in_want:
                # Let the 'want' loop handle all vals for this interface
                continue
            cmds.extend(self.del_attribs(h))
        for w in want:
            # Update any want attrs if needed. The overridden state considers
            # the play as the source of truth for the entire device, therefore
            # set any unspecified attrs to their default state.
            w = self.set_none_vals_to_defaults(flatten_dict(w))
            cmds.extend(self.set_commands(w, have))
        return cmds

    def _state_merged(self, want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        return self.set_commands(want, have)

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        if not (want or have):
            return []
        cmds = []
        if want:
            for w in want:
                obj_in_have = flatten_dict(search_obj_in_list(w['name'], have, 'name'))
                cmds.extend(self.del_attribs(obj_in_have))
        else:
            for h in have:
                cmds.extend(self.del_attribs(flatten_dict(h)))
        return cmds

    def del_attribs(self, obj):
        if not obj or len(obj.keys()) == 1:
            return []
        cmds = []
        if 'bfd' in obj:
            cmds.append('no hsrp bfd')
        if cmds:
            cmds.insert(0, 'interface ' + obj['name'])
        return cmds

    def set_none_vals_to_defaults(self, want):
        # Set dict None values to default states
        if 'bfd' in want and want['bfd'] is None:
            want['bfd'] = 'disable'
        return want

    def diff_of_dicts(self, want, obj_in_have):
        diff = set(want.items()) - set(obj_in_have.items())
        diff = dict(diff)
        if diff and want['name'] == obj_in_have['name']:
            diff.update({'name': want['name']})
        return diff

    def add_commands(self, want, obj_in_have):
        if not want:
            return []
        cmds = []
        if 'bfd' in want and want['bfd'] is not None:
            if want['bfd'] == 'enable':
                cmd = 'hsrp bfd'
                cmds.append(cmd)
            elif want['bfd'] == 'disable' and obj_in_have and obj_in_have.get('bfd') == 'enable':
                cmd = 'no hsrp bfd'
                cmds.append(cmd)

        if cmds:
            cmds.insert(0, 'interface ' + want['name'])
        return cmds

    def set_commands(self, want, have):
        cmds = []
        obj_in_have = search_obj_in_list(want['name'], have, 'name')
        if not obj_in_have:
            cmds = self.add_commands(want, obj_in_have)
        else:
            diff = self.diff_of_dicts(want, obj_in_have)
            cmds = self.add_commands(diff, obj_in_have)
        return cmds
