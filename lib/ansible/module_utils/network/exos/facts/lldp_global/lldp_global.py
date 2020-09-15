#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The exos lldp_global fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re
from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.exos.argspec.lldp_global.lldp_global \
    import Lldp_globalArgs
from ansible.module_utils.network.exos.exos import send_requests


class Lldp_globalFacts(object):
    """ The exos lldp_global fact class
    """

    TLV_SELECT_OPTIONS = [
        "SYSTEM_NAME",
        "SYSTEM_DESCRIPTION",
        "SYSTEM_CAPABILITIES",
        "MANAGEMENT_ADDRESS",
        "PORT_DESCRIPTION"]

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
        """ Populate the facts for lldp_global
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if not data:
            request = {
                "path": "/rest/restconf/data/openconfig-lldp:lldp/config/",
                "method": "GET",
            }
            data = send_requests(self._module, request)

        obj = {}
        if data:
            lldp_obj = self.render_config(self.generated_spec, data[0])
            if lldp_obj:
                obj = lldp_obj

        ansible_facts['ansible_network_resources'].pop('lldp_global', None)
        facts = {}

        params = utils.validate_config(self.argument_spec, {'config': obj})
        facts['lldp_global'] = params['config']

        ansible_facts['ansible_network_resources'].update(facts)
        return ansible_facts

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
        config['interval'] = conf["openconfig-lldp:config"]["hello-timer"]

        for item in self.TLV_SELECT_OPTIONS:
            config["tlv_select"][item.lower()] = (
                False if (item in conf["openconfig-lldp:config"]["suppress-tlv-advertisement"])
                else True)

        return utils.remove_empties(config)
