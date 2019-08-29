#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The junos lldp fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

from copy import deepcopy

from ansible.module_utils._text import to_bytes
from ansible.module_utils.network.common import utils
from ansible.module_utils.network.junos.argspec.lldp_global.lldp_global import Lldp_globalArgs
from ansible.module_utils.network.junos.utils.utils import get_resource_config
from ansible.module_utils.six import string_types
try:
    from lxml import etree
    HAS_LXML = True
except ImportError:
    HAS_LXML = False


class Lldp_globalFacts(object):
    """ The junos lldp fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = Lldp_globalArgs.argument_spec
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
                    <protocols>
                        <lldp>
                        </lldp>
                    </protocols>
                </configuration>
                """
            data = get_resource_config(connection, config_filter=config_filter)

        if isinstance(data, string_types):
            data = etree.fromstring(to_bytes(data, errors='surrogate_then_replace'))

        facts = {}
        config = deepcopy(self.generated_spec)
        resources = data.xpath('configuration/protocols/lldp')
        if resources:
            lldp_root = resources[0]
            config['address'] = utils.get_xml_conf_arg(lldp_root, 'management-address')
            config['interval'] = utils.get_xml_conf_arg(lldp_root, 'advertisement-interval')
            config['transmit_delay'] = utils.get_xml_conf_arg(lldp_root, 'transmit-delay')
            config['hold_multiplier'] = utils.get_xml_conf_arg(lldp_root, 'hold-multiplier')
            if utils.get_xml_conf_arg(lldp_root, 'disable', data='tag'):
                config['enable'] = False

        params = utils.validate_config(self.argument_spec, {'config': utils.remove_empties(config)})

        facts['lldp_global'] = utils.remove_empties(params['config'])
        ansible_facts['ansible_network_resources'].update(facts)

        return ansible_facts
