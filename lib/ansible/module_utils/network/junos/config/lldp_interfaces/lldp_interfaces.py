#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The junos_lldp_interfaces class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.junos.facts.facts import Facts
from ansible.module_utils.network.junos.junos import locked_config, load_config, commit_configuration, discard_changes, tostring
from ansible.module_utils.network.common.netconf import build_root_xml_node, build_child_xml_node, build_subtree


class Lldp_interfaces(ConfigBase):
    """
    The junos_lldp_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'lldp_interfaces',
    ]

    def __init__(self, module):
        super(Lldp_interfaces, self).__init__(module)

    def get_lldp_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)
        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
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
        warnings = list()

        existing_lldp_interfaces_facts = self.get_lldp_interfaces_facts()
        config_xmls = self.set_config(existing_lldp_interfaces_facts)

        with locked_config(self._module):
            for config_xml in to_list(config_xmls):
                diff = load_config(self._module, config_xml, warnings)

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

        changed_lldp_interfaces_facts = self.get_lldp_interfaces_facts()

        result['before'] = existing_lldp_interfaces_facts
        if result['changed']:
            result['after'] = changed_lldp_interfaces_facts

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
        root = build_root_xml_node('protocols')
        lldp_intf_ele = build_subtree(root, 'lldp')

        state = self._module.params['state']
        if state == 'overridden':
            config_xmls = self._state_overridden(want, have)
        elif state == 'deleted':
            config_xmls = self._state_deleted(want, have)
        elif state == 'merged':
            config_xmls = self._state_merged(want, have)
        elif state == 'replaced':
            config_xmls = self._state_replaced(want, have)

        for xml in config_xmls:
            lldp_intf_ele.append(xml)

        return tostring(root)

    def _state_replaced(self, want, have):
        """ The xml configuration generator when state is replaced
        :rtype: A list
        :returns: the xml configuration necessary to migrate the current configuration
                  to the desired configuration
        """
        lldp_intf_xml = []
        lldp_intf_xml.extend(self._state_deleted(want, have))
        lldp_intf_xml.extend(self._state_merged(want, have))

        return lldp_intf_xml

    def _state_overridden(self, want, have):
        """ The xml configuration generator when state is overridden
        :rtype: A list
        :returns: the xml configuration necessary to migrate the current configuration
                  to the desired configuration
        """
        lldp_intf_xmls_obj = []

        # replace interface config with data in want
        lldp_intf_xmls_obj.extend(self._state_replaced(want, have))

        # delete interface config if interface in have not present in want
        delete_obj = []
        for have_obj in have:
            for want_obj in want:
                if have_obj['name'] == want_obj['name']:
                    break
            else:
                delete_obj.append(have_obj)

        if len(delete_obj):
            lldp_intf_xmls_obj.extend(self._state_deleted(delete_obj, have))

        return lldp_intf_xmls_obj

    def _state_merged(self, want, have):
        """ The xml configuration generator when state is merged
         :rtype: A list
         :returns: the xml configuration necessary to merge the provided into
                   the current configuration
         """
        lldp_intf_xml = []
        for config in want:
            lldp_intf_root = build_root_xml_node('interface')

            if config.get('name'):
                build_child_xml_node(lldp_intf_root, 'name', config['name'])

            if config.get('enabled') is not None:
                if config['enabled'] is False:
                    build_child_xml_node(lldp_intf_root, 'disable')
                else:
                    build_child_xml_node(lldp_intf_root, 'disable', None, {'delete': 'delete'})
            else:
                build_child_xml_node(lldp_intf_root, 'disable', None, {'delete': 'delete'})
            lldp_intf_xml.append(lldp_intf_root)
        return lldp_intf_xml

    def _state_deleted(self, want, have):
        """ The xml configuration generator when state is deleted
        :rtype: A list
        :returns: the xml configuration necessary to remove the current configuration
                  of the provided objects
        """
        lldp_intf_xml = []
        intf_obj = want

        if not intf_obj:
            # delete lldp interfaces attribute from all the existing interface
            intf_obj = have

        for config in intf_obj:
            lldp_intf_root = build_root_xml_node('interface')
            lldp_intf_root.attrib.update({'delete': 'delete'})
            build_child_xml_node(lldp_intf_root, 'name', config['name'])

            lldp_intf_xml.append(lldp_intf_root)

        return lldp_intf_xml
