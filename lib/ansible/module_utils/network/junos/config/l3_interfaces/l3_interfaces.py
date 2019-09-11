#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The junos_l3_interfaces class
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
from ansible.module_utils.network.junos.junos import (
    locked_config, load_config, commit_configuration, discard_changes,
    tostring)
from ansible.module_utils.network.common.netconf import (build_root_xml_node,
                                                         build_child_xml_node)


class L3_interfaces(ConfigBase):
    """
    The junos_l3_interfaces class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'l3_interfaces',
    ]

    def __init__(self, module):
        super(L3_interfaces, self).__init__(module)

    def get_l3_interfaces_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(
            self.gather_subset, self.gather_network_resources)
        l3_interfaces_facts = facts['ansible_network_resources'].get(
            'l3_interfaces')
        if not l3_interfaces_facts:
            return []
        return l3_interfaces_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()

        existing_interfaces_facts = self.get_l3_interfaces_facts()

        config_xmls = self.set_config(existing_interfaces_facts)
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

        changed_interfaces_facts = self.get_l3_interfaces_facts()

        result['before'] = existing_interfaces_facts
        if result['changed']:
            result['after'] = changed_interfaces_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_l3_interfaces_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_l3_interfaces_facts
        resp = self.set_state(want, have)
        return to_list(resp)

    def set_state(self, want, have):
        """ Select the appropriate function based on the state provided

        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the list xml configuration necessary to migrate the current
                  configuration
                  to the desired configuration
        """
        root = build_root_xml_node('interfaces')
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
            root.append(xml)

        return tostring(root)

    def _get_common_xml_node(self, name):
        root_node = build_root_xml_node('interface')
        build_child_xml_node(root_node, 'name', name)
        intf_unit_node = build_child_xml_node(root_node, 'unit')
        return root_node, intf_unit_node

    def _state_replaced(self, want, have):
        """ The xml generator when state is replaced

        :rtype: A list
        :returns: the xml necessary to migrate the current configuration
                  to the desired configuration
        """
        intf_xml = []
        intf_xml.extend(self._state_deleted(want, have))
        intf_xml.extend(self._state_merged(want, have))
        return intf_xml

    def _state_overridden(self, want, have):
        """ The xml generator when state is overridden

        :rtype: A list
        :returns: the xml necessary to migrate the current configuration
                  to the desired configuration
        """
        intf_xml = []
        intf_xml.extend(self._state_deleted(have, have))
        intf_xml.extend(self._state_merged(want, have))
        return intf_xml

    def _state_merged(self, want, have):
        """ The xml generator when state is merged

        :rtype: A list
        :returns: the xml necessary to merge the provided into
                  the current configuration
        """
        intf_xml = []
        for config in want:
            root_node, unit_node = self._get_common_xml_node(config['name'])
            build_child_xml_node(unit_node, 'name',
                                            str(config['unit']))
            if config.get('ipv4'):
                self.build_ipaddr_et(config, unit_node)
            if config.get('ipv6'):
                self.build_ipaddr_et(config, unit_node, protocol='ipv6')
            intf_xml.append(root_node)
        return intf_xml

    def build_ipaddr_et(self, config, unit_node, protocol='ipv4',
                        delete=False):
        family = build_child_xml_node(unit_node, 'family')
        inet = 'inet'
        if protocol == 'ipv6':
            inet = 'inet6'
        ip_protocol = build_child_xml_node(family, inet)
        for ip_addr in config[protocol]:
            if ip_addr['address'] == 'dhcp' and protocol == 'ipv4':
                build_child_xml_node(ip_protocol, 'dhcp')
            else:
                ip_addresses = build_child_xml_node(
                    ip_protocol, 'address')
                build_child_xml_node(
                    ip_addresses, 'name', ip_addr['address'])

    def _state_deleted(self, want, have):
        """ The xml configuration generator when state is deleted

        :rtype: A list
        :returns: the xml configuration necessary to remove the current
                  configuration of the provided objects
        """
        intf_xml = []
        existing_l3_intfs = [l3_intf['name'] for l3_intf in have]

        if not want:
            want = have

        for config in want:
            if config['name'] not in existing_l3_intfs:
                continue
            else:
                root_node, unit_node = self._get_common_xml_node(
                    config['name'])
                build_child_xml_node(unit_node, 'name',
                                                str(config['unit']))
                family = build_child_xml_node(unit_node, 'family')
                ipv4 = build_child_xml_node(family, 'inet')
                intf = next(
                    (intf for intf in have if intf['name'] == config['name']),
                    None)
                if 'ipv4' in intf:
                    if 'dhcp' in [x['address'] for x in intf.get('ipv4') if intf.get('ipv4') is not None]:
                        build_child_xml_node(ipv4, 'dhcp', None, {'delete': 'delete'})
                    else:
                        build_child_xml_node(
                            ipv4, 'address', None, {'delete': 'delete'})
                ipv6 = build_child_xml_node(family, 'inet6')
                build_child_xml_node(ipv6, 'address', None, {'delete': 'delete'})
            intf_xml.append(root_node)
        return intf_xml
