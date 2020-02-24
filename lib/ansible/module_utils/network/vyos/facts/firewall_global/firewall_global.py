#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The vyos firewall_global fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type

from copy import deepcopy
from re import findall, search, M
from ansible.module_utils.network.common import utils
from ansible.module_utils.network.vyos.argspec.firewall_global.firewall_global import Firewall_globalArgs


class Firewall_globalFacts(object):
    """ The vyos firewall_global fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = Firewall_globalArgs.argument_spec
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
        """ Populate the facts for firewall_global
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
        objs = {}
        firewalls = findall(r'^set firewall .*$', data, M)
        if firewalls:
            objs = self.render_config(firewalls)
        facts = {}
        params = utils.validate_config(self.argument_spec, {'config': objs})
        facts['firewall_global'] = utils.remove_empties(params['config'])
        ansible_facts['ansible_network_resources'].update(facts)
        return ansible_facts

    def render_config(self, conf):
        """
        Render config as dictionary structure and delete keys
          from spec for null values

        :param spec: The facts tree, generated from the argspec
        :param conf: The configuration
        :rtype: dictionary
        :returns: The generated config
        """
        conf = '\n'.join(filter(lambda x: ('firewall ipv6-name' and 'firewall name' not in x), conf))

        a_lst = ['config_trap', 'validation', 'log_martians', 'syn_cookies', 'twa_hazards_protection']
        firewall = self.parse_attr(conf, a_lst)
        f_sub = {'ping': self.parse_ping(conf),
                 'group': self.parse_group(conf),
                 'route_redirects': self.route_redirects(conf),
                 'state_policy': self.parse_state_policy(conf)}
        firewall.update(f_sub)
        return firewall

    def route_redirects(self, conf):
        """
        This function forms the regex to fetch the afi and invoke
        functions to fetch route redirects and source routes
        :param conf: configuration data.
        :return: generated rule list configuration.
        """
        rr_lst = []

        v6_attr = findall(r'^set firewall (?:ipv6-src-route|ipv6-receive-redirects) (\S+)', conf, M)
        if v6_attr:
            obj = self.parse_rr_attrib(conf, 'ipv6')
            if obj:
                rr_lst.append(obj)

        v4_attr = findall(r'^set firewall (?:ip-src-route|receive-redirects|send-redirects) (\S+)', conf, M)
        if v4_attr:
            obj = self.parse_rr_attrib(conf, 'ipv4')
            if obj:
                rr_lst.append(obj)
        return rr_lst

    def parse_rr_attrib(self, conf, attrib=None):
        """
        This function fetches the 'ip_src_route'
        invoke function to parse icmp redirects.
        :param conf: configuration to be parsed.
        :param attrib: 'ipv4/ipv6'.
        :return: generated config dictionary.
        """

        cfg_dict = self.parse_attr(conf, ['ip_src_route'], type=attrib)
        cfg_dict['icmp_redirects'] = self.parse_icmp_redirects(conf, attrib)
        cfg_dict['afi'] = attrib
        return cfg_dict

    def parse_icmp_redirects(self, conf, attrib=None):
        """
        This function triggers the parsing of 'icmp_redirects' attributes.
        :param conf: configuration to be parsed.
        :param attrib: 'ipv4/ipv6'.
        :return: generated config dictionary.
        """
        a_lst = ['send', 'receive']
        cfg_dict = self.parse_attr(conf, a_lst, type=attrib)
        return cfg_dict

    def parse_ping(self, conf):
        """
        This function triggers the parsing of 'ping' attributes.
        :param conf: configuration to be parsed.
        :return: generated config dictionary.
        """
        a_lst = ['all', 'broadcast']
        cfg_dict = self.parse_attr(conf, a_lst)
        return cfg_dict

    def parse_state_policy(self, conf):
        """
        This function fetched the connecton type and invoke
        function to parse other state-policy attributes.
        :param conf: configuration data.
        :return: generated rule list configuration.
        """
        sp_lst = []
        attrib = 'state-policy'
        policies = findall(r'^set firewall ' + attrib + ' (\\S+)', conf, M)

        if policies:
            rules_lst = []
            for sp in set(policies):
                sp_regex = r' %s .+$' % sp
                cfg = '\n'.join(findall(sp_regex, conf, M))
                obj = self.parse_policies(cfg, sp)
                obj['connection_type'] = sp
                if obj:
                    rules_lst.append(obj)
            sp_lst = sorted(rules_lst, key=lambda i: i['connection_type'])
        return sp_lst

    def parse_policies(self, conf, attrib=None):
        """
        This function triggers the parsing of policy attributes
        action and log.
        :param conf: configuration
        :param attrib: connection type.
        :return: generated rule configuration dictionary.
        """
        a_lst = ['action', 'log']
        cfg_dict = self.parse_attr(conf, a_lst, match=attrib)
        return cfg_dict

    def parse_group(self, conf):
        """
        This function triggers the parsing of 'group' attributes.
        :param conf: configuration.
        :return: generated config dictionary.
        """
        cfg_dict = {}
        cfg_dict['port_group'] = self.parse_group_lst(conf, 'port-group')
        cfg_dict['address_group'] = self.parse_group_lst(conf, 'address-group')
        cfg_dict['network_group'] = self.parse_group_lst(conf, 'network-group')
        return cfg_dict

    def parse_group_lst(self, conf, type):
        """
        This function fetches the name of group and invoke function to
        parse group attributes'.
        :param conf: configuration data.
        :param type: type of group.
        :return: generated group list configuration.
        """
        g_lst = []

        groups = findall(r'^set firewall group ' + type + ' (\\S+)', conf, M)
        if groups:
            rules_lst = []
            for gr in set(groups):
                gr_regex = r' %s .+$' % gr
                cfg = '\n'.join(findall(gr_regex, conf, M))
                obj = self.parse_groups(cfg, type, gr)
                obj['name'] = gr.strip("'")
                if obj:
                    rules_lst.append(obj)
            g_lst = sorted(rules_lst, key=lambda i: i['name'])
        return g_lst

    def parse_groups(self, conf, type, name):
        """
        This function fetches the description and invoke
        the parsing of group members.
        :param conf: configuration.
        :param type: type of group.
        :param name: name of group.
        :return: generated configuration dictionary.
        """
        a_lst = ['name', 'description']
        group = self.parse_attr(conf, a_lst)
        key = self.get_key(type)
        r_sub = {key[0]: self.parse_address_port_lst(conf, name, key[1])}
        group.update(r_sub)
        return group

    def parse_address_port_lst(self, conf, name, key):
        """
        This function forms the regex to fetch the
        group members attributes.
        :param conf: configuration data.
        :param name: name of group.
        :param key: key value.
        :return: generated member list configuration.
        """
        l_lst = []
        attribs = findall(r'^.*' + name + ' ' + key + ' (\\S+)', conf, M)
        if attribs:
            for attr in attribs:
                if key == 'port':
                    l_lst.append({"port": attr.strip("'")})
                else:
                    l_lst.append({"address": attr.strip("'")})
        return l_lst

    def parse_attr(self, conf, attr_list, match=None, type=None):
        """
        This function peforms the following:
        - Form the regex to fetch the required attribute config.
        - Type cast the output in desired format.
        :param conf: configuration.
        :param attr_list: list of attributes.
        :param match: parent node/attribute name.
        :return: generated config dictionary.
        """
        config = {}
        for attrib in attr_list:
            regex = self.map_regex(attrib, type)
            if match:
                regex = match + ' ' + regex
            if conf:
                if self.is_bool(attrib):
                    attr = self.map_regex(attrib, type)
                    out = conf.find(attr.replace("_", "-"))
                    dis = conf.find(attr.replace("_", "-") + " 'disable'")
                    if out >= 1:
                        if dis >= 1:
                            config[attrib] = False
                        else:
                            config[attrib] = True
                else:
                    out = search(r'^.*' + regex + ' (.+)', conf, M)
                    if out:
                        val = out.group(1).strip("'")
                        if self.is_num(attrib):
                            val = int(val)
                        config[attrib] = val
        return config

    def get_key(self, type):
        """
        This function map the group type to
        member type
        :param type:
        :return:
        """
        key = ()
        if type == 'port-group':
            key = ('members', 'port')
        elif type == 'address-group':
            key = ('members', 'address')
        elif type == 'network-group':
            key = ('members', 'network')
        return key

    def map_regex(self, attrib, type=None):
        """
        - This function construct the regex string.
        - replace the underscore with hyphen.
        :param attrib: attribute
        :return: regex string
        """
        regex = attrib.replace("_", "-")
        if attrib == 'all':
            regex = 'all-ping'
        elif attrib == 'disabled':
            regex = 'disable'
        elif attrib == 'broadcast':
            regex = 'broadcast-ping'
        elif attrib == 'send':
            if type == 'ipv6':
                regex = 'ipv6-send-redirects'
            else:
                regex = 'send-redirects'
        elif attrib == 'ip_src_route':
            if type == 'ipv6':
                regex = 'ipv6-src-route'
        elif attrib == 'receive':
            if type == 'ipv6':
                regex = 'ipv6-receive-redirects'
            else:
                regex = 'receive-redirects'
        return regex

    def is_num(self, attrib):
        """
        This function looks for the attribute in predefined integer type set.
        :param attrib: attribute.
        :return: True/false.
        """
        num_set = ('time', 'code', 'type', 'count', 'burst', 'number')
        return True if attrib in num_set else False

    def get_src_route(self, attrib):
        """
        This function looks for the attribute in predefined integer type set.
        :param attrib: attribute.
        :return: True/false.
        """
        return 'ipv6_src_route' if attrib == 'ipv6' else 'ip_src_route'

    def is_bool(self, attrib):
        """
        This function looks for the attribute in predefined bool type set.
        :param attrib: attribute.
        :return: True/False
        """
        bool_set = ('all',
                    'log',
                    'send',
                    'receive',
                    'broadcast',
                    'config_trap',
                    'log_martians',
                    'syn_cookies',
                    'ip_src_route',
                    'twa_hazards_protection')
        return True if attrib in bool_set else False
