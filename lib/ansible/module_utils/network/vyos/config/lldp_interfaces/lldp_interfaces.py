#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vyos_lldp_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.vyos.facts.facts import Facts
from ansible.module_utils.network.common.utils import to_list, dict_diff
from ansible.module_utils.six import iteritems
from ansible.module_utils.network. vyos.utils.utils import search_obj_in_list, \
    search_dict_tv_in_list, key_value_in_dict, is_dict_element_present


class Lldp_interfaces(ConfigBase):
    """
    The vyos_lldp_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'lldp_interfaces',
    ]

    params = ['enable', 'location', 'name']
    set_cmd = 'set service lldp interface '
    del_cmd = 'delete service lldp interface '

    def __init__(self, module):
        super(Lldp_interfaces, self).__init__(module)

    def get_lldp_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: Th      e current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset,
                                                         self.gather_network_resources)
        lldp_interfaces_facts = facts['ansible_network_resources'].get('lldp_interfaces')
        if not lldp_interfaces_facts:
            return []
        return lldp_interfaces_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()
        existing_lldp_interfaces_facts = self.get_lldp_interfaces_facts()
        commands.extend(self.set_config(existing_lldp_interfaces_facts))
        if commands:
            if self._module.check_mode:
                resp = self._connection.edit_config(commands, commit=False)
            else:
                resp = self._connection.edit_config(commands)
            result['changed'] = True

        result['commands'] = commands

        if self._module._diff:
            result['diff'] = resp['diff'] if result['changed'] else None

        changed_lldp_interfaces_facts = self.get_lldp_interfaces_facts()
        result['before'] = existing_lldp_interfaces_facts
        if result['changed']:
            result['after'] = changed_lldp_interfaces_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_lldp_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_lldp_interfaces_facts
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
        if state == 'overridden':
            commands.extend(self._state_overridden(want, have))
        elif state == 'deleted':
            if want:
                for item in want:
                    name = item['name']
                    obj_in_have = search_obj_in_list(name, have)
                    commands.extend(self._state_deleted(obj_in_have))
            else:
                for have_item in have:
                    commands.extend(self._state_deleted(have_item))
        elif state == 'merged':
            for want_item in want:
                name = want_item['name']
                have_item = search_obj_in_list(name, have)
                commands.extend(self._state_merged(want_item, have_item))
        elif state == 'replaced':
            for want_item in want:
                name = want_item['name']
                obj_in_have = search_obj_in_list(name, have)
                commands.extend(self._state_replaced(want_item, obj_in_have))
        return commands

    @staticmethod
    def _state_replaced(want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        if have:
            commands.extend(Lldp_interfaces._render_del_commands(want, have))
        commands.extend(Lldp_interfaces._state_merged(want, have))
        return commands

    @staticmethod
    def _state_overridden(want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        for have_item in have:
            lldp_name = have_item['name']
            lldp_in_want = search_obj_in_list(lldp_name, want)
            if not lldp_in_want:
                commands.extend(Lldp_interfaces._purge_attribs(have_item))

        for want_item in want:
            name = want_item['name']
            lldp_in_have = search_obj_in_list(name, have)
            commands.extend(Lldp_interfaces._state_replaced(want_item, lldp_in_have))
        return commands

    @staticmethod
    def _state_merged(want, have):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []
        if have:
            commands.extend(Lldp_interfaces._render_updates(want, have))
        else:
            commands.extend(Lldp_interfaces._render_set_commands(want))
        return commands

    @staticmethod
    def _state_deleted(have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        if have:
            name = have['name']
            commands.append(Lldp_interfaces.del_cmd + name)
        return commands

    @staticmethod
    def _render_updates(want, have):
        commands = []
        lldp_name = have['name']
        commands.extend(Lldp_interfaces.configure_status(lldp_name, want, have))
        commands.extend(Lldp_interfaces.add_location(lldp_name, want, have))

        return commands

    @staticmethod
    def _render_set_commands(want):
        commands = []
        have = {}
        lldp_name = want['name']

        params = Lldp_interfaces.params

        commands.extend(Lldp_interfaces.add_location(lldp_name, want, have))
        for attrib in params:
            value = want[attrib]
            if value:
                if attrib == 'location':
                    commands.extend(Lldp_interfaces.add_location(lldp_name, want, have))
                elif attrib == 'enable':
                    if not value:
                        commands.append(Lldp_interfaces.set_cmd + lldp_name + ' disable ')
                else:
                    commands.append(Lldp_interfaces.set_cmd + lldp_name)

        return commands

    @staticmethod
    def _purge_attribs(have):
        commands = []
        name = have['name']
        commands.append(Lldp_interfaces.del_cmd + ' ' + name)
        return commands

    @staticmethod
    def _render_del_commands(want, have):
        commands = []

        lldp_name = have['name']
        params = Lldp_interfaces.params

        for attrib in params:
            if attrib == 'location':
                commands.extend(Lldp_interfaces.update_location(lldp_name, want, have))
        return commands

    @staticmethod
    def configure_status(name, want_item, have_item):
        commands = []
        if is_dict_element_present(have_item, 'enable'):
            temp_have_item = False
        else:
            temp_have_item = True
        if want_item['enable'] != temp_have_item:
            if want_item['enable']:
                commands.append(Lldp_interfaces.del_cmd + name + ' disable')
            else:
                commands.append(Lldp_interfaces.set_cmd + name + ' disable')
        return commands

    @staticmethod
    def delete_disable(want_item):
        commands = []
        name = want_item['name']
        if not want_item['enable']:
            commands.append('delete service lldp interface ' + name + ' disable')
        return commands

    @staticmethod
    def add_location(name, want_item, have_item):
        commands = []
        have_dict = {}
        have_ca = {}
        set_cmd = Lldp_interfaces.set_cmd + name
        want_location_type = want_item.get('location') or {}
        have_location_type = have_item.get('location') or {}

        if want_location_type['coordinate_based']:
            want_dict = want_location_type.get('coordinate_based') or {}
            if is_dict_element_present(have_location_type, 'coordinate_based'):
                have_dict = have_location_type.get('coordinate_based') or {}
            location_type = 'coordinate-based'
            updates = dict_diff(have_dict, want_dict)
            for key, value in iteritems(updates):
                if value:
                    commands.append(set_cmd + ' location ' + location_type + ' ' + key + ' ' + str(value))

        elif want_location_type['civic_based']:
            location_type = 'civic-based'
            want_dict = want_location_type.get('civic_based') or {}
            want_ca = want_dict.get('ca_info') or []
            if is_dict_element_present(have_location_type, 'civic_based'):
                have_dict = have_location_type.get('civic_based') or {}
                have_ca = have_dict.get('ca_info') or []
                if want_dict['country_code'] != have_dict['country_code']:
                    commands.append(
                        set_cmd + ' location ' + location_type + ' country-code ' + str(want_dict['country_code']))
            else:
                commands.append(
                    set_cmd + ' location ' + location_type + ' country-code ' + str(want_dict['country_code']))
            commands.extend(Lldp_interfaces.add_civic_address(name, want_ca, have_ca))

        elif want_location_type['elin']:
            location_type = 'elin'
            if is_dict_element_present(have_location_type, 'elin'):
                if want_location_type.get('elin') != have_location_type.get('elin'):
                    commands.append(set_cmd + ' location ' + location_type + ' ' + str(want_location_type['elin']))
            else:
                commands.append(set_cmd + ' location ' + location_type + ' ' + str(want_location_type['elin']))
        return commands

    @staticmethod
    def update_location(name, want_item, have_item):
        commands = []
        del_cmd = 'delete service lldp interface ' + name
        want_location_type = want_item.get('location') or {}
        have_location_type = have_item.get('location') or {}

        if want_location_type['coordinate_based']:
            want_dict = want_location_type.get('coordinate_based') or {}
            if is_dict_element_present(have_location_type, 'coordinate_based'):
                have_dict = have_location_type.get('coordinate_based') or {}
                location_type = 'coordinate-based'
                for key, value in iteritems(have_dict):
                    only_in_have = key_value_in_dict(key, value, want_dict)
                    if not only_in_have:
                        commands.append(del_cmd + ' location ' + location_type + ' ' + key + ' ' + str(value))
            else:
                commands.append(del_cmd + ' location')

        elif want_location_type['civic_based']:
            want_dict = want_location_type.get('civic_based') or {}
            want_ca = want_dict.get('ca_info') or []
            if is_dict_element_present(have_location_type, 'civic_based'):
                have_dict = have_location_type.get('civic_based') or {}
                have_ca = have_dict.get('ca_info')
                commands.extend(Lldp_interfaces.update_civic_address(name, want_ca, have_ca))
            else:
                commands.append(del_cmd + ' location')

        else:
            if is_dict_element_present(have_location_type, 'elin'):
                if want_location_type.get('elin') != have_location_type.get('elin'):
                    commands.append(del_cmd + ' location')
            else:
                commands.append(del_cmd + ' location')
        return commands

    @staticmethod
    def delete_location(want_item):
        commands = []
        name = want_item['name']
        del_cmd = 'delete service lldp interface ' + name + ' location'
        want_location_type = want_item.get('location') or {}
        if want_location_type:
            commands.append(del_cmd)
        return commands

    @staticmethod
    def add_civic_address(name, want, have):
        commands = []
        for item in want:
            ca_type = item['ca_type']
            ca_value = item['ca_value']
            obj_in_have = search_dict_tv_in_list(ca_type, ca_value, have, 'ca_type', 'ca_value')
            if not obj_in_have:
                commands.append(Lldp_interfaces.set_cmd + name + ' location civic-based ca-type ' + str(
                    ca_type) + ' ca-value ' + ca_value)
        return commands

    @staticmethod
    def update_civic_address(name, want, have):
        commands = []
        for item in have:
            ca_type = item['ca_type']
            ca_value = item['ca_value']
            in_want = search_dict_tv_in_list(ca_type, ca_value, want, 'ca_type', 'ca_value')
            if not in_want:
                commands.append(
                    Lldp_interfaces.del_cmd + name + ' location civic-based ca-type ' + str(ca_type))
        return commands
