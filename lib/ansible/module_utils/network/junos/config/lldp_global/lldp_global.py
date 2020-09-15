#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The junos_lldp class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.junos.junos import locked_config, load_config, commit_configuration, discard_changes, tostring
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.junos.facts.facts import Facts
from ansible.module_utils.network.common.netconf import build_root_xml_node, build_child_xml_node


class Lldp_global(ConfigBase):
    """
    The junos_lldp class
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

        existing_lldp_global_facts = self.get_lldp_global_facts()
        config_xmls = self.set_config(existing_lldp_global_facts)

        with locked_config(self._module):
            for config_xml in to_list(config_xmls):
                diff = load_config(self._module, config_xml, [])

            commit = not self._module.check_mode
            if diff:
                if commit:
                    commit_configuration(self._module)
                else:
                    discard_changes(self._module)
                result['changed'] = True

                if self._module._diff:
                    result['diff'] = {'prepared': diff}

        result['commands'] = config_xmls

        changed_lldp_global_facts = self.get_lldp_global_facts()

        result['before'] = existing_lldp_global_facts
        if result['changed']:
            result['after'] = changed_lldp_global_facts

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
        :returns: the list xml configuration necessary to migrate the current configuration
                  to the desired configuration
        """
        root = build_root_xml_node('protocols')
        state = self._module.params['state']
        if state == 'deleted':
            config_xmls = self._state_deleted(want, have)
        elif state == 'merged':
            config_xmls = self._state_merged(want, have)
        elif state == 'replaced':
            config_xmls = self._state_replaced(want, have)

        for xml in config_xmls:
            root.append(xml)
        return tostring(root)

    def _state_replaced(self, want, have):
        """ The xml configuration generator when state is merged
         :rtype: A list
         :returns: the xml configuration necessary to merge the provided into
                   the current configuration
         """
        lldp_xml = []
        lldp_xml.extend(self._state_deleted(want, have))
        lldp_xml.extend(self._state_merged(want, have))

        return lldp_xml

    def _state_merged(self, want, have):
        """ Select the appropriate function based on the state provided
        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the list xml configuration necessary to migrate the current configuration
                  to the desired configuration
        """
        lldp_xml = []

        lldp_root = build_root_xml_node('lldp')
        if want.get('address'):
            build_child_xml_node(lldp_root, 'management-address', want['address'])
        if want.get('interval'):
            build_child_xml_node(lldp_root, 'advertisement-interval', want['interval'])
        if want.get('transmit_delay'):
            build_child_xml_node(lldp_root, 'transmit-delay', want['transmit_delay'])
        if want.get('hold_multiplier'):
            build_child_xml_node(lldp_root, 'hold-multiplier', want['hold_multiplier'])
        enable = want.get('enable')
        if enable is not None:
            if enable is False:
                build_child_xml_node(lldp_root, 'disable')
            else:
                build_child_xml_node(lldp_root, 'disable', None, {'delete': 'delete'})
        else:
            build_child_xml_node(lldp_root, 'disable', None, {'delete': 'delete'})
        lldp_xml.append(lldp_root)

        return lldp_xml

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted
        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        lldp_xml = []

        lldp_root = build_root_xml_node('lldp')
        build_child_xml_node(lldp_root, 'management-address', None, {'delete': 'delete'})
        build_child_xml_node(lldp_root, 'advertisement-interval', None, {'delete': 'delete'})
        build_child_xml_node(lldp_root, 'transmit-delay', None, {'delete': 'delete'})
        build_child_xml_node(lldp_root, 'hold-multiplier', None, {'delete': 'delete'})
        build_child_xml_node(lldp_root, 'disable', None, {'delete': 'delete'})
        lldp_xml.append(lldp_root)
        return lldp_xml
