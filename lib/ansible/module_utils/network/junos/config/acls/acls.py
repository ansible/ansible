#
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The junos_acls class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.junos.facts.facts import Facts
from ansible.module_utils.network.junos.junos import (locked_config,
                                                      load_config,
                                                      commit_configuration,
                                                      discard_changes,
                                                      tostring)
from ansible.module_utils.network.common.netconf import (build_root_xml_node,
                                                         build_child_xml_node)


class Acls(ConfigBase):
    """
    The junos_acls class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'acls',
    ]

    def __init__(self, module):
        super(Acls, self).__init__(module)

    def get_acls_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        acls_facts = facts['ansible_network_resources'].get('junos_acls')
        if not acls_facts:
            return []
        return acls_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        warnings = list()

        existing_acls_facts = self.get_acls_facts()
        config_xmls = self.set_config(existing_acls_facts)

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

        result['xml'] = config_xmls
        changed_acls_facts = self.get_acls_facts()

        result['before'] = existing_acls_facts
        if result['changed']:
            result['after'] = changed_acls_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_acls_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        want = self._module.params['config']
        have = existing_acls_facts
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
        root = build_root_xml_node('firewall')
        state = self._module.params['state']
        config_xmls = []
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

    def _state_replaced(self, want, have):
        """ The command generator when state is replaced

        :rtype: A list
        :returns: the xml necessary to migrate the current configuration
                  to the desired configuration
        """
        acls_xml = []
        acls_xml.extend(self._state_deleted(want, have))
        acls_xml.extend(self._state_merged(want, have))
        return acls_xml

    def _state_overridden(self, want, have):
        """ The command generator when state is overridden

        :rtype: A list
        :returns: the xml necessary to migrate the current configuration
                  to the desired configuration
        """
        acls_xml = []
        acls_xml.extend(self._state_deleted(have, have))
        acls_xml.extend(self._state_merged(want, have))
        return acls_xml

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted

        :rtype: A list
        :returns: the xml necessary to migrate the current configuration
                  to the desired configuration
        """
        if not want:
            want = have
        return self._state_merged(want, have, delete={"delete": "delete"})

    def _state_merged(self, want, have, delete=None):
        """ The command generator when state is merged

        :rtype: A list
        :returns: the xml necessary to migrate the current configuration
                  to the desired configuration
        """
        acls_xml = []
        family_node = build_root_xml_node('family')
        for config in want:
            try:
                family = "inet6" if config.pop("afi") == "ipv6" else "inet"
            except KeyError:
                family = "inet"
            inet_node = build_child_xml_node(family_node, family)

            if not config["acls"]:
                if delete:
                    inet_node.attrib.update(delete)
                continue

            needs_delete = False
            if delete:
                # This should ensure that the delete attr gets attached to the deepest level necessary.
                needs_delete = True

            for acl in config["acls"]:
                filter_node = build_child_xml_node(inet_node, 'filter')
                build_child_xml_node(filter_node, 'name', acl['name'])
                if acl.get('aces'):
                    for ace in acl['aces']:
                        term_node = build_child_xml_node(filter_node, 'term')
                        if delete:
                            term_node.attrib.update(delete)
                            needs_delete = False
                            continue

                        build_child_xml_node(term_node, 'name', ace['name'])
                        if ace.get("source") or ace.get('protocol') or ace.get('port'):
                            from_node = build_child_xml_node(term_node, 'from')
                            for direction in ('source', 'destination'):
                                if ace.get(direction):
                                    if ace[direction].get("address"):
                                        build_child_xml_node(from_node, '{0}-address'.format(direction), ace[direction]['address'])
                                    if ace[direction].get("prefix_list"):
                                        build_child_xml_node(from_node, '{0}-prefix-list'.format(direction), ace[direction]['prefix_list'])
                                    if ace[direction].get('port_protocol'):
                                        if "eq" in ace[direction]["port_protocol"]:
                                            build_child_xml_node(from_node, '{0}-port'.format(direction), ace[direction]['port_protocol']['eq'])
                                        elif "range" in ace[direction]["port_protocol"]:
                                            ports = "{0}-{1}".format(ace[direction]["port_protocol"]["start"], ace[direction]["port_protocol"]["end"])
                                            build_child_xml_node(from_node, '{0}-port'.format(direction), ports)
                            if ace.get('protocol'):
                                protocol = [proto for proto in ace["protocol"] if ace["protocol"][proto]][0]
                                if protocol != 'range':
                                    build_child_xml_node(from_node, 'protocol', protocol)
                        if ace.get("grant"):
                            then_node = build_child_xml_node(term_node, "then")
                            if ace["grant"] == "permit":
                                build_child_xml_node(then_node, "accept")
                            if ace["grant"] == "deny":
                                build_child_xml_node(then_node, "discard")
            if needs_delete:
                filter_node.attrib.update(delete)
                needs_delete = False

        acls_xml.append(family_node)
        return acls_xml
