#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The nxos_vlans class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import dict_diff, to_list, remove_empties
from ansible.module_utils.network.nxos.facts.facts import Facts
from ansible.module_utils.network.nxos.utils.utils import get_interface_type, normalize_interface, search_obj_in_list


class Vlans(ConfigBase):
    """
    The nxos_vlans class
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
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        vlans_facts = facts['ansible_network_resources'].get('vlans')
        if not vlans_facts:
            return []

        # Remove vlan 1 from facts list
        vlans_facts = [i for i in vlans_facts if (int(i['vlan_id'])) != 1]
        return vlans_facts

    def edit_config(self, commands):
        """Wrapper method for `_connection.edit_config()`
        This exists solely to allow the unit test framework to mock device connection calls.
        """
        return self._connection.edit_config(commands)

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()

        existing_vlans_facts = self.get_vlans_facts()
        commands.extend(self.set_config(existing_vlans_facts))
        if commands:
            if not self._module.check_mode:
                self.edit_config(commands)
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
        config = self._module.params.get('config')
        want = []
        if config:
            for w in config:
                if int(w['vlan_id']) == 1:
                    self._module.fail_json(msg="Vlan 1 is not allowed to be managed by this module")
                want.append(remove_empties(w))
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
            self._module.fail_json(msg='config is required for state {0}'.format(state))

        commands = list()
        if state == 'overridden':
            commands.extend(self._state_overridden(want, have))
        elif state == 'deleted':
            commands.extend(self._state_deleted(want, have))
        else:
            for w in want:
                if state == 'merged':
                    commands.extend(self._state_merged(w, have))
                elif state == 'replaced':
                    commands.extend(self._state_replaced(w, have))
        return commands

    def remove_default_states(self, obj):
        """Removes non-empty but default states from the obj.
        """
        default_states = {
            'enabled': True,
            'state': 'active',
            'mode': 'ce',
        }
        for k in default_states.keys():
            if obj[k] == default_states[k]:
                obj.pop(k, None)
        return obj

    def _state_replaced(self, want, have):
        """ The command generator when state is replaced.
        Scope is limited to vlan objects defined in the playbook.
        :rtype: A list
        :returns: The minimum command set required to migrate the current
                  configuration to the desired configuration.
        """
        obj_in_have = search_obj_in_list(want['vlan_id'], have, 'vlan_id')
        if obj_in_have:
            # ignore states that are already reset, then diff what's left
            obj_in_have = self.remove_default_states(obj_in_have)
            diff = dict_diff(want, obj_in_have)
            # Remove merge items from diff; what's left will be used to
            # remove states not specified in the playbook
            for k in dict(set(want.items()) - set(obj_in_have.items())).keys():
                diff.pop(k, None)
        else:
            diff = want

        # merged_cmds: 'want' cmds to update 'have' states that don't match
        # replaced_cmds: remaining 'have' cmds that need to be reset to default
        merged_cmds = self.set_commands(want, have)
        replaced_cmds = []
        if obj_in_have:
            # Remaining diff items are used to reset states to default
            replaced_cmds = self.del_attribs(diff)
        cmds = []
        if replaced_cmds or merged_cmds:
            cmds += ['vlan %s' % str(want['vlan_id'])]
            cmds += merged_cmds + replaced_cmds
        return cmds

    def _state_overridden(self, want, have):
        """ The command generator when state is overridden.
        Scope includes all vlan objects on the device.
        :rtype: A list
        :returns: the minimum command set required to migrate the current
                  configuration to the desired configuration.
        """
        # overridden behavior is the same as replaced except for scope.
        cmds = []
        existing_vlans = []
        for h in have:
            existing_vlans.append(h['vlan_id'])
            obj_in_want = search_obj_in_list(h['vlan_id'], want, 'vlan_id')
            if obj_in_want:
                if h != obj_in_want:
                    replaced_cmds = self._state_replaced(obj_in_want, [h])
                    if replaced_cmds:
                        cmds.extend(replaced_cmds)
            else:
                cmds.append('no vlan %s' % h['vlan_id'])

        # Add wanted vlans that don't exist on the device yet
        for w in want:
            if w['vlan_id'] not in existing_vlans:
                new_vlan = ['vlan %s' % w['vlan_id']]
                cmds.extend(new_vlan + self.add_commands(w))
        return cmds

    def _state_merged(self, w, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        cmds = self.set_commands(w, have)
        if cmds:
            cmds.insert(0, 'vlan %s' % str(w['vlan_id']))
        return(cmds)

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        if want:
            for w in want:
                obj_in_have = search_obj_in_list(w['vlan_id'], have, 'vlan_id')
                if obj_in_have:
                    commands.append('no vlan ' + str(obj_in_have['vlan_id']))
        else:
            if not have:
                return commands
            for h in have:
                commands.append('no vlan ' + str(h['vlan_id']))
        return commands

    def del_attribs(self, obj):
        """Returns a list of commands to reset states to default
        """
        commands = []
        if not obj:
            return commands
        default_cmds = {
            'name': 'no name',
            'state': 'no state',
            'enabled': 'no shutdown',
            'mode': 'mode ce',
            'mapped_vni': 'no vn-segment',
        }
        for k in obj:
            commands.append(default_cmds[k])
        return commands

    def diff_of_dicts(self, w, obj):
        diff = set(w.items()) - set(obj.items())
        diff = dict(diff)
        if diff and w['vlan_id'] == obj['vlan_id']:
            diff.update({'vlan_id': w['vlan_id']})
        return diff

    def add_commands(self, d):
        commands = []
        if not d:
            return commands
        if 'name' in d:
            commands.append('name ' + d['name'])
        if 'state' in d:
            commands.append('state ' + d['state'])
        if 'enabled' in d:
            if d['enabled'] is True:
                commands.append('no shutdown')
            else:
                commands.append('shutdown')
        if 'mode' in d:
            commands.append('mode ' + d['mode'])
        if 'mapped_vni' in d:
            commands.append('vn-segment %s' % d['mapped_vni'])

        return commands

    def set_commands(self, w, have):
        commands = []
        obj_in_have = search_obj_in_list(w['vlan_id'], have, 'vlan_id')
        if not obj_in_have:
            commands = self.add_commands(w)
        else:
            diff = self.diff_of_dicts(w, obj_in_have)
            commands = self.add_commands(diff)
        return commands
