# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
lookup: pfsense
author: Frederic Bor (@f-bor)
version_added: "2.9"
short_description: Generate pfSense aliases, rules and rule_separators
description:
- This lookup plugin is designed to be used with pfsense_aggregate module.
  It takes a yaml file and generate list of aliases and rules definitions.
  The aim is to be able to easily manage a fleet of pfSenses and avoiding any
  redundant work, like defining the sames hosts/ports aliases or rules
  on multiples pfSenses. The plugin determine what is required to be defined
  on each pfsense, leaving to the network administrator only the task of updating
  the yaml definition file.
options:
  file:
    description: The yaml file defining the network
  type:
    description: What to generate
    choices:
      - aliases
      - rules
      - rule_separators
"""

EXAMPLES = """
- name: Get all aliases to be defined
  debug:
    aliases: "{{ lookup('pfsense', 'all_pf_defs.yml', 'aliases') }}"

- name: Get all rules to be defined
  debug:
    rules: "{{ lookup('pfsense', 'all_pf_defs.yml', 'rules') }}"

- name: Get all rule_separators to be defined
  debug:
    rule_separators: "{{ lookup('pfsense', 'all_pf_defs.yml', 'rule_separators') }}"

"""

RETURN = """
  _list:
    description:
      - list of dictonaries with aliases, rules or rule_separators
    type: list
"""

"""
To determine if a rule and corresponding aliases has to be declared on a pfsense
and on which interfaces, the plugin check if rule source or destination is
matching any local or routed network on the pfsense. To avoid having every rule
declared on a wan interface, 0.0.0.0/0 is considered as an internet only network,
excluding any private network address. If a network is declared as
routed (accessible thru) on an interface and is also defined as the local network
on an interface of the target pfsense, it is automaticly removed (it allows easy
routing declaration). The same apply to adjacent networks, which indicates neighbor
networks that are routed thru a pfSense.

Following pfSense rule definition (one host/alias per source/destination,
one port/alias per source/destination), each rule declared in the yaml is breaked
into smaller rules until having rules than can be declared.

The generated rules order follows the yaml file rules order.

Rule separators name are taken from parent rules' groups (see 'ADMIN', 'VOIP',
'MISC' or 'ACTIVE DIRECTORY' in the example below). Nested groups generate separators
names in the form 'GROUP1 - GROUP2 - ...'

You can define a default value for all rules and subrules of a separator using
the name 'options'. The parameters supported this way are gateway, log, queue, ackqueue,
in_queue and out_queue. You can override those default values setting other values
on a deeper options set or inside the rule definition.

You can use an extra parameter in rules and options, filter, to restrict the rule
generation only to the pfsenses set in this parameter.

The yaml file must include the following definitions to describe the network topology:
- pfsenses
- rules
- hosts_aliases
- ports_aliases

You can run the plugin alone to debug rules and aliases generation, for example:
- ./lookup_plugins/pfsense.py defs.yml pf1
- ./lookup_plugins/pfsense.py defs.yml pf1 ping_from_poc3

A typical pfsense_aggregate task using the lookup plugin will look like this:
  tasks:
    - name: "setup aliases & rules"
      pfsense_aggregate:
        purge_aliases: true
        purge_rules: true
        purge_rule_separators: true
        aggregated_aliases: |
          {{ lookup('pfsense', 'defs.yml', 'aliases') }}
        aggregated_rules: |
          {{ lookup('pfsense', 'defs.yml', 'rules') }}
        aggregated_rule_separators: |
          {{ lookup('pfsense', 'defs.yml', 'rule_separators') }}


Here is an example of yaml file:
---

pfsenses:
  pf1:          {
    interfaces: {
      lan: { ip: 192.168.1.1/24, adjacent_networks: lan_data_poc4 },
      lan_100: { ip: 172.16.1.1/24 },
      vpn: { routed_networks: lan_data_all lan_voip_all},
      }
    }

  pf2:          {
    interfaces: {
      lan: { ip: 192.168.2.1/24 },
      lan_100: { ip: 172.16.2.1/24 },
      vpn: { routed_networks: lan_data_all lan_voip_all},
      }
    }

  pf3:          {
    interfaces: {
      bridge_lan: { ip: 192.168.3.1/24, routed_networks: lan_data_all, bridge: True },
      bridge_lan_100: { ip: 172.16.3.1/24, routed_networks: lan_voip_all, bridge: True },
      wan: { routed_networks: 0.0.0.0/0 }
      }
    }

rules:
  options: { log: yes }

  ADMIN:
    antilock_out: { src: any, dst: any, protocol: tcp, dst_port: port_ssh port_http 443 }
    admin_bypass: { src: srv_admin, dst: any }
    MISC:
      ping_from_poc3: { src: lan_poc3_all, dst: srv_admin, protocol: icmp }

  VOIP:
    voip_conf_tftp: { src: all_ipbx, dst: lan_voip_all, dst_port: 69, protocol: udp }

  ACTIVE DIRECTORY:
    ads_to_ads_tcp: { src: all_ads, dst: all_ads, dst_port: port_dns port_ldap port_ldap_ssl, protocol: tcp }
    ads_to_ads_udp: { src: all_ads, dst: all_ads, dst_port: port_dns port_ldap, protocol: udp }

  DNS:
    options: { log: no }
    any_to_local_dns: {src: any, dst: all_ads, dst_port: port_dns, protocol: udp }

hosts_aliases:
  # hosts
  ipbx_poc1: { ip: 172.16.1.3 }
  ipbx_poc2: { ip: 172.16.2.3 }
  ipbx_poc3: { ip: 172.16.3.3 }
  all_ipbx: { ip: ipbx_poc1 ipbx_poc2 ipbx_poc3 }

  ad_poc1: { ip: 192.168.1.3 }
  ad_poc2: { ip: 192.168.2.3 }
  ad_poc3: { ip: 192.168.3.3 }
  all_ads: { ip: ad_poc1 ad_poc2 ad_poc3 }

  # networks
  lan_voip_poc1: { ip: 172.16.1.0/24 }
  lan_voip_poc2: { ip: 172.16.2.0/24 }
  lan_voip_poc3: { ip: 172.16.3.0/24 }
  lan_voip_all : { ip: lan_voip_poc1 lan_voip_poc2 lan_voip_poc3 }

  lan_data_poc1: { ip: 192.168.1.0/24 }
  lan_data_poc2: { ip: 192.168.2.0/24 }
  lan_data_poc3: { ip: 192.168.3.0/24 }
  lan_data_poc4: { ip: 192.168.4.0/24 }
  lan_data_all : { ip: lan_data_poc1 lan_data_poc2 lan_data_poc3 lan_data_poc4 }

  lan_poc3_all : { ip: lan_voip_poc3 lan_data_poc3 }

  srv_admin: { ip: 192.168.1.165 }

