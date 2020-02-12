#
# -*- coding: utf-8 -*-
# Copyright 2020 Allied Telesis
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The awplus lldp_global fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import re
from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.awplus.argspec.lldp_global.lldp_global import Lldp_globalArgs


class Lldp_globalFacts(object):
    """ The awplus lldp_global fact class
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

    def get_lldp_facts(self, connection):
        return connection.get('show lldp')

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for lldp_global
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        objs = dict()
        if not data:
            data = self.get_lldp_facts(connection)
        # operate on a collection of resource x
        config = data.split('\n')
        for conf in config:
            if conf:
                obj = self.render_config(self.generated_spec, conf)
                if obj:
                    objs.update(obj)
        facts = {}

        if objs:
            params = utils.validate_config(
                self.argument_spec, {'config': utils.remove_empties(objs)})
            facts['lldp_global'] = utils.remove_empties(params['config'])
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

        holdtime = re.search(r'Hold-time Multiplier \D+ (\d+)', conf)
        if holdtime:
            config['holdtime'] = int(holdtime.group(1))

        timer = re.search(r'Tx Timer Interval \D+ (\d+)', conf)
        if timer:
            config['timer'] = int(timer.group(1))

        reinit = re.search(r'Reinitialization Delay \D+ (\d+)', conf)
        if reinit:
            config['reinit'] = int(reinit.group(1))

        enabled = re.search(r'LLDP Status \W+ (\w+)', conf)
        if enabled:
            if enabled.group(1) == 'Enabled':
                config['enabled'] = True
            else:
                config['enabled'] = False

        return utils.remove_empties(config)
