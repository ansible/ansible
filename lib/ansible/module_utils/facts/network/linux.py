# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

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

        default_ipv4, default_ipv6 = self.get_default_interfaces(
            ip_path,
            collected_facts=collected_facts
        )
        interfaces, ips = self.get_interfaces_info(
            ip_path,
            default_ipv4,
            default_ipv6
        )
        network_facts['interfaces'] = interfaces.keys()
        for iface, value in interfaces.items():
            network_facts[iface] = value

        network_facts.update({
            'default_ipv4': default_ipv4,
            'default_ipv6': default_ipv6,
            'all_ipv4_addresses': ips['all_ipv4_addresses'],
            'all_ipv6_addresses': ips['all_ipv6_addresses'],
            'locally_reachable_ips': self.get_locally_reachable_ips(ip_path),
        })
        return network_facts

    def _parse_locally_reachable_ips(self, output, ips_data):
        for line in output.splitlines():
            if not line:
                continue
            words = line.split()
            if words[0] != 'local':
                continue
            address = words[1]
            if ":" in address:
                if address not in ips_data['ipv6']:
                    ips_data['ipv6'].append(address)
            else:
                if address not in ips_data['ipv4']:
                    ips_data['ipv4'].append(address)

    # List all `scope host` routes/addresses.
    # They belong to routes, but it means the whole prefix is reachable
    # locally, regardless of specific IP addresses.
    # E.g.: 192.168.0.0/24, any IP address is reachable from this range
    # if assigned as scope host.
    def get_locally_reachable_ips(self, ip_path):
        locally_reachable_ips = {
            'ipv4': [],
            'ipv6': [],
        }

        for ip_ver in ['-4', '-6']:
            args = [ip_path, ip_ver, 'route', 'show', 'table', 'local']
            rc, routes, dummy = self.module.run_command(args)
            if rc == 0:
                self._parse_locally_reachable_ips(routes, ips_data=locally_reachable_ips)

        return locally_reachable_ips

    def get_default_interfaces(self, ip_path, collected_facts=None):
        collected_facts = collected_facts or {}
        # Use the commands:
        #     ip -4 route get 8.8.8.8                     -> Google public DNS
        #     ip -6 route get 2404:6800:400a:800::1012    -> ipv6.google.com
        # to find out the default outgoing interface, address, and gateway
        command = {
            'v4': [ip_path, '-4', 'route', 'get', '8.8.8.8'],
            'v6': [ip_path, '-6', 'route', 'get', '2404:6800:400a:800::1012']
        }
        interface = {
            'v4': {},
            'v6': {}
        }

        for v in 'v4', 'v6':
            if (v == 'v6' and collected_facts.get('ansible_os_family') == 'RedHat' and
                    collected_facts.get('ansible_distribution_version', '').startswith('4.')):
                continue
            if v == 'v6' and not socket.has_ipv6:
                continue
            dummy, out, dummy = self.module.run_command(command[v], errors='surrogate_then_replace')
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

    def _parse_ip_output(self, output, device, interfaces, ips, default_ipv4, default_ipv6, macaddress, secondary=False):
        for line in output.splitlines():
            if not line:
                continue
            words = line.split()
            broadcast = ''
            if words[0] == 'inet':
                if '/' in words[1]:
                    address, netmask_length = words[1].split('/')
                    if len(words) > 3:
                        if words[2] == 'brd':
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

                if iface != device:
                    interfaces[iface] = {}
                if not secondary and "ipv4" not in interfaces[iface]:
                    interfaces[iface]['ipv4'] = {
                        'address': address,
                        'broadcast': broadcast,
                        'netmask': netmask,
                        'network': network,
                        'prefix': netmask_length,
                    }
                else:
                    if "ipv4_secondaries" not in interfaces[iface]:
                        interfaces[iface]["ipv4_secondaries"] = []
                    interfaces[iface]["ipv4_secondaries"].append({
                        'address': address,
                        'broadcast': broadcast,
                        'netmask': netmask,
                        'network': network,
                        'prefix': netmask_length,
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
                            'prefix': netmask_length,
                        })

                if 'address' in default_ipv4 and default_ipv4['address'] == address:
                    default_ipv4['broadcast'] = broadcast
                    default_ipv4['netmask'] = netmask
                    default_ipv4['network'] = network
                    default_ipv4['prefix'] = netmask_length
                    default_ipv4['macaddress'] = macaddress
                    default_ipv4['mtu'] = interfaces[device]['mtu']
                    default_ipv4['type'] = interfaces[device].get("type", "unknown")
                    default_ipv4['alias'] = words[-1]
                if not address.startswith('127.'):
                    ips['all_ipv4_addresses'].append(address)
            elif words[0] == 'inet6':
                if 'peer' == words[2]:
                    address = words[1]
                    dummy, prefix = words[3].split('/')
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

    def get_interfaces_info(self, ip_path, default_ipv4, default_ipv6):
        interfaces = {}
        ips = {
            'all_ipv4_addresses': [],
            'all_ipv6_addresses': [],
        }

        for path in glob.glob('/sys/class/net/*'):
            if not os.path.isdir(path):
                continue
            device = os.path.basename(path)
            interfaces[device] = {'device': device}

            mac_address_file_path = os.path.join(path, 'address')
            if os.path.exists(mac_address_file_path):
                macaddress = get_file_content(mac_address_file_path, default='')
                if macaddress and macaddress != '00:00:00:00:00:00':
                    interfaces[device]['macaddress'] = macaddress

            mtu_file_path = os.path.join(path, 'mtu')
            if os.path.exists(mtu_file_path):
                interfaces[device]['mtu'] = int(get_file_content(mtu_file_path))
            operstate_file_path = os.path.join(path, 'operstate')
            if os.path.exists(operstate_file_path):
                interfaces[device]['active'] = get_file_content(operstate_file_path) != 'down'
            module_file_path = os.path.join(path, 'device', 'driver', 'module')
            if os.path.exists(module_file_path):
                interfaces[device]['module'] = os.path.basename(os.path.realpath(module_file_path))
            type_file_path = os.path.join(path, 'type')
            if os.path.exists(type_file_path):
                _type = get_file_content(type_file_path)
                interfaces[device]['type'] = self.INTERFACE_TYPE.get(_type, 'unknown')
            bridge_file_path = os.path.join(path, 'bridge')
            if os.path.exists(bridge_file_path):
                interfaces[device]['type'] = 'bridge'
                interfaces[device]['interfaces'] = [os.path.basename(b) for b in glob.glob(os.path.join(path, 'brif', '*'))]
                bridge_id_file_path = os.path.join(bridge_file_path, 'bridge_id')
                if os.path.exists(bridge_id_file_path):
                    interfaces[device]['id'] = get_file_content(bridge_id_file_path, default='')
                bridge_stp_state_file_path = os.path.join(bridge_file_path, 'stp_state')
                if os.path.exists(bridge_stp_state_file_path):
                    interfaces[device]['stp'] = get_file_content(bridge_stp_state_file_path) == '1'
            bonding_file_path = os.path.join(path, 'bonding')
            if os.path.exists(bonding_file_path):
                interfaces[device]['type'] = 'bonding'
                interfaces[device]['slaves'] = get_file_content(os.path.join(bonding_file_path, 'slaves'), default='').split()
                interfaces[device]['mode'] = get_file_content(os.path.join(bonding_file_path, 'mode'), default='').split()[0]
                interfaces[device]['miimon'] = get_file_content(os.path.join(bonding_file_path, 'miimon'), default='').split()[0]
                interfaces[device]['lacp_rate'] = get_file_content(os.path.join(bonding_file_path, 'lacp_rate'), default='').split()[0]
                primary = get_file_content(os.path.join(bonding_file_path, 'primary'))
                if primary:
                    interfaces[device]['primary'] = primary
                    path = os.path.join(bonding_file_path, 'all_slaves_active')
                    if os.path.exists(path):
                        interfaces[device]['all_slaves_active'] = get_file_content(path) == '1'
            bonding_client_path = os.path.join(path, 'bonding_slave')
            if os.path.exists(bonding_client_path):
                interfaces[device]['perm_macaddress'] = get_file_content(os.path.join(bonding_client_path, 'perm_hwaddr'), default='')
            device_file_path = os.path.join(path, 'device')
            if os.path.exists(device_file_path):
                interfaces[device]['pciid'] = os.path.basename(os.readlink(device_file_path))
            speed_file_path = os.path.join(path, 'speed')
            if os.path.exists(speed_file_path):
                speed = get_file_content(speed_file_path)
                if speed is not None:
                    interfaces[device]['speed'] = int(speed)

            # Check whether an interface is in promiscuous mode
            flags_file_path = os.path.join(path, 'flags')
            if os.path.exists(flags_file_path):
                promisc_mode = False
                # The second byte indicates whether the interface is in promiscuous mode.
                # 1 = promisc
                # 0 = no promisc
                data = int(get_file_content(flags_file_path), 16)
                promisc_mode = data & 0x0100 > 0
                interfaces[device]['promisc'] = promisc_mode

            ip_path = self.module.get_bin_path("ip")

            args = [ip_path, 'addr', 'show', 'primary', 'dev', device]
            rc, primary_data, dummy = self.module.run_command(args, errors='surrogate_then_replace')
            if rc == 0:
                self._parse_ip_output(primary_data, device, interfaces, ips, default_ipv4, default_ipv6, macaddress)
            else:
                # possibly busybox, fallback to running without the "primary" arg
                # https://github.com/ansible/ansible/issues/50871
                args = [ip_path, 'addr', 'show', 'dev', device]
                rc, data, dummy = self.module.run_command(args, errors='surrogate_then_replace')
                if rc == 0:
                    self._parse_ip_output(data, device, interfaces, ips, default_ipv4, default_ipv6, macaddress)

            args = [ip_path, 'addr', 'show', 'secondary', 'dev', device]
            rc, secondary_data, dummy = self.module.run_command(args, errors='surrogate_then_replace')
            if rc == 0:
                self._parse_ip_output(
                    secondary_data,
                    device,
                    interfaces,
                    ips,
                    default_ipv4,
                    default_ipv6,
                    macaddress,
                    secondary=True
                )

            interfaces[device].update(self.get_ethtool_data(device))

        # replace : by _ in interface name since they are hard to use in template
        new_interfaces = {}
        for i, v in interfaces.items():
            if ':' in i:
                new_interfaces[i.replace(':', '_')] = v
            else:
                new_interfaces[i] = v
        return new_interfaces, ips

    def get_ethtool_data(self, device):

        data = {}
        ethtool_path = self.module.get_bin_path("ethtool")
        if ethtool_path is None:
            return data

        args = [ethtool_path, '-k', device]
        rc, stdout, dummy = self.module.run_command(args, errors='surrogate_then_replace')
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
        rc, stdout, dummy = self.module.run_command(args, errors='surrogate_then_replace')
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