ports_aliases:
  port_ssh: { port: 22 }
  port_telnet: { port: 23 }
  port_dns: { port: 51 }
  port_http: { port: 80 }
  port_ldap: { port: 389 }
  port_ldap_ssl: { port: 636 }

 """

from copy import copy, deepcopy
from collections import OrderedDict
from ansible.utils.display import Display

import json
import re
import sys
import yaml

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils.compat import ipaddress

OPTION_FIELDS = ['gateway', 'log', 'queue', 'ackqueue', 'in_queue', 'out_queue', 'filter']
OUTPUT_OPTION_FIELDS = ['gateway', 'log', 'queue', 'ackqueue', 'in_queue', 'out_queue']

display = Display()


def to_unicode(string):
    """ return a unicode representation of string if required """
    if sys.version_info[0] >= 3:
        return string
    return string.decode("utf-8")


def ordered_load(stream, loader_cls=yaml.Loader, object_pairs_hook=OrderedDict):
    """ load and return yaml data from stream using ordered dicts """

    class OrderedLoader(loader_cls):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)


def static_vars(**kwargs):
    """ static decorator to declare static vars """

    def decorate(func):
        """ static decorator func """
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate


@static_vars(
    classA=ipaddress.IPv4Network((u"10.0.0.0", u"255.0.0.0")),
    classB=ipaddress.IPv4Network((u"172.16.0.0", u"255.240.0.0")),
    classC=ipaddress.IPv4Network((u"192.168.0.0", u"255.255.0.0")))
def is_private_ip(address):
    """ check if ip address is class A, B or C """
    if not isinstance(address, ipaddress.IPv4Address):
        ip_address = ipaddress.ip_address(to_unicode(address))
    else:
        ip_address = address
    return ip_address in is_private_ip.classA or ip_address in is_private_ip.classB or ip_address in is_private_ip.classC


@static_vars(
    classA=ipaddress.IPv4Network((u"10.0.0.0", u"255.0.0.0")),
    classB=ipaddress.IPv4Network((u"172.16.0.0", u"255.240.0.0")),
    classC=ipaddress.IPv4Network((u"192.168.0.0", u"255.255.0.0")))
def is_private_network(address):
    """ check if network is class A, B or C """
    if not isinstance(address, ipaddress.IPv4Network):
        net = ipaddress.ip_network(to_unicode(address))
    else:
        net = address
    return net.subnet_of(is_private_network.classA) or net.subnet_of(is_private_network.classB) or net.subnet_of(is_private_network.classC)


@static_vars(ip_broadcast=ipaddress.IPv4Address((u"255.255.255.255")))
def is_ip_broadcast(address):
    """ check if ip address is ip broadcast address """
    if not isinstance(address, ipaddress.IPv4Address):
        ip_address = ipaddress.ip_address(to_unicode(address))
    else:
        ip_address = address
    return ip_address == is_ip_broadcast.ip_broadcast


def is_valid_ip(address):
    """ validate ip address format """
    try:
        ipaddress.ip_address(to_unicode(address))
        return True
    except ValueError:
        return False
    return False


def is_valid_port(port):
    """ validate port format """
    if not port.isdigit():
        return False

    nport = int(port)
    return nport >= 0 and nport <= 65535


def is_valid_port_range(port_range):
    """ validate port range format """
    group = re.match(r'^(\d+)-(\d+)$', port_range)
    if not group:
        return False
    nport1 = int(group.group(1))
    nport2 = int(group.group(2))

    return nport1 >= 0 and nport1 <= 65535 and nport2 >= 0 and nport2 <= 65535


def is_valid_network(address):
    """ validate network address format """
    try:
        ipaddress.ip_network(to_unicode(address))
        return True
    except ValueError:
        return False
    return False


def rule_product_dict(tab, rule, field, out_field=None):
    """ Return cartesian product between rule[field] and tab as dicts """
    if field not in rule:
        return tab
    if not out_field:
        out_field = field
    out = []
    for new_val in rule[field].split(' '):
        for existing_val in tab:
            obj = deepcopy(existing_val)
            obj[out_field] = new_val
            out.append(obj)

    return out


def rule_product_ports(rule, field, field_port):
    """ Return cartesian product between rule[field] and field_port as string """
    if field_port not in rule:
        return rule[field]

    aliases = rule[field].split(' ')
    ports = rule[field_port].split(' ')
    ret = []
    for alias in aliases:
        added = False
        for port in ports:
            if port:
                ret.append(alias + ":" + port)
                added = True
        if not added:
            ret.append(alias)

    return ' '.join(list(ret))


class PFSenseHostAlias(object):
    """ Class holding structured pfsense host alias definition """
    def __init__(self):
        self.name = None
        self.descr = None
        self.definition = []
        self.ips = []
        self.networks = []
        self.fake_alias_ip = False
        self.fake_alias_network = False

        # define all interfaces on which the alias may be defined as a local source
        # interfaces['gw_poc1_1'] = ['lan', 'obs']
        self.local_interfaces = {}

        # define all interfaces on which the alias may be defined as a routed source
        self.routed_interfaces = {}

    def compute_any(self, data):
        """ Do all computations for object 'any' """
        # we add all interfaces of all pfsenses
        for pfsense in data.pfsenses_obj.values():
            for interface in pfsense.interfaces.values():
                self.local_interfaces[pfsense.name].append(interface.name)
                self.routed_interfaces[pfsense.name].append(interface.name)

    def compute_all(self, data):
        """ Do all computations """
        if self.name != 'any':
            self.compute_addresses(data)
            self.compute_local_interfaces(data)
            self.compute_routed_interfaces(data)

    def compute_addresses(self, data):
        """ Convert all aliases to structured ip addresses or networks """
        todo = []
        todo.extend(self.definition)

        while todo:
            address = todo.pop()

            try:
                host_ip = ipaddress.ip_address(to_unicode(address))
                self.ips.append(host_ip)
                continue
            except ValueError:
                pass

            try:
                net = ipaddress.ip_network(to_unicode(address))
                self.networks.append(net)
                continue
            except ValueError:
                pass

            if address not in data.all_aliases:
                raise AssertionError("Invalid address: " + address + " for " + self.name)

            todo.extend(data.all_aliases[address]['ip'].split(' '))

    def _is_in_networks(self, interface, fcheckname):
        """ check if an alias is in a network of an interface """
        fcheck = getattr(interface, fcheckname)
        for alias_ip in self.ips:
            if is_ip_broadcast(alias_ip):
                continue

            if not fcheck(alias_ip):
                return False

        for alias_net in self.networks:
            if not fcheck(alias_net):
                return False
        return True

    def is_in_local_network(self, interface):
        """ check if an alias is in the local network of an interface """
        return self._is_in_networks(interface, 'local_network_contains')

    def is_in_routed_networks(self, interface):
        """ check if an alias is in the routed networks of an interface """
        return self._is_in_networks(interface, 'routed_networks_contains')

    def is_in_adjacent_networks(self, interface):
        """ check if an alias is in the adjacent networks of an interface """
        return self._is_in_networks(interface, 'adjacent_networks_contains')

    def compute_routed_interfaces(self, data):
        """ Find all interfaces on all pfsense where the alias may be used as a routed source """
        for pfsense in data.pfsenses_obj.values():
            self.routed_interfaces[pfsense.name] = set()
            for alias_ip in self.ips:
                interfaces = pfsense.interfaces_routed_networks_contains(alias_ip)
                self.routed_interfaces[pfsense.name].update(interfaces)

            for alias_net in self.networks:
                interfaces = pfsense.interfaces_routed_networks_contains(alias_net)
                self.routed_interfaces[pfsense.name].update(interfaces)

    def compute_local_interfaces(self, data):
        """ Find all interfaces on all pfsense where the alias may be used as a local source """
        for pfsense in data.pfsenses_obj.values():
            self.local_interfaces[pfsense.name] = set()
            for alias_ip in self.ips:
                interfaces = pfsense.interfaces_local_networks_contains(alias_ip)
                self.local_interfaces[pfsense.name].update(interfaces)

            for alias_net in self.networks:
                interfaces = pfsense.interfaces_local_networks_contains(alias_net)
                self.local_interfaces[pfsense.name].update(interfaces)

    def is_whole_local(self, pfsense):
        """ check if all ips/networks match a local network interface in pfense """
        for alias_ip in self.ips:
            if is_ip_broadcast(alias_ip):
                continue

            if not pfsense.any_local_network_contains(alias_ip):
                return False

        for alias_net in self.networks:
            if not pfsense.any_local_network_contains(alias_net):
                return False

        return True

    def routed_by_interfaces(self, pfsense):
        """ return all interfaces for which all ips/networks match a adjacent/routed network in pfense """
        interfaces = set()
        for interface in pfsense.interfaces.values():
            all_found = True
            # we must found a routing network for each ip
            for alias_ip in self.ips:
                if not interface.adjacent_networks_contains(alias_ip) and not interface.routed_networks_contains(alias_ip):
                    all_found = False
                    break

            # we must found a routing network for each network
            for alias_net in self.networks:
                if not interface.adjacent_networks_contains(alias_net) and not interface.routed_networks_contains(alias_net):
                    all_found = False
                    break

            if all_found:
                interfaces.add(interface.name)
        return interfaces

    def is_adjacent_or_routed(self, pfsense):
        """ check if all ips/networks are in a adjacent/routed network in pfense """
        for alias_ip in self.ips:
            if not pfsense.any_routed_networks_contains(alias_ip) and not pfsense.any_adjacent_networks_contains(alias_ip):
                return False

        for alias_net in self.networks:
            if not pfsense.any_routed_networks_contains(alias_net) and not pfsense.any_adjacent_networks_contains(alias_net):
                return False

        return True

    def is_ip_broadcast(self):
        """ check if an alias is the ip_broadcast """
        if len(self.ips) != 1 or self.networks:
            return False
        return is_ip_broadcast(self.ips[0])

    def is_whole_in_pfsense(self, pfsense):
        """ check if all ips/networks have as least one interface in pfense """
        for alias_ip in self.ips:
            if is_ip_broadcast(alias_ip):
                return False

            if not pfsense.any_network_contains(alias_ip):
                return False

        for alias_net in self.networks:
            if not pfsense.any_network_contains(alias_net):
                return False

        return True

    def is_whole_not_in_pfsense(self, pfsense):
        """ check if all ips/networks have as least one interface in pfense """
        for alias_ip in self.ips:
            if is_ip_broadcast(alias_ip):
                return False
            if pfsense.any_network_contains(alias_ip):
                return False

        for alias_net in self.networks:
            if pfsense.any_network_contains(alias_net):
                return False

        return True

    def is_whole_in_same_routing_ifaces(self, pfsense):
        """ check if all ips/networks have the same interfaces in pfense """

        # first, we check remote networks
        target_ar_interfaces = None
        for alias_ip in self.ips:
            interfaces = pfsense.interfaces_adjacent_or_routed_networks_contains(alias_ip)
            if not target_ar_interfaces:
                target_ar_interfaces = interfaces
            elif target_ar_interfaces ^ interfaces:
                return False

        for alias_net in self.networks:
            interfaces = pfsense.interfaces_adjacent_or_routed_networks_contains(alias_net)
            if not target_ar_interfaces:
                target_ar_interfaces = interfaces
            elif target_ar_interfaces ^ interfaces:
                return False

        # then, local networks
        target_local_interfaces = None
        for alias_ip in self.ips:
            interfaces = pfsense.interfaces_local_networks_contains(alias_ip)
            if not target_local_interfaces:
                target_local_interfaces = interfaces
            elif target_local_interfaces ^ interfaces:
                return False

        for alias_net in self.networks:
            interfaces = pfsense.interfaces_local_networks_contains(alias_net)
            if not target_local_interfaces:
                target_local_interfaces = interfaces
            elif target_local_interfaces ^ interfaces:
                return False

        # if we are on local and remote, split
        if target_local_interfaces and target_ar_interfaces:
            return False

        return True

    def match_local_interface_ip(self, pfsense):
        """ Return True if the alias ip match one interface on the pfsense """
        for alias_ip in self.ips:
            for iface in pfsense.interfaces.values():
                if alias_ip == iface.local_ip:
                    return True
        return False


class PFSenseRule(object):
    """ Class holding structured pfsense rule declaration """
    def __init__(self):
        self.name = None
        self.separator = None
        self.src = []
        self.src_port = []
        self.dst = []
        self.dst_port = []
        self.protocol = []
        self.action = "pass"
        self.options = dict()

        self.sub_rules = []
        self.interfaces = None
        self.generated_names = {}

    def get_option(self, name):
        """ return option value for name """
        if name in self.options:
            return self.options[name]
        separator = self.separator
        while separator is not None:
            if separator.options is not None and name in separator.options:
                return separator.options[name]
            separator = separator.parent
        return None

    def to_json(self):
        """ return JSON String containing rule """
        srcs = []
        for src in self.src:
            srcs.append(src.name)

        dsts = []
        for dst in self.dst:
            dsts.append(dst.name)

        res = self.name + ": { src: " + " ".join(srcs) + ", dst: " + " ".join(dsts)

        if self.src_port:
            res += ", src_port: " + " ".join(self.src_port)

        if self.dst_port:
            res += ", dst_port: " + " ".join(self.dst_port)

        if self.protocol:
            res += ", protocol: " + " ".join(self.protocol)

        if self.action != "pass":
            res += ", action: " + " ".join(self.action)

        for field in OUTPUT_OPTION_FIELDS:
            value = self.get_option(field)
            if value is not None:
                res += ', {0}: {1}'.format(field, value)

        res += " }"
        return res


class PFSenseRuleSeparator(object):
    """ Class holding structured pfsense rule separator declaration """
    def __init__(self):
        self.name = None
        self.interface = None
        self.parent = None
        self.options = None

    def __hash__(self):
        return hash(self.name + self.interface)

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.name == other.name and self.interface == other.interface


class PFSenseInterface(object):
    """ Class holding structured pfsense interface definition """
    def __init__(self):
        self.name = None
        self.local_ip = None
        self.local_network = None
        self.routed_networks = set()
        self.adjacent_networks = set()
        self.bridge = False

    @staticmethod
    def _networks_contains(address, networks):
        """ return true if address is into networks """
        if isinstance(address, ipaddress.IPv4Address):
            private_address = is_private_ip(address)
            for snet in networks:
                private_net = is_private_network(snet)
                if private_address and private_net or not private_address and not private_net:
                    if address in snet:
                        return True
        elif isinstance(address, ipaddress.IPv4Network):
            private_address = is_private_network(address)
            for snet in networks:
                private_net = is_private_network(snet)
                if private_address and private_net or not private_address and not private_net:
                    if address.subnet_of(snet):
                        return True
        else:
            raise AssertionError('wrong type in routed_networks_contains:' + type(address))
        return False

    def routed_networks_contains(self, address):
        """ return true if address is routed on this interface """
        return self._networks_contains(address, self.routed_networks)

    def adjacent_networks_contains(self, address):
        """ return true if address is routed on this interface """
        return self._networks_contains(address, self.adjacent_networks)

    def local_network_contains(self, address):
        """ return true if address is in the local network of this interface """
        if self.local_network:
            if isinstance(address, ipaddress.IPv4Address):
                private_address = is_private_ip(address)
                private_net = is_private_network(self.local_network)
                if private_address and private_net or not private_address and not private_net:
                    return address in self.local_network
                return False
            elif isinstance(address, ipaddress.IPv4Network):
                private_address = is_private_network(address)
                private_net = is_private_network(self.local_network)
                if private_address and private_net or not private_address and not private_net:
                    return address.subnet_of(self.local_network)
            else:
                raise AssertionError('wrong type in local_network_contains:' + type(address))
        return False


class PFSense(object):
    """ Class holding structured pfsense definition """
    def __init__(self, name, interfaces):
        self.name = name
        self.interfaces = interfaces

    def any_adjacent_networks_contains(self, address):
        """ return true if address is in adjacent networks of any interface """
        return len(self.interfaces_adjacent_networks_contains(address)) != 0

    def any_routed_networks_contains(self, address):
        """ return true if address is in routed networks of any interface """
        return len(self.interfaces_routed_networks_contains(address)) != 0

    def any_local_network_contains(self, address):
        """ return true if address is in the local network of any interface """
        return len(self.interfaces_local_networks_contains(address)) != 0

    def any_network_contains(self, address):
        """ return true if address is in the local or routed networks of any interface """
        return self.any_local_network_contains(address) or self.any_routed_networks_contains(address) or self.any_adjacent_networks_contains(address)

    def _interfaces_network_contains(self, address, networks_name):
        """ return interfaces names where address is in the interface network  """
        res = set()
        if isinstance(address, ipaddress.IPv4Address):
            private_address = is_private_ip(address)
            for interface in self.interfaces.values():
                networks = getattr(interface, networks_name)
                if networks is not None:
                    if not isinstance(networks, set):
                        networks = [networks]
                    for snet in networks:
                        private_net = is_private_network(snet)
                        if private_address and private_net or not private_address and not private_net:
                            if address in snet:
                                res.add(interface.name)
        elif isinstance(address, ipaddress.IPv4Network):
            private_address = is_private_network(address)
            for interface in self.interfaces.values():
                networks = getattr(interface, networks_name)
                if networks is not None:
                    if not isinstance(networks, set):
                        networks = [networks]
                    for snet in networks:
                        private_net = is_private_network(snet)
                        if private_address and private_net or not private_address and not private_net:
                            if address.subnet_of(snet):
                                res.add(interface.name)
        else:
            raise AssertionError('wrong type in _interfaces_network_contains:' + type(address))
        return res

    def interfaces_local_networks_contains(self, address):
        """ return interfaces names where address is in the interface local network  """
        return self._interfaces_network_contains(address, 'local_network')

    def interfaces_routed_networks_contains(self, address):
        """ return interfaces names where address is in the interface routed networks  """
        return self._interfaces_network_contains(address, 'routed_networks')

    def interfaces_adjacent_networks_contains(self, address):
        """ return interfaces names where address is in the interface adjacent networks  """
        return self._interfaces_network_contains(address, 'adjacent_networks')

    def interfaces_adjacent_or_routed_networks_contains(self, address):
        """ return interfaces names where address are in the interface local or routed networks """
        res = self.interfaces_routed_networks_contains(address)
        res.update(self.interfaces_adjacent_networks_contains(address))
        return res


class PFSenseData(object):
    """ Class holding all data """

    def __init__(self, hosts_aliases, ports_aliases, pfsenses, rules, target_name):
        self._hosts_aliases = hosts_aliases
        self._ports_aliases = ports_aliases
        self._pfsenses = pfsenses
        self._rules = rules
        self._rules_separators = list()
        self._target_name = target_name
        self._rules_obj = OrderedDict()
        self._pfsenses_obj = {}
        self._hosts_aliases_obj = OrderedDict()
        self._target = None
        self._errors = []
        self.log_errors = False
        self._all_aliases = copy(self._hosts_aliases)
        self._all_aliases.update(self._ports_aliases)

    @property
    def all_aliases(self):
        """ all_aliases getter """
        return self._all_aliases

    @property
    def hosts_aliases(self):
        """ hosts_aliases getter """
        return self._hosts_aliases

    @property
    def hosts_aliases_obj(self):
        """ hosts_aliases_obj getter """
        return self._hosts_aliases_obj

    @property
    def ports_aliases(self):
        """ ports_aliases getter """
        return self._ports_aliases

    @property
    def pfsenses(self):
        """ pfsenses getter """
        return self._pfsenses

    @property
    def pfsenses_obj(self):
        """ pfsenses_obj getter """
        return self._pfsenses_obj

    @property
    def rules_obj(self):
        """ rules_obj getter """
        return self._rules_obj

    @property
    def rules(self):
        """ rules getter """
        return self._rules

    @property
    def rules_separators(self):
        """ rules_separators getter """
        return self._rules_separators

    @property
    def target_name(self):
        """ target_name getter """
        return self._target_name

    @property
    def target(self):
        """ target getter """
        return self._target

    @target.setter
    def target(self, target):
        """ target setter """
        self._target = target

    @property
    def errors(self):
        """ errors getter """
        return self._errors

    def set_error(self, error):
        """ add an error """
        display.error(error)
        self._errors.append(error)

    @staticmethod
    def is_child_def(values):
        """ check if values contains more definitions """
        for value in values.values():
            if isinstance(value, (OrderedDict, dict, list)):
                return False
        return True

    def unalias_ip(self, alias):
        """ expand alias to it's ip definition """
        ret = []
        todo = []
        todo.extend(alias.split(' '))

        while todo:
            elts = todo.pop()
            if elts in self._all_aliases:
                todo.extend(self._all_aliases[elts]['ip'].split(' '))
            else:
                ret.append(elts)

        return ret


