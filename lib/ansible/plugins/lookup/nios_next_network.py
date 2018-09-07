#
# Copyright 2018 Red Hat | Ansible
#
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

DOCUMENTATION = """
---
lookup: nios_next_network
version_added: "2.7"
short_description: Return the next available network range for a network-container
description:
  - Uses the Infoblox WAPI API to return the next available network addresses for
    a given network CIDR
requirements:
  - infoblox_client
extends_documentation_fragment: nios
options:
    _terms:
      description: The CIDR network to retrieve the next network from next available network within the specified
                   container.
      required: True
    cidr:
      description:
        - The CIDR of the network to retrieve the next network from next available network within the
          specified container. Also, Requested CIDR must be specified and greater than the parent CIDR.
      required: True
      default: 24
    num:
      description: The number of network addresses to return from network-container
      required: false
      default: 1
    exclude:
      description: Network addresses returned from network-container excluding list of user's input network range
      required: false
      default: ''
"""

EXAMPLES = """
- name: return next available network for network-container 192.168.10.0/24
  set_fact:
    networkaddr: "{{ lookup('nios_next_network', '192.168.10.0/24', cidr=25, provider={'host': 'nios01', 'username': 'admin', 'password': 'password'}) }}"

- name: return the next 2 available network addresses for network-container 192.168.10.0/24
  set_fact:
    networkaddr: "{{ lookup('nios_next_network', '192.168.10.0/24', cidr=25, num=2,
                        provider={'host': 'nios01', 'username': 'admin', 'password': 'password'}) }}"

- name: return the available network addresses for network-container 192.168.10.0/24 excluding network range '192.168.10.0/25'
  set_fact:
    networkaddr: "{{ lookup('nios_next_network', '192.168.10.0/24', cidr=25, exclude=['192.168.10.0/25'],
                        provider={'host': 'nios01', 'username': 'admin', 'password': 'password'}) }}"
"""

RETURN = """
_list:
  description:
    - The list of next network addresses available
  returned: always
  type: list
"""

from ansible.plugins.lookup import LookupBase
from ansible.module_utils.net_tools.nios.api import WapiLookup
from ansible.module_utils._text import to_text
from ansible.errors import AnsibleError


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        try:
            network = terms[0]
        except IndexError:
            raise AnsibleError('missing network argument in the form of A.B.C.D/E')
        try:
            cidr = kwargs.get('cidr', 24)
        except IndexError:
            raise AnsibleError('missing CIDR argument in the form of xx')

        provider = kwargs.pop('provider', {})
        wapi = WapiLookup(provider)
        network_obj = wapi.get_object('networkcontainer', {'network': network})

        if network_obj is None:
            raise AnsibleError('unable to find network-container object %s' % network)
        num = kwargs.get('num', 1)
        exclude_ip = kwargs.get('exclude', [])

        try:
            ref = network_obj[0]['_ref']
            avail_nets = wapi.call_func('next_available_network', ref, {'cidr': cidr, 'num': num, 'exclude': exclude_ip})
            return [avail_nets['networks']]
        except Exception as exc:
            raise AnsibleError(to_text(exc))
