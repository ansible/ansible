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

from ansible.module_utils.facts.network.base import Network, NetworkCollector


class HPUXNetwork(Network):
    """
    HP-UX-specifig subclass of Network. Defines networking facts:
    - default_interface
    - interfaces (a list of interface names)
    - interface_<name> dictionary of ipv4 address information.
    """
    platform = 'HP-UX'

    def populate(self, collected_facts=None):
        network_facts = {}
        netstat_path = self.module.get_bin_path('netstat')

        if netstat_path is None:
            return network_facts

        default_interfaces_facts = self.get_default_interfaces()
        network_facts.update(default_interfaces_facts)

        interfaces = self.get_interfaces_info()
        network_facts['interfaces'] = interfaces.keys()
        for iface in interfaces:
            network_facts[iface] = interfaces[iface]

        return network_facts

    def get_default_interfaces(self):
        default_interfaces = {}
        rc, out, err = self.module.run_command("/usr/bin/netstat -nr")
        lines = out.splitlines()
        for line in lines:
            words = line.split()
            if len(words) > 1:
                if words[0] == 'default':
                    default_interfaces['default_interface'] = words[4]
                    default_interfaces['default_gateway'] = words[1]

        return default_interfaces

    def get_interfaces_info(self):
        interfaces = {}
        rc, out, err = self.module.run_command("/usr/bin/netstat -niw")
        lines = out.splitlines()
        for line in lines:
            words = line.split()
            for i in range(len(words) - 1):
                if words[i][:3] == 'lan':
                    device = words[i]
                    interfaces[device] = {'device': device}
                    address = words[i + 3]
                    interfaces[device]['ipv4'] = {'address': address}
                    network = words[i + 2]
                    interfaces[device]['ipv4'] = {'network': network,
                                                  'interface': device,
                                                  'address': address}
        return interfaces


class HPUXNetworkCollector(NetworkCollector):
    _fact_class = HPUXNetwork
    _platform = 'HP-UX'