class PFSenseDataParser(object):
    """ Class doing all data checks and pfsense objects generation """

    def __init__(self, data):
        self._data = data

    @staticmethod
    def check_alias_name(name):
        """ check an alias name """
        # todo: check reserved keywords (any, self, ...)
        if re.match('^[a-zA-Z0-9_]+$', name) is None:
            raise AnsibleError(name + ': the name of the alias may only consist of the characters "a-z, A-Z, 0-9 and _"')

    def parse_host_alias(self, obj, src_name, type_name, name, allow_any):
        """ Parse an host alias definition """
        ret = True
        value = obj[src_name]
        values = str(value).split(' ')
        if not values:
            self._data.set_error("Empty " + src_name + " field for " + type_name + " " + name)
            return False

        # we check that all exists
        net_defs = 0
        for value in values:
            if is_valid_ip(value):
                self._data.hosts_aliases_obj[value] = self.create_obj_host_alias(value)
                continue

            if is_valid_network(value):
                self._data.hosts_aliases_obj[value] = self.create_obj_host_alias(value)
                net_defs = net_defs + 1
                continue

            if value not in self._data.hosts_aliases and (value != 'any' or not allow_any):
                self._data.set_error(value + " is not a valid alias, ip address or network in " + type_name + " " + name)
                ret = False

        # if it's a real alias, we must check for mixed network definitions
        if not allow_any:
            if net_defs > 0:
                if net_defs != len(values):
                    self._data.set_error("mixed network definitions and aliases or IP addresses in " + type_name + " " + name)
                    ret = False
                else:
                    obj['type'] = 'network'
            else:
                obj['type'] = 'host'

        return ret

    def parse_hosts_aliases(self):
        """ Parse all hosts aliases definitions """
        dups = {}
        ret = True
        for name, alias in self._data.hosts_aliases.items():
            self.check_alias_name(name)

            # ip field is mandatory
            if 'ip' not in alias:
                self._data.set_error("No ip field for alias " + name)
                ret = False
                continue

            # we check that all fields are valid
            for field in alias:
                if field != 'ip' and field != 'descr':
                    self._data.set_error(field + " is not a valid field name in alias " + name)
                    ret = False

            # we check that all ip exist and are not empty
            if not self.parse_host_alias(alias, 'ip', 'alias', name, False):
                ret = False
                continue

            # we check for duplicates
            _alias = deepcopy(alias)
            if 'descr' in _alias:
                del _alias['descr']
            dup = json.dumps(_alias)
            if dup in dups:
                display.warning("duplicate alias definition for ip " + alias['ip'] + " (" + dups[dup] + ", " + name + ")")
            else:
                dups[dup] = name

            obj = PFSenseHostAlias()
            obj.name = name
            obj.definition = alias['ip'].split(' ')
            if 'descr' in alias:
                obj.descr = alias['descr']
            self._data.hosts_aliases_obj[name] = obj

        return ret

    def check_port_alias(self, ports, src_name, type_name, name):
        """ Checking a port alias definition """
        ret = True
        values = str(ports).split(' ')
        if not values:
            self._data.set_error("Empty " + src_name + " field for " + type_name + " " + name)
            return False

        # we check that all exists
        for value in values:
            if not is_valid_port(value) and not is_valid_port_range(value) and value not in self._data.ports_aliases:
                self._data.set_error(value + " is not a valid alias, port or port range in " + type_name + " " + name)
                ret = False

        return ret

    def parse_ports_aliases(self):
        """ Checking all ports alias definitions """
        dups = {}
        ret = True
        for name, alias in self._data.ports_aliases.items():
            self.check_alias_name(name)

            # port field is mandatory
            if 'port' not in alias:
                self._data.set_error("No port field for alias " + name)
                ret = False
                continue

            if not isinstance(alias['port'], str):
                alias['port'] = str(alias['port'])

            # we check that all ip exist and are not empty
            if not self.check_port_alias(alias['port'], 'port', 'alias', name):
                ret = False
                continue

            # we check that all fields are valid
            for field in alias:
                if field != 'port' and field != 'descr':
                    self._data.set_error(field + " is not a valid field name in alias " + name)
                    ret = False

            # we check for duplicates
            _alias = deepcopy(alias)
            if 'descr' in _alias:
                del _alias['descr']
            dup = json.dumps(_alias)
            if dup in dups:
                display.warning("duplicate alias definition for port " + alias['port'] + " (" + dups[dup] + ", " + name + ")")
            else:
                dups[dup] = name

        return ret

    def create_obj_any_alias(self):
        """ Create a PFSenseHostAlias object for address any (for easier processing later) """
        obj = PFSenseHostAlias()
        obj.name = 'any'
        obj.definition = ['any']
        obj.fake_alias_network = True
        obj.compute_any(self._data)

        self._data.all_aliases['any'] = {}
        self._data.all_aliases['any']['ip'] = '0.0.0.0/0'
        self._data.all_aliases['any']['type'] = 'network'

        return obj

    def create_obj_host_alias(self, src):
        """ Create a PFSenseHostAlias object from address (for easier processing later) """
        obj = PFSenseHostAlias()
        obj.name = src
        obj.definition = [src]
        if is_valid_ip(src):
            obj.fake_alias_ip = True
            obj.compute_all(self._data)
        elif is_valid_network(src):
            obj.fake_alias_network = True
            obj.compute_all(self._data)
        elif src == 'any':
            return self.create_obj_any_alias()
        else:
            raise AssertionError("Invalid alias: " + src)

        return obj

    def create_obj_rule_from_def(self, name, rule, separator):
        """ Create a PFSenseRule object from yaml definition """
        obj = PFSenseRule()
        obj.name = name
        obj.separator = separator

        if 'src_port' in rule:
            if not isinstance(rule['src_port'], str):
                obj.src_port = str(rule['src_port'])
            else:
                obj.src_port = rule['src_port'].split(' ')

        if 'dst_port' in rule:
            if not isinstance(rule['dst_port'], str):
                obj.dst_port = str(rule['dst_port'])
            else:
                obj.dst_port = rule['dst_port'].split(' ')

        if 'protocol' in rule:
            obj.protocol = rule['protocol'].split(' ')

        if 'action' in rule:
            obj.action = rule['action']

        for field in OPTION_FIELDS:
            if field in rule:
                obj.options[field] = rule[field]

        for src in rule['src'].split(' '):
            if src not in self._data.hosts_aliases_obj:
                self._data.hosts_aliases_obj[src] = self.create_obj_host_alias(src)
            target = self._data.hosts_aliases_obj[src]
            obj.src.append(target)

        for dst in rule['dst'].split(' '):
            if dst not in self._data.hosts_aliases_obj:
                self._data.hosts_aliases_obj[dst] = self.create_obj_host_alias(dst)
            target = self._data.hosts_aliases_obj[dst]
            obj.dst.append(target)

        return obj

    def parse_rules(self, parent=None, parent_separator=None):
        """ Parse all rules definitions """
        ret = True
        if parent is None:
            parent = self._data.rules
        if parent_separator is None:
            parent_separator = PFSenseRuleSeparator()

        for name, rule in parent.items():
            # not a rule
            if not self._data.is_child_def(rule):
                separator = PFSenseRuleSeparator()
                separator.parent = parent_separator
                if parent_separator.name is None:
                    separator.name = name
                else:
                    separator.name = parent_separator.name + ' - ' + name
                self._data.rules_separators.append(separator)
                if not self.parse_rules(rule, separator):
                    ret = False
                continue
            elif name == 'options':
                parent_separator.options = rule
                continue

            # src field is mandatory
            if 'src' not in rule:
                self._data.set_error("No src field for rule " + name)
                ret = False
                continue

            # we check that all src exist and are not empty
            if not self.parse_host_alias(rule, 'src', 'rule', name, True):
                ret = False

            # dst field is mandatory
            if 'dst' not in rule:
                self._data.set_error("No dst field for rule " + name)
                ret = False
                continue

            # we check that all dst exist and are not empty
            if not self.parse_host_alias(rule, 'dst', 'rule', name, True):
                ret = False

            # checking ports
            if 'src_port' in rule:
                if not isinstance(rule['src_port'], str):
                    rule['src_port'] = str(rule['src_port'])

                if not self.check_port_alias(rule['src_port'], 'src_port', 'rule', name) or not self.check_tcp_udp(rule, name):
                    ret = False

            if 'dst_port' in rule:
                if not isinstance(rule['dst_port'], str):
                    rule['dst_port'] = str(rule['dst_port'])

                if not self.check_port_alias(rule['dst_port'], 'dst_port', 'rule', name) or not self.check_tcp_udp(rule, name):
                    ret = False

            # we check that all fields are valid
            valid_fields = ['src', 'dst', 'src_port', 'dst_port', 'protocol', 'action']
            valid_fields.extend(OPTION_FIELDS)
            for field in rule:
                if field not in valid_fields:
                    self._data.set_error(field + " is not a valid field name in rule " + name)
                    ret = False

            self._data.rules_obj[name] = self.create_obj_rule_from_def(name, rule, parent_separator)

        return ret

    def parse_target_name(self):
        """ Parse target's name definition """
        if self._data.target_name not in self._data.pfsenses:
            self._data.set_error(self._data.target_name + " does not exist in pfsenses section")
            return False
        self._data.target = self._data.pfsenses_obj[self._data.target_name]
        return True

    def check_tcp_udp(self, rule, name):
        """ check if protocol is valid when ports are sets """
        if 'protocol' not in rule:
            return True
        protocols = str(rule['protocol']).split(' ')
        for protocol in protocols:
            if protocol != 'udp' and protocol != 'tcp' and protocol != 'tcp/udp':
                self._data.set_error(protocol + " protocol used with src_port or dst_port in rule " + name)
                return False
        return True

    def check_pfsense_interfaces_objs(self, interfaces, name):
        """ Checking all interfaces networks between them """
        for src_name, src in interfaces.items():
            for dst_name, dst in interfaces.items():
                if src_name != dst_name and src.local_network is not None and dst.local_network is not None and src.local_network.overlaps(dst.local_network):
                    self._data.set_error("Local networks of " + src_name + " and " + dst_name + " overlap in " + name)
                    return False

                # we remove the local networks from the routed_networks of other interfaces
                if src.local_network:
                    todo = dst.routed_networks
                    dst.routed_networks = set()
                    while todo:
                        network = todo.pop()
                        if network.prefixlen == 0:
                            dst.routed_networks.add(network)
                        elif network.compare_networks(src.local_network) == 0:
                            pass
                        elif src.local_network.subnet_of(network):
                            new_networks = set(network.address_exclude(src.local_network))
                            todo.update(new_networks)
                        elif network.overlaps(src.local_network):
                            self._data.set_error("Local network of " + src_name + " overlaps with routed network "
                                                 + network.exploded + " of " + dst_name + " in " + name)
                            return False
                        else:
                            dst.routed_networks.add(network)

                # we remove the adjacent networks from the routed_networks of other interfaces
                todo = dst.routed_networks
                dst.routed_networks = set()
                while todo:
                    network = todo.pop()
                    if network.prefixlen == 0:
                        dst.routed_networks.add(network)
                    else:
                        to_add = True
                        for adjacent_network in src.adjacent_networks:
                            if network.compare_networks(adjacent_network) == 0:
                                to_add = False
                            elif adjacent_network.subnet_of(network):
                                to_add = False
                                new_networks = set(network.address_exclude(adjacent_network))
                                todo.update(new_networks)
                            elif network.overlaps(adjacent_network):
                                self._data.set_error("Adjacent network of " + src_name + " overlaps with routed network "
                                                     + network.exploded + " of " + dst_name + " in " + name)
                                return False
                        if to_add:
                            dst.routed_networks.add(network)

        return True

    def parse_pfsense_interfaces(self, pfsense, name):
        """ Parse all pfsense interfaces definitions """
        ret = {}
        for iname, interface in pfsense['interfaces'].items():
            # extracting & checking local network
            local_ip = None
            local_network = None
            if 'ip' in interface:
                try:
                    local_network = ipaddress.ip_network(to_unicode(interface['ip']), False)
                except ValueError:
                    self._data.set_error("Invalid network " + interface['ip'] + " in " + name)
                    ret = {}
                    break

                if local_network.prefixlen == 32:
                    self._data.set_error("Invalid network prefix length for network " + interface['ip'] + " in " + name)
                    ret = {}
                    break

                # extracting & checking ip
                group = re.match(r'([^\/]*)\/(\d+)', interface['ip'])
                try:
                    local_ip = ipaddress.ip_address(to_unicode(group.group(1)))
                except ValueError:
                    self._data.set_error("Invalid ip " + interface['ip'] + " in " + name)
                    ret = {}
                    break

            # extracting & checking routed networks
            routed_networks = set()
            if 'routed_networks' in interface:
                networks = self._data.unalias_ip(interface['routed_networks'])
                for network in networks:
                    try:
                        routed_networks.add(ipaddress.ip_network(to_unicode(network)))
                    except ValueError:
                        self._data.set_error("Invalid network " + network + " in routed_networks of " + name)
                        return {}

            # extracting & checking adjacent networks
            adjacent_networks = set()
            if 'adjacent_networks' in interface:
                networks = self._data.unalias_ip(interface['adjacent_networks'])
                for network in networks:
                    try:
                        adjacent_networks.add(ipaddress.ip_network(to_unicode(network)))
                    except ValueError:
                        self._data.set_error("Invalid network " + network + " in adjacent_networks of " + name)
                        return {}

            obj = PFSenseInterface()
            obj.name = iname
            obj.local_ip = local_ip
            obj.local_network = local_network
            obj.bridge = (interface.get('bridge'))
            obj.routed_networks = routed_networks
            obj.adjacent_networks = adjacent_networks
            ret[iname] = obj

        if not self.check_pfsense_interfaces_objs(ret, name):
            ret = {}

        return ret

    def parse_pfsenses(self):
        """ Checking all pfsenses definitions """
        dups = {}
        ret = True
        for name, pfsense in self._data.pfsenses.items():
            # interfaces field is mandatory
            if 'interfaces' not in pfsense:
                self._data.set_error("No interfaces field for pfsense " + name)
                ret = False
                continue

            if not pfsense['interfaces']:
                self._data.set_error("Empty interfaces field for pfsense " + name)
                ret = False
                continue

            interfaces = self.parse_pfsense_interfaces(pfsense, name)
            # checking interfaces
            if not interfaces:
                ret = False
                continue

            # we check that all fields are valid
            for field in pfsense:
                if field != 'interfaces':
                    self._data.set_error(field + " is not a valid field name in pfsense " + name)
                    ret = False

            # we check for duplicates
            _pfsense = deepcopy(pfsense)
            if 'descr' in _pfsense:
                del _pfsense['descr']
            dup = json.dumps(_pfsense)
            if dup in dups:
                display.warning("duplicate pfsense definition for ip " + pfsense['ip'] + " (" + dups[dup] + ", " + name + ")")
            else:
                dups[dup] = name

            obj = PFSense(name, interfaces)
            self._data.pfsenses_obj[obj.name] = obj

        return ret

    def parse_hosts_aliases_objs(self):
        """ Checking all host alias objs, addresses and finding pfsenses interfaces """
        for obj in self._data.hosts_aliases_obj.values():
            obj.compute_all(self._data)

        return True

    def parse(self):
        """ Check and parse everything """
        ret = True
        ret = ret and self.parse_hosts_aliases()
        ret = ret and self.parse_ports_aliases()
        ret = ret and self.parse_rules()
        ret = ret and self.parse_pfsenses()
        ret = ret and self.parse_target_name()
        ret = ret and self.parse_hosts_aliases_objs()

        return ret


