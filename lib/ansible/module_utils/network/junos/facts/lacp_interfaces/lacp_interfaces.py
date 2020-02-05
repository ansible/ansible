#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The junos lacp_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

from copy import deepcopy

from ansible.module_utils._text import to_bytes
from ansible.module_utils.network.common import utils
from ansible.module_utils.network.junos.argspec.lacp_interfaces.lacp_interfaces import Lacp_interfacesArgs
from ansible.module_utils.network.junos.utils.utils import get_resource_config
from ansible.module_utils.six import string_types
try:
    from lxml import etree
    HAS_LXML = True
except ImportError:
    HAS_LXML = False


class Lacp_interfacesFacts(object):
    """ The junos lacp_interfaces fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = Lacp_interfacesArgs.argument_spec
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
        """ Populate the facts for interfaces
        :param connection: the device connection
        :param data: previously collected configuration as lxml ElementTree root instance
                     or valid xml sting
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
            data = get_resource_config(connection, config_filter=config_filter)

        if isinstance(data, string_types):
            data = etree.fromstring(to_bytes(data, errors='surrogate_then_replace'))

        self._resources = data.xpath('configuration/interfaces/interface')

        objs = []
        for resource in self._resources:
            if resource is not None:
                obj = self.render_config(self.generated_spec, resource)
                if obj:
                    objs.append(obj)
        facts = {}
        if objs:
            facts['lacp_interfaces'] = []
            params = utils.validate_config(self.argument_spec, {'config': objs})
            for cfg in params['config']:
                facts['lacp_interfaces'].append(utils.remove_empties(cfg))
        ansible_facts['ansible_network_resources'].update(facts)
        return ansible_facts

    def render_config(self, spec, conf):
        """
        Render config as dictionary structure and delete keys
          from spec for null values
        :param spec: The facts tree, generated from the argspec
        :param conf: The ElementTree instance of configuration object
        :rtype: dictionary
        :returns: The generated config
        """
        config = deepcopy(spec)
        config['name'] = utils.get_xml_conf_arg(conf, 'name')
        config['period'] = utils.get_xml_conf_arg(conf, 'aggregated-ether-options/lacp/periodic')
        config['sync_reset'] = utils.get_xml_conf_arg(conf, 'aggregated-ether-options/lacp/sync-reset')
        force_up = utils.get_xml_conf_arg(conf, 'ether-options/ieee-802.3ad/lacp/force-up', data='tag')
        if force_up:
            config['force_up'] = True
        config['port_priority'] = utils.get_xml_conf_arg(conf, 'ether-options/ieee-802.3ad/lacp/port-priority')
        config['system']['priority'] = utils.get_xml_conf_arg(conf, 'aggregated-ether-options/lacp/system-priority')
        address = utils.get_xml_conf_arg(conf, 'aggregated-ether-options/lacp/system-id')
        if address:
            config['system'].update({'mac': {'address': address}})

        lacp_intf_cfg = utils.remove_empties(config)
        # if lacp config is not present for interface return empty dict
        if len(lacp_intf_cfg) == 1:
            return {}
        else:
            return lacp_intf_cfg
