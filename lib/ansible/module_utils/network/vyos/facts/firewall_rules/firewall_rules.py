#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vyos firewall_rules fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type
import q
from re import findall, search, M
from copy import deepcopy
from ansible.module_utils.network.common import utils
from ansible.module_utils.network.vyos.argspec.firewall_rules.firewall_rules import Firewall_rulesArgs


class Firewall_rulesFacts(object):
    """ The vyos firewall_rules fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = Firewall_rulesArgs.argument_spec
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
        """ Populate the facts for firewall_rules
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if connection:  # just for linting purposes, remove
            pass

        if not data:
            # typically data is populated from the current device configuration
            # data = connection.get('show running-config | section ^interface')
            # using mock data instead
            data = connection.get_config()

        # split the config into instances of the resource
        objs = []
        rules = findall(r'(set firewall ipv6-name|set firewall name) (\S+)', data, M)
        if rules:
            for r in set(rules):
                route_regex = r' %s .+$' % r[1]
                cfg = findall(route_regex, data, M)
                config = self.render_config(self.generated_spec, cfg)
            if config:
                objs.append(config)

        ansible_facts['ansible_network_resources'].pop('firewall_rules', None)
        facts = {}
        if objs:
            facts['firewall_rules'] = []
            params = utils.validate_config(self.argument_spec, {'config': objs})
            for cfg in params['config']:
                facts['firewall_rules'].append(utils.remove_empties(cfg))

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
        q(config)
        q(conf)
        rules = []
        r_num = '\n'.join(filter(lambda x: ('rule' in x), conf))
        des = '\n'.join(filter(lambda x: ('description' in x), conf))
        act = '\n'.join(filter(lambda x: ('action' in x), conf))
        #dest = '\n'.join(filter(lambda x: ('destination' in x), conf))

        rule = {'number': self.parse_num(r_num), 'description': self.parse_num(des),
                'action': self.parse_act(r_num)}
        rules.append(rule)

        return rules

    def parse_act(self, conf):
        if conf:
            act = search(r'^.*rule.*action (.\S+)', conf, M)
            value = act.group(1).strip("'")
            return value

    def parse_num(self, conf):
        if conf:
            num = search(r'^.*rule (.\S+)', conf, M)
            value = num.group(1).strip("'")
        return int(value)

    def parse_des(self, conf):
        if conf:
            des = search(r'^.*rule.*description (.\S+)', conf, M)
            value = des.group(1).strip("'")
        return value