class PFSenseRuleDecomposer(object):
    """ Class decomposing rules into smaller rules (more suited to pfsense logic ) """

    def __init__(self, data):
        self._data = data

    def host_separate(self, host):
        """ separate aliases to remove mixed configuration
        where there is a local and remote network/ip is the host
        host is expanded to sub-aliases if required """
        ret = []
        if host.is_whole_not_in_pfsense(self._data.target):
            ret.append(host)
        elif host.is_whole_in_pfsense(self._data.target):
            ret.append(host)
        elif host.is_ip_broadcast():
            ret.append(host)
        else:
            alias = self._data.all_aliases[host.name]
            if 'ip' in alias:
                for alias_ip in alias['ip'].split(' '):
                    ret_n = self.host_separate(self._data.hosts_aliases_obj[alias_ip])
                    ret.extend(ret_n)

        return ret

    def host_separate_by_iface(self, host):
        """ separate aliases to remove mixed configuration
        where there is a local and remote network/ip is the host
        host is expanded to sub-aliases if required """
        ret = []
        if host.is_whole_in_same_routing_ifaces(self._data.target):
            ret.append(host)
        else:
            alias = self._data.all_aliases[host.name]
            if 'ip' in alias:
                for alias_ip in alias['ip'].split(' '):
                    ret_n = self.host_separate_by_iface(self._data.hosts_aliases_obj[alias_ip])
                    ret.extend(ret_n)

        return ret

    def separate_aliases(self, rule, field, attr, func):
        """ Separate aliases from field using func, setting new aliases in attr """
        sub_rules = []
        function = getattr(self, func)
        src_sep = function(field)
        if len(src_sep) > 1:
            for src in src_sep:
                new_rule = deepcopy(rule)
                setattr(new_rule, attr, [src])
                sub_rules.append(new_rule)

        return sub_rules

    def decompose_rule(self, rule):
        """ Returns smaller rules from rule """
        # A PFSense rule can have only one src or dst
        blocking = rule.action != 'pass'

        sub_rules = []
        if len(rule.src) > 1 or len(rule.dst) > 1:
            for src in rule.src:
                for dst in rule.dst:
                    new_rule = deepcopy(rule)
                    new_rule.src = [src]
                    new_rule.dst = [dst]
                    sub_rules.append(new_rule)

            return sub_rules

        if len(rule.src) != 1 or len(rule.dst) != 1:
            raise AssertionError()

        src = rule.src[0]
        dst = rule.dst[0]

        # if it's blocking or reject rule, we don't split the destination
        # since only we only need the source to know how to define the rule
        sub_rules = self.separate_aliases(rule, src, 'src', 'host_separate')
        if not blocking and not sub_rules:
            sub_rules = self.separate_aliases(rule, dst, 'dst', 'host_separate')
        if not sub_rules:
            sub_rules = self.separate_aliases(rule, src, 'src', 'host_separate_by_iface')
        if not blocking and not sub_rules:
            sub_rules = self.separate_aliases(rule, dst, 'dst', 'host_separate_by_iface')

        return sub_rules

    def decompose_rules(self):
        """ Returns smaller rules (more suited to pfsense logic ) """
        for rule in self._data.rules_obj.values():
            todo = []
            todo.append(rule)
            while todo:
                obj = todo.pop()
                res = self.decompose_rule(obj)
                if not res:
                    rule.sub_rules.append(obj)
                else:
                    todo.extend(res)


