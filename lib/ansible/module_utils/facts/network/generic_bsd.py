# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

import re
import socket
import struct

from ansible.module_utils.facts.network.base import Network


class GenericBsdIfconfigNetwork(Network):
    """
    This is a generic BSD subclass of Network using the ifconfig command.
    It defines
    - interfaces (a list of interface names)
    - interface_<name> dictionary of ipv4, ipv6, and mac address information.
    - all_ipv4_addresses and all_ipv6_addresses: lists of all configured addresses.
    """
    platform = 'Generic_BSD_Ifconfig'

    def populate(self, collected_facts=None):
        network_facts = {}
        ifconfig_path = self.module.get_bin_path('ifconfig')

        if ifconfig_path is None:
            return network_facts

        route_path = self.module.get_bin_path('route')

        if route_path is None:
            return network_facts

        default_ipv4, default_ipv6 = self.get_default_interfaces(route_path)
        interfaces, ips = self.get_interfaces_info(ifconfig_path)
        interfaces = self.detect_type_media(interfaces)

        self.merge_default_interface(default_ipv4, interfaces, 'ipv4')
        self.merge_default_interface(default_ipv6, interfaces, 'ipv6')
        network_facts['interfaces'] = sorted(list(interfaces.keys()))

        for iface in interfaces:
            network_facts[iface] = interfaces[iface]

        network_facts['default_ipv4'] = default_ipv4
        network_facts['default_ipv6'] = default_ipv6
        network_facts['all_ipv4_addresses'] = ips['all_ipv4_addresses']
        network_facts['all_ipv6_addresses'] = ips['all_ipv6_addresses']

        return network_facts

    def detect_type_media(self, interfaces):
        for iface in interfaces:
            if 'media' in interfaces[iface]:
                if 'ether' in interfaces[iface]['media'].lower():
                    interfaces[iface]['type'] = 'ether'
        return interfaces

    def get_default_interfaces(self, route_path):

        # Use the commands:
        #     route -n get default
        #     route -n get -inet6 default
        # to find out the default outgoing interface, address, and gateway

        command = dict(v4=[route_path, '-n', 'get', 'default'],
                       v6=[route_path, '-n', 'get', '-inet6', 'default'])

        interface = dict(v4={}, v6={})

        for v in 'v4', 'v6':

            if v == 'v6' and not socket.has_ipv6:
                continue
            rc, out, err = self.module.run_command(command[v])
            if not out:
                # v6 routing may result in
                #   RTNETLINK answers: Invalid argument
                continue
            for line in out.splitlines():
                words = line.strip().split(': ')
                # Collect output from route command
                if len(words) > 1:
                    if words[0] == 'interface':
                        interface[v]['interface'] = words[1]
                    if words[0] == 'gateway':
                        interface[v]['gateway'] = words[1]
                    # help pick the right interface address on OpenBSD
                    if words[0] == 'if address':
                        interface[v]['address'] = words[1]
                    # help pick the right interface address on NetBSD
                    if words[0] == 'local addr':
                        interface[v]['address'] = words[1]

        return interface['v4'], interface['v6']

    def get_interfaces_info(self, ifconfig_path, ifconfig_options='-a'):
        interfaces = {}
        current_if = {}
        ips = dict(
            all_ipv4_addresses=[],
            all_ipv6_addresses=[],
        )
        # FreeBSD, DragonflyBSD, NetBSD, OpenBSD and macOS all implicitly add '-a'
        # when running the command 'ifconfig'.
        # Solaris must explicitly run the command 'ifconfig -a'.
        rc, out, err = self.module.run_command([ifconfig_path, ifconfig_options])

        for line in out.splitlines():

            if line:
                words = line.split()

                if words[0] == 'pass':
                    continue
                elif re.match(r'^\S', line) and len(words) > 3:
                    current_if = self.parse_interface_line(words)
                    interfaces[current_if['device']] = current_if
                elif words[0].startswith('options='):
                    self.parse_options_line(words, current_if, ips)
                elif words[0] == 'nd6':
                    self.parse_nd6_line(words, current_if, ips)
                elif words[0] == 'ether':
                    self.parse_ether_line(words, current_if, ips)
                elif words[0] == 'media:':
                    self.parse_media_line(words, current_if, ips)
                elif words[0] == 'status:':
                    self.parse_status_line(words, current_if, ips)
                elif words[0] == 'lladdr':
                    self.parse_lladdr_line(words, current_if, ips)
                elif words[0] == 'inet':
                    self.parse_inet_line(words, current_if, ips)
                elif words[0] == 'inet6':
                    self.parse_inet6_line(words, current_if, ips)
                elif words[0] == 'tunnel':
                    self.parse_tunnel_line(words, current_if, ips)
                else:
                    self.parse_unknown_line(words, current_if, ips)

        return interfaces, ips

    def parse_interface_line(self, words):
        device = words[0][0:-1]
        current_if = {'device': device, 'ipv4': [], 'ipv6': [], 'type': 'unknown'}
        current_if['flags'] = self.get_options(words[1])
        if 'LOOPBACK' in current_if['flags']:
            current_if['type'] = 'loopback'
        current_if['macaddress'] = 'unknown'    # will be overwritten later

        if len(words) >= 5:  # Newer FreeBSD versions
            current_if['metric'] = words[3]
            current_if['mtu'] = words[5]
        else:
            current_if['mtu'] = words[3]

        return current_if

    def parse_options_line(self, words, current_if, ips):
        # Mac has options like this...
        current_if['options'] = self.get_options(words[0])

    def parse_nd6_line(self, words, current_if, ips):
        # FreeBSD has options like this...
        current_if['options'] = self.get_options(words[1])

    def parse_ether_line(self, words, current_if, ips):
        current_if['macaddress'] = words[1]
        current_if['type'] = 'ether'

    def parse_media_line(self, words, current_if, ips):
        # not sure if this is useful - we also drop information
        current_if['media'] = words[1]
        if len(words) > 2:
            current_if['media_select'] = words[2]
        if len(words) > 3:
            current_if['media_type'] = words[3][1:]
        if len(words) > 4:
            current_if['media_options'] = self.get_options(words[4])

    def parse_status_line(self, words, current_if, ips):
        current_if['status'] = words[1]

    def parse_lladdr_line(self, words, current_if, ips):
        current_if['lladdr'] = words[1]

    def parse_inet_line(self, words, current_if, ips):
        # netbsd show aliases like this
        #  lo0: flags=8049<UP,LOOPBACK,RUNNING,MULTICAST> mtu 33184
        #         inet 127.0.0.1 netmask 0xff000000
        #         inet alias 127.1.1.1 netmask 0xff000000
        if words[1] == 'alias':
            del words[1]

        address = {'address': words[1]}
        # cidr style ip address (eg, 127.0.0.1/24) in inet line
        # used in netbsd ifconfig -e output after 7.1
        if '/' in address['address']:
            ip_address, cidr_mask = address['address'].split('/')

            address['address'] = ip_address

            netmask_length = int(cidr_mask)
            netmask_bin = (1 << 32) - (1 << 32 >> int(netmask_length))
            address['netmask'] = socket.inet_ntoa(struct.pack('!L', netmask_bin))

            if len(words) > 5:
                address['broadcast'] = words[3]

        else:
            # Don't just assume columns, use "netmask" as the index for the prior column
            try:
                netmask_idx = words.index('netmask') + 1
            except ValueError:
                netmask_idx = 3

            # deal with hex netmask
            if re.match('([0-9a-f]){8}$', words[netmask_idx]):
                netmask = '0x' + words[netmask_idx]
            else:
                netmask = words[netmask_idx]

            if netmask.startswith('0x'):
                address['netmask'] = socket.inet_ntoa(struct.pack('!L', int(netmask, base=16)))
            else:
                # otherwise assume this is a dotted quad
                address['netmask'] = netmask
        # calculate the network
        address_bin = struct.unpack('!L', socket.inet_aton(address['address']))[0]
        netmask_bin = struct.unpack('!L', socket.inet_aton(address['netmask']))[0]
        address['network'] = socket.inet_ntoa(struct.pack('!L', address_bin & netmask_bin))
        if 'broadcast' not in address:
            # broadcast may be given or we need to calculate
            try:
                broadcast_idx = words.index('broadcast') + 1
            except ValueError:
                address['broadcast'] = socket.inet_ntoa(struct.pack('!L', address_bin | (~netmask_bin & 0xffffffff)))
            else:
                address['broadcast'] = words[broadcast_idx]

        # add to our list of addresses
        if not words[1].startswith('127.'):
            ips['all_ipv4_addresses'].append(address['address'])
        current_if['ipv4'].append(address)

    def parse_inet6_line(self, words, current_if, ips):
        address = {'address': words[1]}

        # using cidr style addresses, ala NetBSD ifconfig post 7.1
        if '/' in address['address']:
            ip_address, cidr_mask = address['address'].split('/')

            address['address'] = ip_address
            address['prefix'] = cidr_mask

            if len(words) > 5:
                address['scope'] = words[5]
        else:
            if (len(words) >= 4) and (words[2] == 'prefixlen'):
                address['prefix'] = words[3]
            if (len(words) >= 6) and (words[4] == 'scopeid'):
                address['scope'] = words[5]

        localhost6 = ['::1', '::1/128', 'fe80::1%lo0']
        if address['address'] not in localhost6:
            ips['all_ipv6_addresses'].append(address['address'])
        current_if['ipv6'].append(address)

    def parse_tunnel_line(self, words, current_if, ips):
        current_if['type'] = 'tunnel'

    def parse_unknown_line(self, words, current_if, ips):
        # we are going to ignore unknown lines here - this may be
        # a bad idea - but you can override it in your subclass
        pass

    # TODO: these are module scope static function candidates
    #       (most of the class is really...)
    def get_options(self, option_string):
        start = option_string.find('<') + 1
        end = option_string.rfind('>')
        if (start > 0) and (end > 0) and (end > start + 1):
            option_csv = option_string[start:end]
            return option_csv.split(',')
        else:
            return []

    def merge_default_interface(self, defaults, interfaces, ip_type):
        if 'interface' not in defaults:
            return
        if not defaults['interface'] in interfaces:
            return
        ifinfo = interfaces[defaults['interface']]
        # copy all the interface values across except addresses
        for item in ifinfo:
            if item != 'ipv4' and item != 'ipv6':
                defaults[item] = ifinfo[item]

        ipinfo = []
        if 'address' in defaults:
            ipinfo = [x for x in ifinfo[ip_type] if x['address'] == defaults['address']]

        if len(ipinfo) == 0:
            ipinfo = ifinfo[ip_type]

        if len(ipinfo) > 0:
            for item in ipinfo[0]:
                defaults[item] = ipinfo[0][item]
