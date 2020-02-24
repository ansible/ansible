#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The eos acls fact class
It is in this file the configuration is collected from the device
for a given resource, parsed, and the facts tree is populated
based on the configuration.
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
from copy import deepcopy

from ansible.module_utils.network.common import utils
from ansible.module_utils.network.eos.argspec.acls.acls import AclsArgs


class AclsFacts(object):
    """ The eos acls fact class
    """

    def __init__(self, module, subspec='config', options='options'):
        self._module = module
        self.argument_spec = AclsArgs.argument_spec
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
        return connection.get('show running-config | section access-list')

    def populate_facts(self, connection, ansible_facts, data=None):
        """ Populate the facts for acls
        :param connection: the device connection
        :param ansible_facts: Facts dictionary
        :param data: previously collected conf
        :rtype: dictionary
        :returns: facts
        """
        if not data:
            data = self.get_device_data(connection)

        # split the config into instances of the resource
        find_pattern = r'(?:^|\n)(?:ip|ipv6) access\-list.*?(?=(?:^|\n)(?:ip|ipv6) access\-list|$)'
        resources = [p for p in re.findall(find_pattern,
                                           data,
                                           re.DOTALL)]

        objs = []
        ipv4list = []
        ipv6list = []
        for resource in resources:
            if "ipv6" in resource:
                ipv6list.append(resource)
            else:
                ipv4list.append(resource)
        ipv4list = ["\n".join(ipv4list)]
        ipv6list = ["\n".join(ipv6list)]
        for resource in ipv4list:
            if resource:
                obj = self.render_config(self.generated_spec, resource)
                if obj:
                    objs.append(obj)
        for resource in ipv6list:
            if resource:
                obj = self.render_config(self.generated_spec, resource)
                if obj:
                    objs.append(obj)

        ansible_facts['ansible_network_resources'].pop('acls', None)
        facts = {}
        if objs:
            facts['acls'] = []
            params = utils.validate_config(self.argument_spec, {'config': objs})
            for cfg in params['config']:
                facts['acls'].append(utils.remove_empties(cfg))

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
        afi_list = []
        acls_list = []
        name_dict = {}
        standard = 0
        operator = ['eq', 'lt', 'neq', 'range', 'gt']
        flags = ['ack', 'established', 'fin', 'psh', 'rst', 'syn', 'urg']
        others = ['hop_limit', 'log', 'ttl', 'fragments', 'tracked']
        for dev_config in conf.split('\n'):
            ace_dict = {}
            if not dev_config:
                continue
            if dev_config == '!':
                continue
            dev_config = dev_config.strip()
            matches = re.findall(r'(ip.*?) access-list (.*)', dev_config)
            if matches:
                afi = "ipv4" if matches[0][0] == "ip" else "ipv6"
                ace_list = []
                if bool(name_dict):
                    acls_list.append(name_dict.copy())
                    name_dict = {}
                if afi not in afi_list:
                    afi_list.append(afi)
                    config.update({"afi": afi})
                if "standard" in matches[0][1]:
                    standard = 1
                    name = matches[0][1].split()
                    name_dict.update({"name": name[1]})
                    name_dict.update({"standard": True})
                else:
                    name_dict.update({"name": matches[0][1]})
            else:
                source_dict = {}
                dest_dict = {}
                dev_config = re.sub('-', '_', dev_config)
                dev_config_remainder = dev_config.split()
                if "fragment_rules" in dev_config:
                    ace_dict.update({"sequence": dev_config_remainder.pop(0)})
                    ace_dict.update({"fragment_rules": True})
                if "remark" in dev_config:
                    ace_dict.update({"sequence": dev_config_remainder.pop(0)})
                    ace_dict.update({"remark": ' '.join(dev_config_remainder[1:])})
                seq = re.search(r'\d+ (permit|deny) .*', dev_config)
                if seq:
                    ace_dict.update({"sequence": dev_config_remainder.pop(0)})
                    ace_dict.update({"grant": dev_config_remainder.pop(0)})
                    if dev_config_remainder[0] == "vlan":
                        vlan_str = ""
                        dev_config_remainder.pop(0)
                        if dev_config_remainder[0] == "inner":
                            vlan_str = dev_config_remainder.pop(0) + " "
                        vlan_str = dev_config_remainder.pop(0) + " " + dev_config_remainder.pop(0)
                        ace_dict.update({"vlan": vlan_str})
                    if not standard:
                        protocol = dev_config_remainder[0]
                        ace_dict.update({"protocol": dev_config_remainder.pop(0)})
                    src_prefix = re.search(r'/', dev_config_remainder[0])
                    src_address = re.search(r'[a-z\d:\.]+', dev_config_remainder[0])
                    if dev_config_remainder[0] == "host":
                        source_dict.update({"host": dev_config_remainder.pop(1)})
                        dev_config_remainder.pop(0)
                    elif dev_config_remainder[0] == "any":
                        source_dict.update({"any": True})
                        dev_config_remainder.pop(0)
                    elif src_prefix:
                        source_dict.update({"subnet_address": dev_config_remainder.pop(0)})
                    elif src_address:
                        source_dict.update({"address": dev_config_remainder.pop(0)})
                        source_dict.update({"wildcard_bits": dev_config_remainder.pop(0)})
                    if dev_config_remainder:
                        if dev_config_remainder[0] in operator:
                            port_dict = {}
                            src_port = ""
                            src_opr = dev_config_remainder.pop(0)
                            portlist = dev_config_remainder[:]
                            for config_remainder in portlist:
                                addr = re.search(r'[\.\:]', config_remainder)
                                if config_remainder == "any" or config_remainder == "host" or addr:
                                    break
                                else:
                                    src_port = src_port + " " + config_remainder
                                    dev_config_remainder.pop(0)
                            src_port = src_port.strip()
                            port_dict.update({src_opr: src_port})
                            source_dict.update({"port_protocol": port_dict})
                    ace_dict.update({"source": source_dict})
                    if not dev_config_remainder or standard:
                        if dev_config_remainder and "log" in dev_config_remainder:
                            ace_dict.update({"log": True})
                        if bool(ace_dict):
                            ace_list.append(ace_dict.copy())
                        if len(ace_list):
                            name_dict = name_dict.copy()
                            name_dict.update({"aces": ace_list[:]})
                        # acls_list.append(name_dict)
                        continue
                    dest_prefix = re.search(r'/', dev_config_remainder[0])
                    dest_address = re.search(r'[a-z\d:\.]+', dev_config_remainder[0])
                    if dev_config_remainder[0] == "host":
                        dest_dict.update({"host": dev_config_remainder.pop(1)})
                        dev_config_remainder.pop(0)
                    elif dev_config_remainder[0] == "any":
                        dest_dict.update({"any": True})
                        dev_config_remainder.pop(0)
                    elif dest_prefix:
                        dest_dict.update({"subnet_address": dev_config_remainder.pop(0)})
                    elif dest_address:
                        dest_dict.update({"address": dev_config_remainder.pop(0)})
                        dest_dict.update({"wildcard_bits": dev_config_remainder.pop(0)})
                    if dev_config_remainder:
                        if dev_config_remainder[0] in operator:
                            port_dict = {}
                            dest_port = ""
                            dest_opr = dev_config_remainder.pop(0)
                            portlist = dev_config_remainder[:]
                            for config_remainder in portlist:
                                if config_remainder in operator or config_remainder in others:
                                    break
                                else:
                                    dest_port = dest_port + " " + config_remainder
                                    dev_config_remainder.pop(0)
                            dest_port = dest_port.strip()
                            port_dict.update({dest_opr: dest_port})
                            dest_dict.update({"port_protocol": port_dict})
                    ace_dict.update({"destination": dest_dict})
                    protocol_option_dict = {}
                    tcp_dict = {}
                    icmp_dict = {}
                    ip_dict = {}
                    if not dev_config_remainder:
                        if bool(ace_dict):
                            ace_list.append(ace_dict.copy())
                        if len(ace_list):
                            name_dict = name_dict.copy()
                            name_dict.update({"aces": ace_list[:]})
                        # acls_list.append(name_dict)
                        continue
                    if protocol == "tcp" or "6":
                        protocol = "tcp"
                        flags_dict = {}
                        if dev_config_remainder[0] in flags:
                            flaglist = dev_config_remainder.copy()
                            for config_remainder in flaglist:
                                if config_remainder not in flags:
                                    break
                                else:
                                    flags_dict.update({config_remainder: True})
                                    dev_config_remainder.pop(0)
                        if bool(flags_dict):
                            tcp_dict.update({"flags": flags_dict})
                    if bool(tcp_dict):
                        protocol_option_dict.update({"tcp": tcp_dict})
                    if protocol == "icmp" or protocol == "icmpv6" \
                            or protocol == "1" or protocol == "58":
                        if protocol == "1":
                            protocol = "icmp"
                        elif protocol == "58":
                            protocol = "icmpv6"
                        if dev_config_remainder[0] not in others:
                            icmp_dict.update({dev_config_remainder[0]: True})
                            dev_config_remainder.pop(0)
                    if bool(icmp_dict):
                        protocol_option_dict.update({protocol: icmp_dict})
                    if protocol == "ip" or "ipv6":
                        if dev_config_remainder[0] == "nexthop_group":
                            dev_config_remainder.pop(0)
                            ip_dict.update({"nexthop_group": dev_config_remainder.pop(0)})
                    if bool(ip_dict):
                        protocol_option_dict.update({protocol: ip_dict})
                    if bool(protocol_option_dict):
                        ace_dict.update({"protocol_options": protocol_option_dict})
                    if dev_config_remainder[0] == "ttl":
                        dev_config_remainder.pop(0)
                        op = dev_config_remainder.pop(0)
                        ttl_dict = {op: dev_config_remainder.pop(0)}
                        ace_dict.update({"ttl": ttl_dict})
                    for config_remainder in dev_config_remainder:
                        if config_remainder in others:
                            if config_remainder == "hop_limit":
                                hop_index = dev_config_remainder.index(config_remainder)
                                hoplimit_dict = {dev_config_remainder[hop_index + 1]: dev_config_remainder[hop_index + 2]}
                                ace_dict.update({"hop_limit": hoplimit_dict})
                                dev_config_remainder.pop(0)
                                continue
                            ace_dict.update({config_remainder: True})
                            dev_config_remainder.pop(0)
                    if dev_config_remainder:
                        config.update({"line": dev_config})
                        return utils.remove_empties(config)
            if bool(ace_dict):
                ace_list.append(ace_dict.copy())
            if len(ace_list):
                name_dict = name_dict.copy()
                name_dict.update({"aces": ace_list[:]})
        acls_list.append(name_dict.copy())
        config.update({"acls": acls_list})
        return utils.remove_empties(config)