class PFSenseAliasFactory(object):
    """ Class generating aliases definitions """

    def __init__(self, data):
        self._data = data

    def add_host_alias_rec(self, alias, aliases):
        """ set aliases hosts names to define (recursive) """
        name = alias.name
        aliases[name] = self._data.all_aliases[name]
        for target in alias.definition:
            obj = self._data.hosts_aliases_obj[target]
            if obj.fake_alias_ip or obj.fake_alias_network:
                continue
            self.add_host_alias_rec(obj, aliases)

    def add_port_alias_rec(self, alias, aliases):
        """ Return aliases ports names to define (recursive) """
        if alias in self._data.all_aliases:
            if alias not in aliases:
                aliases[alias] = self._data.all_aliases[alias]

            if 'port' in aliases[alias]:
                for port in aliases[alias]['port'].split(' '):
                    self.add_port_alias_rec(port, aliases)

    def add_hosts_aliases(self, rule, aliases):
        """ Return aliases hosts names to define """
        for alias in rule.src:
            if alias.fake_alias_ip or alias.fake_alias_network:
                continue
            self.add_host_alias_rec(alias, aliases)

        for alias in rule.dst:
            if alias.fake_alias_ip or alias.fake_alias_network:
                continue
            self.add_host_alias_rec(alias, aliases)

    def add_ports_aliases(self, rule, aliases):
        """ Return aliases ports names to define """
        for alias in rule.src_port:
            self.add_port_alias_rec(alias, aliases)

        for alias in rule.dst_port:
            self.add_port_alias_rec(alias, aliases)

    def generate_aliases(self, rule_filter=None):
        """ Return aliases definitions for pfsense_aggregate """

        hosts_aliases = {}
        ports_aliases = {}

        for name, rule in self._data.rules_obj.items():
            if rule_filter is not None and name != rule_filter:
                continue
            for subrule in rule.sub_rules:
                if not subrule.interfaces:
                    continue
                self.add_hosts_aliases(subrule, hosts_aliases)
                self.add_ports_aliases(subrule, ports_aliases)

        ret = []
        for name, alias in hosts_aliases.items():
            definition = {}
            definition['name'] = name
            definition['type'] = alias['type']
            definition['address'] = alias['ip']
            definition['state'] = 'present'
            if 'descr' in alias:
                definition['descr'] = alias['descr']
            ret.append(definition)

        for name, alias in ports_aliases.items():
            definition = {}
            definition['name'] = name
            definition['type'] = 'port'
            definition['address'] = alias['port'].replace('-', ':')
            definition['state'] = 'present'
            if 'descr' in alias:
                definition['descr'] = alias['descr']
            ret.append(definition)

        return ret

    @staticmethod
    def output_aliases(aliases):
        """ Output aliases definitions for pfsense_aggregate """
        print("          #===========================")
        print("          # Hosts & network aliases")
        print("          # ")
        for alias in aliases:
            if alias['type'] == 'port':
                continue
            definition = "          - { name: \"" + alias['name'] + "\", type: \"" + alias['type'] + "\", address: \"" + alias['address'] + "\""
            if 'descr' in alias:
                definition = definition + ", descr: \"" + alias['descr'] + "\""
            definition = definition + ", state: \"present\" }"
            print(definition)

        print("          #===========================")
        print("          # ports aliases")
        print("          # ")
        for alias in aliases:
            if alias['type'] != 'port':
                continue
            definition = "          - { name: \"" + alias['name'] + "\", type: \"port\", address: \"" + alias['address'] + "\""
            if 'descr' in alias:
                definition = definition + ", descr: \"" + alias['descr'] + "\""
            definition = definition + ", state: \"present\" }"
            print(definition)


