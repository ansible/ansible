#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vyos firewall_interfaces fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

from re import findall, search, M
from copy import deepcopy
from ansible.module_utils.network.common import utils
from ansible.module_utils.network.vyos.argspec.firewall_interfaces.firewall_interfaces import Firewall_interfacesArgs


class Firewall_interfacesFacts(object):
    """ The vyos firewall_interfaces fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = Firewall_interfacesArgs.argument_spec
        spec = deepcopy(self.argument_spec)
        if subspec:
            if options:
                facts_argument_spec = spec[subspec][options]
            else:
                facts_argument_spec = spec[subspec]
        else:
            facts_argument_spec = spec

        self.generated_spec = utils.generate_dict(facts_argument_spec)

    def get_device_data(self, connection):
        return connection.get_config()

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for firewall_interfaces
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if not data:
            # typically data is populated from the current device configuration
            # data = connection.get('show running-config | section ^interface')
            # using mock data instead
            data = self.get_device_data(connection)
        objs = []
        interfaces = findall(r'^set interfaces ethernet (?:\'*)(\S+)(?:\'*)', data, M)
        if interfaces:
            objs = self.get_names(data, interfaces)
        ansible_facts['ansible_network_resources'].pop('firewall_interfaces', None)
        facts = {}
        if objs:
            facts['firewall_interfaces'] = []
            params = utils.validate_config(self.argument_spec, {'config': objs})
            for cfg in params['config']:
                facts['firewall_interfaces'].append(utils.remove_empties(cfg))

        ansible_facts['ansible_network_resources'].update(facts)
        return ansible_facts

    def get_names(self, data, interfaces):
        """
        This function performs following:
        - Form regex to fetch 'interface name' from  interfaces firewall data.
        - Form the name list.
        :param data: configuration.
        :param rules: list of interfaces.
        :return: generated firewall interfaces configuration.
        """
        names = []
        for r in set(interfaces):
            int_regex = r' %s .+$' % r.strip("'")
            cfg = findall(int_regex, data, M)
            fi = self.render_config(cfg)
            fi['name'] = r.strip("'")
            names.append(fi)
        if names:
            names = sorted(names, key=lambda i: i['name'])
        return names

    def render_config(self, conf):
        """
        Render config as dictionary structure and delete keys
          from spec for null values

        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        conf = '\n'.join(filter(lambda x: 'firewall' in x, conf))
        config = {'access_rules': self.parse_access_rules(conf)}
        return config

    def parse_access_rules(self, conf):
        """
        This function forms the regex to fetch the 'access-rules'
        for specific interface.
        :param conf: configuration data.
        :return: generated access-rules list configuration.
        """
        ar_lst = []
        v4_ar = findall(r'^.*(in|out|local) name .*$', conf, M)
        v6_ar = findall(r'^.*(in|out|local) ipv6-name .*$', conf, M)
        if v4_ar:
            v4_conf = "\n".join(findall(r"(^.*?%s.*?$)" % ' name', conf, M))
            config = self.parse_int_rules(v4_conf, 'ipv4')
            if config:
                ar_lst.append(config)
        if v6_ar:
            v6_conf = "\n".join(findall(r"(^.*?%s.*?$)" % ' ipv6-name', conf, M))
            config = self.parse_int_rules(v6_conf, 'ipv6')
            if config:
                ar_lst.append(config)
        if ar_lst:
            ar_lst = sorted(ar_lst, key=lambda i: i['afi'])
        else:
            empty_rules = findall(r'^.*(in|out|local).*', conf, M)
            if empty_rules:
                ar_lst.append({'afi': 'ipv4', 'rules': []})
                ar_lst.append({'afi': 'ipv6', 'rules': []})
        return ar_lst

    def parse_int_rules(self, conf, afi):
        """
        This function forms the regex to fetch the 'access-rules'
        for specific interface based on ip-type.
        :param conf: configuration data.
        :param rules: rules configured per interface.
        :param afi: ip address type.
        :return: generated rule configuration dictionary.
        """
        r_lst = []
        config = {}
        rules = ['in', 'out', 'local']
        for r in set(rules):
            fr = {}
            r_regex = r' %s .+$' % r
            cfg = '\n'.join(findall(r_regex, conf, M))
            if cfg:
                fr = self.parse_rules(cfg, afi)
            else:
                out = search(r'^.*firewall ' + "'" + r + "'" + '(.*)', conf, M)
                if out:
                    fr = {'direction': r}
            if fr:
                r_lst.append(fr)
        if r_lst:
            r_lst = sorted(r_lst, key=lambda i: i['direction'])
            config = {'afi': afi, 'rules': r_lst}
        return config

    def parse_rules(self, conf, afi):
        """
        This function triggers the parsing of 'rule' attributes.
        a_lst is a list having rule attributes which doesn't
        have further sub attributes.
        :param conf: configuration.
        :param afi: ip address type.
        :return: generated rule configuration dictionary.
        """
        cfg = {}
        out = findall(r'[^\s]+', conf, M)
        if out:
            cfg['direction'] = out[0].strip("'")
            if afi == 'ipv6':
                out = findall(r'[^\s]+ ipv6-name (?:\'*)(\S+)(?:\'*)', conf, M)
                if out:
                    cfg['name'] = str(out[0]).strip("'")
            else:
                out = findall(r'[^\s]+ name (?:\'*)(\S+)(?:\'*)', conf, M)
                if out:
                    cfg['name'] = out[-1].strip("'")
        return cfg
