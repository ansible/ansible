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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import glob
import os
import re
import socket
import struct

from ansible.module_utils.facts.network.base import Network, NetworkCollector

from ansible.module_utils.facts.utils import get_file_content


class LinuxNetwork(Network):
    """
    This is a Linux-specific subclass of Network.  It defines
    - interfaces (a list of interface names)
    - interface_<name> dictionary of ipv4, ipv6, and mac address information.
    - all_ipv4_addresses and all_ipv6_addresses: lists of all configured addresses.
    - ipv4_address and ipv6_address: the first non-local address for each family.
    """
    platform = 'Linux'
    INTERFACE_TYPE = {
        '1': 'ether',
        '32': 'infiniband',
        '512': 'ppp',
        '772': 'loopback',
        '65534': 'tunnel',
    }

    def populate(self, collected_facts=None):
        network_facts = {}
        ip_path = self.module.get_bin_path('ip')
        if ip_path is None:
            return network_facts
        default_ipv4, default_ipv6 = self.get_default_interfaces(ip_path,
                                                                 collected_facts=collected_facts)
        interfaces, ips = self.get_interfaces_info(ip_path, default_ipv4, default_ipv6)
        network_facts['interfaces'] = interfaces.keys()
        for iface in interfaces:
            network_facts[iface] = interfaces[iface]
        network_facts['default_ipv4'] = default_ipv4
        network_facts['default_ipv6'] = default_ipv6
        network_facts['all_ipv4_addresses'] = ips['all_ipv4_addresses']
        network_facts['all_ipv6_addresses'] = ips['all_ipv6_addresses']
        return network_facts

    def get_default_interfaces(self, ip_path, collected_facts=None):
        collected_facts = collected_facts or {}
        # Use the commands:
        #     ip -4 route get 8.8.8.8                     -> Google public DNS
        #     ip -6 route get 2404:6800:400a:800::1012    -> ipv6.google.com
        # to find out the default outgoing interface, address, and gateway
        command = dict(
            v4=[ip_path, '-4', 'route', 'get', '8.8.8.8'],
            v6=[ip_path, '-6', 'route', 'get', '2404:6800:400a:800::1012']
        )
        interface = dict(v4={}, v6={})

        for v in 'v4', 'v6':
            if (v == 'v6' and collected_facts.get('ansible_os_family') == 'RedHat' and
                    collected_facts.get('ansible_distribution_version', '').startswith('4.')):
                continue
            if v == 'v6' and not socket.has_ipv6:
                continue
            rc, out, err = self.module.run_command(command[v], errors='surrogate_then_replace')
            if not out:
                # v6 routing may result in
                #   RTNETLINK answers: Invalid argument
                continue
            words = out.splitlines()[0].split()
            # A valid output starts with the queried address on the first line
            if len(words) > 0 and words[0] == command[v][-1]:
                for i in range(len(words) - 1):
                    if words[i] == 'dev':
                        interface[v]['interface'] = words[i + 1]
                    elif words[i] == 'src':
                        interface[v]['address'] = words[i + 1]
                    elif words[i] == 'via' and words[i + 1] != command[v][-1]:
                        interface[v]['gateway'] = words[i + 1]
        return interface['v4'], interface['v6']

    def get_interfaces_info(self, ip_path, default_ipv4, default_ipv6):
        interfaces = {}
        ips = dict(
            all_ipv4_addresses=[],
            all_ipv6_addresses=[],
        )

        # FIXME: maybe split into smaller methods?
        # FIXME: this is pretty much a constructor

        for path in glob.glob('/sys/class/net/*'):
            if not os.path.isdir(path):
                continue
            device = os.path.basename(path)
            interfaces[device] = {'device': device}
            if os.path.exists(os.path.join(path, 'address')):
                macaddress = get_file_content(os.path.join(path, 'address'), default='')
                if macaddress and macaddress != '00:00:00:00:00:00':
                    interfaces[device]['macaddress'] = macaddress
            if os.path.exists(os.path.join(path, 'mtu')):
                interfaces[device]['mtu'] = int(get_file_content(os.path.join(path, 'mtu')))
            if os.path.exists(os.path.join(path, 'operstate')):
                interfaces[device]['active'] = get_file_content(os.path.join(path, 'operstate')) != 'down'
            if os.path.exists(os.path.join(path, 'device', 'driver', 'module')):
                interfaces[device]['module'] = os.path.basename(os.path.realpath(os.path.join(path, 'device', 'driver', 'module')))
            if os.path.exists(os.path.join(path, 'type')):
                _type = get_file_content(os.path.join(path, 'type'))
                interfaces[device]['type'] = self.INTERFACE_TYPE.get(_type, 'unknown')
            if os.path.exists(os.path.join(path, 'bridge')):
                interfaces[device]['type'] = 'bridge'
                interfaces[device]['interfaces'] = [os.path.basename(b) for b in glob.glob(os.path.join(path, 'brif', '*'))]
                if os.path.exists(os.path.join(path, 'bridge', 'bridge_id')):
                    interfaces[device]['id'] = get_file_content(os.path.join(path, 'bridge', 'bridge_id'), default='')
                if os.path.exists(os.path.join(path, 'bridge', 'stp_state')):
                    interfaces[device]['stp'] = get_file_content(os.path.join(path, 'bridge', 'stp_state')) == '1'
            if os.path.exists(os.path.join(path, 'bonding')):
                interfaces[device]['type'] = 'bonding'
                interfaces[device]['slaves'] = get_file_content(os.path.join(path, 'bonding', 'slaves'), default='').split()
                interfaces[device]['mode'] = get_file_content(os.path.join(path, 'bonding', 'mode'), default='').split()[0]
                interfaces[device]['miimon'] = get_file_content(os.path.join(path, 'bonding', 'miimon'), default='').split()[0]
                interfaces[device]['lacp_rate'] = get_file_content(os.path.join(path, 'bonding', 'lacp_rate'), default='').split()[0]
                primary = get_file_content(os.path.join(path, 'bonding', 'primary'))
                if primary:
                    interfaces[device]['primary'] = primary
                    path = os.path.join(path, 'bonding', 'all_slaves_active')
                    if os.path.exists(path):
                        interfaces[device]['all_slaves_active'] = get_file_content(path) == '1'
            if os.path.exists(os.path.join(path, 'bonding_slave')):
                interfaces[device]['perm_macaddress'] = get_file_content(os.path.join(path, 'bonding_slave', 'perm_hwaddr'), default='')
            if os.path.exists(os.path.join(path, 'device')):
                interfaces[device]['pciid'] = os.path.basename(os.readlink(os.path.join(path, 'device')))
            if os.path.exists(os.path.join(path, 'speed')):
                speed = get_file_content(os.path.join(path, 'speed'))
                if speed is not None:
                    interfaces[device]['speed'] = int(speed)

            # Check whether an interface is in promiscuous mode
            if os.path.exists(os.path.join(path, 'flags')):
                promisc_mode = False
                # The second byte indicates whether the interface is in promiscuous mode.
                # 1 = promisc
                # 0 = no promisc
                data = int(get_file_content(os.path.join(path, 'flags')), 16)
                promisc_mode = (data & 0x0100 > 0)
                interfaces[device]['promisc'] = promisc_mode

            # TODO: determine if this needs to be in a nested scope/closure
            def parse_ip_output(output, secondary=False):
                for line in output.splitlines():
                    if not line:
                        continue
                    words = line.split()
                    broadcast = ''
                    if words[0] == 'inet':
                        if '/' in words[1]:
                            address, netmask_length = words[1].split('/')
                            if len(words) > 3:
                                broadcast = words[3]
                        else:
                            # pointopoint interfaces do not have a prefix
                            address = words[1]
                            netmask_length = "32"
                        address_bin = struct.unpack('!L', socket.inet_aton(address))[0]
                        netmask_bin = (1 << 32) - (1 << 32 >> int(netmask_length))
                        netmask = socket.inet_ntoa(struct.pack('!L', netmask_bin))
                        network = socket.inet_ntoa(struct.pack('!L', address_bin & netmask_bin))
                        iface = words[-1]
                        # NOTE: device is ref to outside scope
                        # NOTE: interfaces is also ref to outside scope
                        if iface != device:
                            interfaces[iface] = {}
                        if not secondary and "ipv4" not in interfaces[iface]:
                            interfaces[iface]['ipv4'] = {'address': address,
                                                         'broadcast': broadcast,
                                                         'netmask': netmask,
                                                         'network': network}
                        else:
                            if "ipv4_secondaries" not in interfaces[iface]:
                                interfaces[iface]["ipv4_secondaries"] = []
                            interfaces[iface]["ipv4_secondaries"].append({
                                'address': address,
                                'broadcast': broadcast,
                                'netmask': netmask,
                                'network': network,
                            })

                        # add this secondary IP to the main device
                        if secondary:
                            if "ipv4_secondaries" not in interfaces[device]:
                                interfaces[device]["ipv4_secondaries"] = []
                            if device != iface:
                                interfaces[device]["ipv4_secondaries"].append({
                                    'address': address,
                                    'broadcast': broadcast,
                                    'netmask': netmask,
                                    'network': network,
                                })

                        # NOTE: default_ipv4 is ref to outside scope
                        # If this is the default address, update default_ipv4
                        if 'address' in default_ipv4 and default_ipv4['address'] == address:
                            default_ipv4['broadcast'] = broadcast
                            default_ipv4['netmask'] = netmask
                            default_ipv4['network'] = network
                            # NOTE: macaddress is ref from outside scope
                            default_ipv4['macaddress'] = macaddress
                            default_ipv4['mtu'] = interfaces[device]['mtu']
                            default_ipv4['type'] = interfaces[device].get("type", "unknown")
                            default_ipv4['alias'] = words[-1]
                        if not address.startswith('127.'):
                            ips['all_ipv4_addresses'].append(address)
                    elif words[0] == 'inet6':
                        if 'peer' == words[2]:
                            address = words[1]
                            _, prefix = words[3].split('/')
                            scope = words[5]
                        else:
                            address, prefix = words[1].split('/')
                            scope = words[3]
                        if 'ipv6' not in interfaces[device]:
                            interfaces[device]['ipv6'] = []
                        interfaces[device]['ipv6'].append({
                            'address': address,
                            'prefix': prefix,
                            'scope': scope
                        })
                        # If this is the default address, update default_ipv6
                        if 'address' in default_ipv6 and default_ipv6['address'] == address:
                            default_ipv6['prefix'] = prefix
                            default_ipv6['scope'] = scope
                            default_ipv6['macaddress'] = macaddress
                            default_ipv6['mtu'] = interfaces[device]['mtu']
                            default_ipv6['type'] = interfaces[device].get("type", "unknown")
                        if not address == '::1':
                            ips['all_ipv6_addresses'].append(address)

            ip_path = self.module.get_bin_path("ip")

            args = [ip_path, 'addr', 'show', 'primary', device]
            rc, primary_data, stderr = self.module.run_command(args, errors='surrogate_then_replace')
            if rc == 0:
                parse_ip_output(primary_data)
            else:
                # possibly busybox, fallback to running without the "primary" arg
                # https://github.com/ansible/ansible/issues/50871
                args = [ip_path, 'addr', 'show', device]
                rc, data, stderr = self.module.run_command(args, errors='surrogate_then_replace')
                if rc == 0:
                    parse_ip_output(data)

            args = [ip_path, 'addr', 'show', 'secondary', device]
            rc, secondary_data, stderr = self.module.run_command(args, errors='surrogate_then_replace')
            if rc == 0:
                parse_ip_output(secondary_data, secondary=True)

            interfaces[device].update(self.get_ethtool_data(device))

        # replace : by _ in interface name since they are hard to use in template
        new_interfaces = {}
        # i is a dict key (string) not an index int
        for i in interfaces:
            if ':' in i:
                new_interfaces[i.replace(':', '_')] = interfaces[i]
            else:
                new_interfaces[i] = interfaces[i]
        return new_interfaces, ips

    def get_ethtool_data(self, device):

        data = {}
        ethtool_path = self.module.get_bin_path("ethtool")
        # FIXME: exit early on falsey ethtool_path and un-indent
        if ethtool_path:
            args = [ethtool_path, '-k', device]
            rc, stdout, stderr = self.module.run_command(args, errors='surrogate_then_replace')
            # FIXME: exit early on falsey if we can
            if rc == 0:
                features = {}
                for line in stdout.strip().splitlines():
                    if not line or line.endswith(":"):
                        continue
                    key, value = line.split(": ")
                    if not value:
                        continue
                    features[key.strip().replace('-', '_')] = value.strip()
                data['features'] = features

            args = [ethtool_path, '-T', device]
            rc, stdout, stderr = self.module.run_command(args, errors='surrogate_then_replace')
            if rc == 0:
                data['timestamping'] = [m.lower() for m in re.findall(r'SOF_TIMESTAMPING_(\w+)', stdout)]
                data['hw_timestamp_filters'] = [m.lower() for m in re.findall(r'HWTSTAMP_FILTER_(\w+)', stdout)]
                m = re.search(r'PTP Hardware Clock: (\d+)', stdout)
                if m:
                    data['phc_index'] = int(m.groups()[0])

        return data


class LinuxNetworkCollector(NetworkCollector):
    _platform = 'Linux'
    _fact_class = LinuxNetwork
    required_facts = set(['distribution', 'platform'])
