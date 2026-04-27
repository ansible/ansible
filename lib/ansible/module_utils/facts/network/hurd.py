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

import os

from ansible.module_utils.facts.network.base import Network, NetworkCollector


class HurdPfinetNetwork(Network):
    """
    This is a GNU Hurd specific subclass of Network. It use fsysopts to
    get the ip address and support only pfinet.
    """
    platform = 'GNU'
    _socket_dir = '/servers/socket/'

    def assign_network_facts(self, network_facts, fsysopts_path, socket_path):
        rc, out, err = self.module.run_command([fsysopts_path, '-L', socket_path])
        # FIXME: build up a interfaces datastructure, then assign into network_facts
        network_facts['interfaces'] = []
        for i in out.split():
            if '=' in i and i.startswith('--'):
                k, v = i.split('=', 1)
                # remove '--'
                k = k[2:]
                if k == 'interface':
                    # remove /dev/ from /dev/eth0
                    v = v[5:]
                    network_facts['interfaces'].append(v)
                    network_facts[v] = {
                        'active': True,
                        'device': v,
                        'ipv4': {},
                        'ipv6': [],
                    }
                    current_if = v
                elif k == 'address':
                    network_facts[current_if]['ipv4']['address'] = v
                elif k == 'netmask':
                    network_facts[current_if]['ipv4']['netmask'] = v
                elif k == 'address6':
                    address, prefix = v.split('/')
                    network_facts[current_if]['ipv6'].append({
                        'address': address,
                        'prefix': prefix,
                    })
        return network_facts

    def populate(self, collected_facts=None):
        network_facts = {}

        fsysopts_path = self.module.get_bin_path('fsysopts')
        if fsysopts_path is None:
            return network_facts

        socket_path = None

        for l in ('inet', 'inet6'):
            link = os.path.join(self._socket_dir, l)
            if os.path.exists(link):
                socket_path = link
                break

        if socket_path is None:
            return network_facts

        return self.assign_network_facts(network_facts, fsysopts_path, socket_path)


class HurdNetworkCollector(NetworkCollector):
    _platform = 'GNU'
    _fact_class = HurdPfinetNetwork
