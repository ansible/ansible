#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The junos l3_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

from copy import deepcopy

from ansible.module_utils._text import to_bytes
from ansible.module_utils.network.common import utils
from ansible.module_utils.network.junos.argspec.l3_interfaces.l3_interfaces import L3_interfacesArgs
from ansible.module_utils.six import string_types
try:
    from lxml import etree
    HAS_LXML = True
except ImportError:
    HAS_LXML = False


class L3_interfacesFacts(object):
    """ The junos l3_interfaces fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = L3_interfacesArgs.argument_spec
        spec = deepcopy(self.argument_spec)
        if subspec:
            if options:
                facts_argument_spec = spec[subspec][options]
            else:
                facts_argument_spec = spec[subspec]
        else:
            facts_argument_spec = spec

        self.generated_spec = utils.generate_dict(facts_argument_spec)

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for l3_interfaces
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if not HAS_LXML:
            self._module.fail_json(msg='lxml is not installed.')

        if not data:
            config_filter = """
                <configuration>
                    <interfaces/>
                </configuration>
                """
            data = connection.get_configuration(filter=config_filter)

        if isinstance(data, string_types):
            data = etree.fromstring(to_bytes(data, errors='surrogate_then_replace'))

        resources = data.xpath('configuration/interfaces/interface')

        objs = []
        if resources:
            objs = self.parse_l3_if_resources(resources)

        config = []
        if objs:
            for l3_if_obj in objs:
                config.append(self.render_config(
                    self.generated_spec, l3_if_obj))

        facts = {}
        facts['l3_interfaces'] = config

        ansible_facts['ansible_network_resources'].update(facts)
        return ansible_facts

    def parse_l3_if_resources(self, l3_if_resources):
        l3_ifaces = []
        for iface in l3_if_resources:
            interface = {}
            interface['name'] = iface.find('name').text
            if iface.find('description') is not None:
                interface['description'] = iface.find('description').text
            interface['unit'] = iface.find('unit/name').text
            family = iface.find('unit/family/')
            if family is not None and family.tag != 'ethernet-switching':
                ipv4 = iface.findall('unit/family/inet/address')
                dhcp = iface.findall('unit/family/inet/dhcp')
                ipv6 = iface.findall('unit/family/inet6/address')
                if dhcp:
                    interface['ipv4'] = [{'address': 'dhcp'}]
                if ipv4:
                    interface['ipv4'] = self.get_ip_addresses(ipv4)
                elif not dhcp:
                    interface['ipv4'] = None
                if ipv6:
                    interface['ipv6'] = self.get_ip_addresses(ipv6)
                l3_ifaces.append(interface)
        return l3_ifaces

    def get_ip_addresses(self, ip_addr):
        address_list = []
        for ip in ip_addr:
            for addr in ip:
                address_list.append({'address': addr.text})
        return address_list

    def render_config(self, spec, conf):
        """
        Render config as dictionary structure and delete keys
          from spec for null values

        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        config = deepcopy(spec)
        config['name'] = conf['name']
        config['description'] = conf.get('description')
        config['unit'] = conf.get('unit', 0)
        config['ipv4'] = conf.get('ipv4')
        config['ipv6'] = conf.get('ipv6')

        return utils.remove_empties(config)