class PFSenseRuleFactory(object):
    """ Class generating rules definitions """

    def __init__(self, data, display_warnings=True):
        self._data = data
        self._decomposer = PFSenseRuleDecomposer(data)
        self._display_warnings = display_warnings

    def rule_interfaces_any(self, rule_obj):
        """ Return interfaces set on which the rule is needed to be defined
            Manage rules with any src or dst """

        src = rule_obj.src[0]
        dst = rule_obj.dst[0]

        if src.name == 'any' and dst.name == 'any':
            # we return all interfaces of target
            return set(self._data.target.interfaces.keys())
        elif src.name == 'any':
            # if the destination is local, we return all interfaces of target
            if dst.is_whole_local(self._data.target):
                return set(self._data.target.interfaces.keys())

            # otherwise we return all interfaces of target if the destination is adjacent/routable
            # (we must be able to reach the destination to allow any src to access it)
            for iface, interface in self._data.target.interfaces.items():
                if dst.is_in_adjacent_networks(interface) or dst.is_in_routed_networks(interface):
                    return set(self._data.target.interfaces.keys())
            return set()

        elif rule_obj.dst[0].name == 'any':
            # we allow the interfaces matching the source ip/networks
            # or the adjacent/routed networks
            interfaces = set()
            for iface, interface in self._data.target.interfaces.items():
                if src.is_in_local_network(interface) or src.is_in_adjacent_networks(interface) or src.is_in_routed_networks(interface):
                    interfaces.add(iface)
            return interfaces
        return None

    def rule_interfaces_ip_broadcast(self, rule_obj):
        """ Return interfaces set on which the rule is needed to be defined
            Manage rules with src or dst ip broadcast """
        src = rule_obj.src[0]
        dst = rule_obj.dst[0]
        src_is_bcast = src.is_ip_broadcast()
        dst_is_bcast = dst.is_ip_broadcast()
        if not src_is_bcast and not dst_is_bcast:
            return None

        if src_is_bcast and rule_obj.dst[0].is_whole_local(self._data.target):
            return rule_obj.dst[0].local_interfaces[self._data.target.name] | rule_obj.dst[0].routed_interfaces[self._data.target.name]

        if rule_obj.src[0].is_whole_local(self._data.target) and dst_is_bcast:
            return rule_obj.src[0].local_interfaces[self._data.target.name] | rule_obj.src[0].routed_interfaces[self._data.target.name]

        # we return no rules for:
        # - broadcast to broadcast
        # - broadcast to remote
        # - remote to broadcast
        return []

    def bridged_by_interfaces(self, routing_interfaces, dst):
        """ if all the routing_interfaces are bridged and the destinations are on local bridges too
            return the destination bridges """
        for iface in routing_interfaces:
            if not self._data.target.interfaces[iface].bridge:
                return None

        if self._data.target.name in dst.local_interfaces:
            for iface in dst.local_interfaces[self._data.target.name]:
                if not self._data.target.interfaces[iface].bridge:
                    return None
        else:
            return None

        return dst.local_interfaces[self._data.target.name]

    def rule_interfaces(self, rule_obj):
        """ Return interfaces list on which the rule is needed to be defined """

        # if the rule has a filter, apply it
        # TODO: better filters (regex)
        rule_filter = rule_obj.get_option('filter')
        if rule_filter and self._data.target.name not in rule_filter.split(' '):
            return set()

        if len(rule_obj.src) != 1 or len(rule_obj.dst) != 1:
            raise AssertionError()

        interfaces = self.rule_interfaces_any(rule_obj)
        if interfaces is not None:
            return interfaces

        interfaces = self.rule_interfaces_ip_broadcast(rule_obj)
        if interfaces is not None:
            return interfaces

        interfaces = set()
        src_is_local = rule_obj.src[0].is_whole_local(self._data.target)
        dst_is_local = rule_obj.dst[0].is_whole_local(self._data.target)

        # if it's a blocking or reject rule, we only use the src
        if rule_obj.action != 'pass':
            if src_is_local:
                interfaces.update(rule_obj.src[0].local_interfaces[self._data.target.name])
            else:
                interfaces.update(rule_obj.src[0].routed_by_interfaces(self._data.target))

            if len(interfaces) > 1:
                raise AssertionError('Invalid local interfaces count for {0}: {1}'.format(rule_obj.name, len(interfaces)))
            return interfaces

        # if source and dst are local, return the local interface
        if src_is_local and dst_is_local:
            if len(rule_obj.src[0].local_interfaces[self._data.target.name]) != 1:
                raise AssertionError(
                    'Invalid local interfaces count for {0}: {1}'
                    .format(rule_obj.name, len(rule_obj.src[0].local_interfaces[self._data.target.name])))
            if len(rule_obj.dst[0].local_interfaces[self._data.target.name]) != 1:
                raise AssertionError(
                    'Invalid local interfaces count for {0}: {1}'
                    .format(rule_obj.name, len(rule_obj.dst[0].local_interfaces[self._data.target.name])))

            # if they are both on the same interface, we return nothing, unless the interface is a bridge
            # or the pfsense is the source/destination of the rule
            src_interface = ''.join(rule_obj.src[0].local_interfaces[self._data.target.name])
            dst_interface = ''.join(rule_obj.dst[0].local_interfaces[self._data.target.name])
            if src_interface == dst_interface and not self._data.target.interfaces[src_interface].bridge:
                if not rule_obj.src[0].match_local_interface_ip(self._data.target) and not rule_obj.dst[0].match_local_interface_ip(self._data.target):
                    return set()

            return rule_obj.src[0].local_interfaces[self._data.target.name]

        # if the destination is unreachable
        if not dst_is_local and src_is_local and not rule_obj.dst[0].is_adjacent_or_routed(self._data.target):
            if self._display_warnings:
                display.warning(
                    'Destination {0} is not accessible from this pfSense for {1}.Please add the right adjacent/routed network if it\'s not an error'
                    .format(rule_obj.dst[0].name, rule_obj.name))
            return set()

        # if the source is unreachable
        if not src_is_local and dst_is_local and not rule_obj.src[0].is_adjacent_or_routed(self._data.target):
            if self._display_warnings:
                display.warning(
                    'Source {0} can not access to this pfSense for {1}. Please add the right adjacent/routed network if it\'s not an error'
                    .format(rule_obj.src[0].name, rule_obj.name))
            return set()

        # we add all the interfaces the source can use to go out
        if self._data.target.name in rule_obj.src[0].local_interfaces:
            interfaces.update(rule_obj.src[0].local_interfaces[self._data.target.name])

        # we add interfaces the source can use to get in
        if not src_is_local:
            routing_interfaces = rule_obj.src[0].routed_by_interfaces(self._data.target)
            # if they are both not local and on the same interfaces or with an unreachable destination
            # we return nothing
            if not dst_is_local:
                dst_routing_interfaces = rule_obj.dst[0].routed_by_interfaces(self._data.target)
                routing_interfaces = routing_interfaces.difference(dst_routing_interfaces)
                if not routing_interfaces or not dst_routing_interfaces:
                    return set()

            # if the interfaces we would use are bridged, and the destinations are on local bridges too
            # we declare the rule on the destination bridges since packets would come from there
            bridge_interfaces = self.bridged_by_interfaces(routing_interfaces, rule_obj.dst[0])
            if bridge_interfaces:
                interfaces.update(bridge_interfaces)
            else:
                interfaces.update(routing_interfaces)

        if not interfaces and (src_is_local or dst_is_local):
            msg = 'Invalid sub-rule interfaces count ({0}), src={1}, dst={2}'.format(len(interfaces), rule_obj.src[0].name, rule_obj.dst[0].name)
            raise AssertionError(msg)
        return interfaces

    @staticmethod
    def generate_rule(name, rule_obj, interfaces, last_name):
        """ Generate rules definitions for rule """
        base = []
        base.append({})

        if len(rule_obj.src) != 1 or len(rule_obj.dst) != 1:
            raise AssertionError()

        rule = {}
        rule['src'] = rule_obj.src[0].name
        rule['dst'] = rule_obj.dst[0].name
        if rule_obj.src_port:
            rule['src_port'] = ' '.join(rule_obj.src_port)
        if rule_obj.dst_port:
            rule['dst_port'] = ' '.join(rule_obj.dst_port)
        if rule_obj.protocol:
            rule['protocol'] = ' '.join(rule_obj.protocol)

        rule['src'] = rule_product_ports(rule, 'src', 'src_port')
        rule['dst'] = rule_product_ports(rule, 'dst', 'dst_port')

        base = rule_product_dict(base, rule, 'src', 'source')
        base = rule_product_dict(base, rule, 'dst', 'destination')
        base = rule_product_dict(base, rule, 'protocol')

        for interface in rule_obj.interfaces:
            if len(base) == 1:
                definition = {}
                definition['name'] = name
                definition['action'] = rule_obj.action
                for field in OUTPUT_OPTION_FIELDS:
                    definition[field] = rule_obj.get_option(field)
                definition['interface'] = interface
                definition['state'] = 'present'
                if interface in last_name and last_name[interface]:
                    definition['after'] = last_name[interface]
                else:
                    definition['after'] = 'top'
                definition.update(base[0])
                interfaces[interface].append(definition)
                last_name[interface] = name

                # todo: create the separators before and set the first rule there
                # and find a way to generate separators when a filter is used
                if interface not in rule_obj.generated_names:
                    rule_obj.generated_names[interface] = name
            else:
                rule_idx = 1
                for rule_def in base:
                    definition = {}
                    rule_name = name + "_" + str(rule_idx)
                    definition['name'] = rule_name
                    definition['action'] = rule_obj.action
                    for field in OUTPUT_OPTION_FIELDS:
                        definition[field] = rule_obj.get_option(field)
                    definition['interface'] = interface
                    definition['state'] = 'present'
                    if interface in last_name and last_name[interface]:
                        definition['after'] = last_name[interface]
                    else:
                        definition['after'] = 'top'
                    definition.update(rule_def)
                    interfaces[interface].append(definition)
                    last_name[interface] = rule_name
                    rule_idx = rule_idx + 1
                    # todo: create the separators before and set the first rule there
                    # and find a way to generate separators when a filter is used
                    if interface not in rule_obj.generated_names:
                        rule_obj.generated_names[interface] = rule_name

    def generate_rules(self, rule_filter=None):
        """ Return rules definitions for pfsense_aggregate
            if rule_filter, process only rules matching rule_filter
        """

        self._decomposer.decompose_rules()
        ret = []

        interfaces = {}
        last_name = {}
        rules = OrderedDict()
        for name, rule in self._data.rules_obj.items():
            subrules = []
            for subrule in rule.sub_rules:
                subrule.interfaces = self.rule_interfaces(subrule)
                if rule_filter is not None and name != rule_filter:
                    continue
                if not subrule.interfaces:
                    continue
                subrules.append(subrule)
                for interface in subrule.interfaces:
                    if interface not in interfaces:
                        interfaces[interface] = []
                        last_name[interface] = ""
            if len(subrules) > 1:
                rule_number = 1
                for subrule in subrules:
                    rules[name + "_" + str(rule_number)] = subrule
                    rule_number += 1
            elif len(subrules) == 1:
                rules[name] = subrules[0]

        for name, rule in rules.items():
            self.generate_rule(name, rule, interfaces, last_name)

        ret = []
        for name, interface in interfaces.items():
            for rule in interface:
                ret.append(rule)

        return ret

    def output_rules(self, rules):
        """ Output aliases definitions for pfsense_aggregate """
        print("          #===========================")
        print("          # Rules")
        print("          # ")
        interfaces = list(self._data.target.interfaces.keys())
        interfaces.sort()
        for interface in interfaces:
            for rule in rules:
                if interface != rule['interface']:
                    continue
                definition = ("          - { name: \"" + rule['name'] + "\", source: \""
                              + rule['source'] + "\", destination: \"" + rule['destination']
                              + "\", interface: \"" + rule['interface'] + "\", action: \"" + rule['action'] + "\"")
                if rule.get('protocol'):
                    definition += ", protocol: \"" + rule['protocol'] + "\""
                if rule.get('descr'):
                    definition += ", descr: \"" + rule['descr'] + "\""
                for field in OUTPUT_OPTION_FIELDS:
                    value = rule.get(field)
                    if value is not None:
                        definition += ', {0}: {1}'.format(field, value)

                if rule.get('after'):
                    definition += ", after: \"" + rule['after'] + "\""
                definition += ", state: \"present\" }"
                print(definition)


