#
# -*- coding: utf-8 -*-
# Copyright 2019 Cisco and/or its affiliates.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
nxos_bfd_interfaces class
This class creates a command set to bring the current device configuration
to a desired end-state. The command set is based on a comparison of the
current configuration (as dict) and the provided configuration (as dict).
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import dict_diff, to_list, remove_empties
from ansible.module_utils.network.nxos.facts.facts import Facts
from ansible.module_utils.network.nxos.utils.utils import flatten_dict, get_interface_type, normalize_interface, search_obj_in_list, vlan_range_to_list


class Bfd_interfaces(ConfigBase):
    """
    The nxos_bfd_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]
    gather_network_resources = [
        'bfd_interfaces',
    ]
    # exclude_params = []

    def __init__(self, module):
        super(Bfd_interfaces, self).__init__(module)

    def get_bfd_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :returns: A list of interface configs and a platform string
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        bfd_interfaces_facts = facts['ansible_network_resources'].get('bfd_interfaces', [])
        platform = facts.get('ansible_net_platform', '')
        return bfd_interfaces_facts, platform

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

        existing_bfd_interfaces_facts, platform = self.get_bfd_interfaces_facts()
        cmds.extend(self.set_config(existing_bfd_interfaces_facts, platform))
        if cmds:
            if not self._module.check_mode:
                self.edit_config(cmds)
            result['changed'] = True
        result['commands'] = cmds

        changed_bfd_interfaces_facts, platform = self.get_bfd_interfaces_facts()
        result['before'] = existing_bfd_interfaces_facts
        if result['changed']:
            result['after'] = changed_bfd_interfaces_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_bfd_interfaces_facts, platform):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        if re.search('N[56]K', platform):
            # Some platforms do not support the 'bfd' interface keyword;
            # remove the 'bfd' key from each want/have interface.
            orig_want = self._module.params['config']
            want = []
            for w in orig_want:
                del w['bfd']
                want.append(w)
            orig_have = existing_bfd_interfaces_facts
            have = []
            for h in orig_have:
                del h['bfd']
                have.append(h)
        else:
            want = self._module.params['config']
            have = existing_bfd_interfaces_facts

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
            # Clean up bfd attrs for any interfaces not listed in the play
            h = flatten_dict(h)
            obj_in_want = flatten_dict(search_obj_in_list(h['name'], want, 'name'))
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
        # 'bfd' and 'bfd echo' are enabled by default so the handling is
        # counter-intuitive; we are enabling them to remove them. The end result
        # is that they are removed from the interface config on the device.
        if 'bfd' in obj and 'disable' in obj['bfd']:
            cmds.append('bfd')
        if 'echo' in obj and 'disable' in obj['echo']:
            cmds.append('bfd echo')
        if cmds:
            cmds.insert(0, 'interface ' + obj['name'])
        return cmds

    def set_none_vals_to_defaults(self, want):
        # Set dict None values to default states
        if 'bfd' in want and want['bfd'] is None:
            want['bfd'] = 'enable'
        if 'echo' in want and want['echo'] is None:
            want['echo'] = 'enable'
        return want

    def diff_of_dicts(self, want, obj_in_have):
        diff = set(want.items()) - set(obj_in_have.items())
        diff = dict(diff)
        if diff and want['name'] == obj_in_have['name']:
            diff.update({'name': want['name']})
        return diff

    def add_commands(self, want):
        if not want:
            return []
        cmds = []
        if 'bfd' in want and want['bfd'] is not None:
            cmd = 'bfd' if want['bfd'] == 'enable' else 'no bfd'
            cmds.append(cmd)
        if 'echo' in want and want['echo'] is not None:
            cmd = 'bfd echo' if want['echo'] == 'enable' else 'no bfd echo'
            cmds.append(cmd)

        if cmds:
            cmds.insert(0, 'interface ' + want['name'])
        return cmds

    def set_commands(self, want, have):
        cmds = []
        obj_in_have = flatten_dict(search_obj_in_list(want['name'], have, 'name'))
        if not obj_in_have:
            cmds = self.add_commands(want)
        else:
            diff = self.diff_of_dicts(want, obj_in_have)
            cmds = self.add_commands(diff)
        return cmds