class PFSenseRuleSeparatorFactory(object):
    """ Class generating rule separators definitions """

    def __init__(self, data):
        self._data = data

    def _find_first_separator_rule(self, separator):
        """ return the name of the first rule in the separator """
        for rule in self._data.rules_obj.values():
            for subrule in rule.sub_rules:
                if subrule.separator.name == separator.name and separator.interface in subrule.generated_names:
                    return subrule.generated_names[separator.interface]
        return None

    def generate_rule_separators(self, rule_filter=None):
        """ Return rule_separators definitions for pfsense_aggregate """

        separators = OrderedDict()

        for name, rule in self._data.rules_obj.items():
            if rule_filter is not None and name != rule_filter:
                continue
            for subrule in rule.sub_rules:
                if subrule.separator is None or subrule.separator.name is None:
                    continue
                for interface in subrule.interfaces:
                    separator = PFSenseRuleSeparator()
                    separator.name = subrule.separator.name
                    separator.interface = interface
                    if separator not in separators:
                        separators[separator] = separator

        ret = []
        for separator in separators.values():
            definition = {}
            definition['name'] = separator.name
            definition['interface'] = separator.interface
            definition['before'] = self._find_first_separator_rule(separator)
            if definition['before'] is None:
                # for now we don't manage empty separators
                continue
            definition['state'] = 'present'
            ret.append(definition)

        return ret

    def output_rule_separators(self, separators):
        """ Output rule separators definitions for pfsense_aggregate """
        print("          #===========================")
        print("          # Rule separators")
        print("          # ")
        interfaces = list(self._data.target.interfaces.keys())
        interfaces.sort()
        for interface in interfaces:
            for separator in separators:
                if interface != separator['interface']:
                    continue
                definition = "          - { name: \"" + separator['name'] + "\", interface: \"" + separator['interface']
                definition += "\", before: \"" + separator['before'] + "\", state: \"present\" }"
                print(definition)


class LookupModule(LookupBase):
    """ Lookup module generating pfsense definitions """

    def load_data(self, from_file):
        """ Load and return pfsense data """
        myvars = getattr(self._templar, '_available_variables', {})
        current_host = myvars['inventory_hostname']

        fvars = ordered_load(open(from_file), yaml.SafeLoader)
        data = PFSenseData(
            hosts_aliases=fvars['hosts_aliases'],
            ports_aliases=fvars['ports_aliases'],
            pfsenses=fvars['pfsenses'],
            rules=fvars['rules'],
            target_name=current_host
        )
        return data

    def run(self, terms, variables, **kwargs):
        """ Main function """
        data = self.load_data(terms[0])

        parser = PFSenseDataParser(data)
        if not parser.parse():
            raise AnsibleError("Error checking pfsense data")

        alias_factory = PFSenseAliasFactory(data)
        rule_factory = PFSenseRuleFactory(data, display_warnings=(terms[1] == 'rules'))
        rule_separator_factory = PFSenseRuleSeparatorFactory(data)

        rules = rule_factory.generate_rules()
        rule_separators = rule_separator_factory.generate_rule_separators()
        aliases = alias_factory.generate_aliases()

        if terms[1] == 'aliases':
            return [aliases]
        elif terms[1] == 'rules':
            return [rules]
        elif terms[1] == 'rule_separators':
            return [rule_separators]
        elif terms[1] == 'all_definitions':
            res = {}
            res['aggregated_aliases'] = aliases
            res['aggregated_rules'] = rules
            res['aggregated_rule_separators'] = rule_separators
            return [res]

        return []


def unit_test_helper(filename, pfname):
    """ Unit test helper """
    rule_filter = None
    fvars = ordered_load(open(filename), yaml.SafeLoader)

    data = PFSenseData(
        hosts_aliases=fvars['hosts_aliases'],
        ports_aliases=fvars['ports_aliases'],
        pfsenses=fvars['pfsenses'],
        rules=fvars['rules'],
        target_name=pfname
    )

    parser = PFSenseDataParser(data)

    if not parser.parse():
        return False
    alias_factory = PFSenseAliasFactory(data)
    rule_factory = PFSenseRuleFactory(data)
    rule_separator_factory = PFSenseRuleSeparatorFactory(data)

    rules = rule_factory.generate_rules(rule_filter)
    rule_separators = rule_separator_factory.generate_rule_separators()
    aliases = alias_factory.generate_aliases(rule_filter)

    alias_factory.output_aliases(aliases)
    rule_factory.output_rules(rules)
    rule_separator_factory.output_rule_separators(rule_separators)

    return (aliases, rules)


def main():
    """ Output debug helper """
    if len(sys.argv) != 3 and len(sys.argv) != 4:
        print('Usage: pfsense.py <file> <target_fw> [rule_name]')
        return 0

    rule_filter = None
    if len(sys.argv) == 4:
        rule_filter = sys.argv[3]

    print('Loading data...')
    fvars = ordered_load(open(sys.argv[1]), yaml.SafeLoader)

    data = PFSenseData(
        hosts_aliases=fvars['hosts_aliases'],
        ports_aliases=fvars['ports_aliases'],
        pfsenses=fvars['pfsenses'],
        rules=fvars['rules'],
        target_name=sys.argv[2]
    )

    parser = PFSenseDataParser(data)
    print('Parsing data...')
    if not parser.parse():
        return False

    alias_factory = PFSenseAliasFactory(data)
    rule_factory = PFSenseRuleFactory(data)
    rule_separator_factory = PFSenseRuleSeparatorFactory(data)

    print('Generating rules...')
    rules = rule_factory.generate_rules(rule_filter)

    if rule_filter is None:
        print('Generating rule separators...')
        rule_separators = rule_separator_factory.generate_rule_separators(rule_filter)
    else:
        print('Filter set. Skipping rule separators...')

    print('Generating aliases...')
    aliases = alias_factory.generate_aliases(rule_filter)

    alias_factory.output_aliases(aliases)
    rule_factory.output_rules(rules)
    if rule_filter is None:
        rule_separator_factory.output_rule_separators(rule_separators)


if __name__ == '__main__':
    main()
