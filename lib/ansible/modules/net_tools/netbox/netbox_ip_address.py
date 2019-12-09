#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Mikhail Yohman (@FragmentedPacket) <mikhail.yohman@gmail.com>
# Copyright: (c) 2019, Alexander Stauch (@BlackestDawn) <blacke4dawn@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: netbox_ip_address
short_description: Creates or removes IP addresses from Netbox
description:
  - Creates or removes IP addresses from Netbox
notes:
  - Tags should be defined as a YAML list
  - This should be ran with connection C(local) and hosts C(localhost)
author:
  - Mikhail Yohman (@FragmentedPacket)
  - Anthony Ruhier (@Anthony25)
  - Alexander Stauch (@BlackestDawn)
requirements:
  - pynetbox
version_added: '2.8'
options:
  netbox_url:
    description:
      - URL of the Netbox instance resolvable by Ansible control host
    required: true
  netbox_token:
    description:
      - The token created within Netbox to authorize API access
    required: true
  data:
    description:
      - Defines the IP address configuration
    suboptions:
      family:
        description:
          - Specifies with address family the IP address belongs to
        choices:
          - 4
          - 6
      address:
        description:
          - Required if state is C(present)
      prefix:
        description:
          - |
            With state C(present), if an interface is given, it will ensure
            that an IP inside this prefix (and vrf, if given) is attached
            to this interface. Otherwise, it will get the next available IP
            of this prefix and attach it.
            With state C(new), it will force to get the next available IP in
            this prefix. If an interface is given, it will also force to attach
            it.
            Required if state is C(present) or C(new) when no address is given.
            Unused if an address is specified.
      vrf:
        description:
          - VRF that IP address is associated with
      tenant:
        description:
          - The tenant that the device will be assigned to
      status:
        description:
          - The status of the IP address
        choices:
          - Active
          - Reserved
          - Deprecated
          - DHCP
      role:
        description:
          - The role of the IP address
        choices:
          - Loopback
          - Secondary
          - Anycast
          - VIP
          - VRRP
          - HSRP
          - GLBP
          - CARP
      interface:
        description:
          - |
            The name and device of the interface that the IP address should be assigned to
            Required if state is C(present) and a prefix specified.
      description:
        description:
          - The description of the interface
      nat_inside:
        description:
          - The inside IP address this IP is assigned to
      tags:
        description:
          - Any tags that the IP address may need to be associated with
      custom_fields:
        description:
          - must exist in Netbox
    required: true
  state:
    description:
      - |
        Use C(present), C(new) or C(absent) for adding, force adding or removing.
        C(present) will check if the IP is already created, and return it if
        true. C(new) will force to create it anyway (useful for anycasts, for
        example).
    choices: [ absent, new, present ]
    default: present
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used on personally controlled sites using self-signed certificates.
    default: 'yes'
    type: bool
'''

EXAMPLES = r'''
- name: "Test Netbox IP address module"
  connection: local
  hosts: localhost
  gather_facts: False

  tasks:
    - name: Create IP address within Netbox with only required information
      netbox_ip_address:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          address: 192.168.1.10
        state: present
    - name: Force to create (even if it already exists) the IP
      netbox_ip_address:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          address: 192.168.1.10
        state: new
    - name: Get a new available IP inside 192.168.1.0/24
      netbox_ip_address:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          prefix: 192.168.1.0/24
        state: new
    - name: Delete IP address within netbox
      netbox_ip_address:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          address: 192.168.1.10
        state: absent
    - name: Create IP address with several specified options
      netbox_ip_address:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          family: 4
          address: 192.168.1.20
          vrf: Test
          tenant: Test Tenant
          status: Reserved
          role: Loopback
          description: Test description
          tags:
            - Schnozzberry
        state: present
    - name: Create IP address and assign a nat_inside IP
      netbox_ip_address:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          family: 4
          address: 192.168.1.30
          vrf: Test
          nat_inside:
            address: 192.168.1.20
            vrf: Test
          interface:
            name: GigabitEthernet1
            device: test100
    - name: Ensure that an IP inside 192.168.1.0/24 is attached to GigabitEthernet1
      netbox_ip_address:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          prefix: 192.168.1.0/24
          vrf: Test
          interface:
            name: GigabitEthernet1
            device: test100
        state: present
    - name: Attach a new available IP of 192.168.1.0/24 to GigabitEthernet1
      netbox_ip_address:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          prefix: 192.168.1.0/24
          vrf: Test
          interface:
            name: GigabitEthernet1
            device: test100
        state: new
'''

RETURN = r'''
ip_address:
  description: Serialized object as created or already existent within Netbox
  returned: on creation
  type: dict
msg:
  description: Message indicating failure or info about what has been achieved
  returned: always
  type: str
'''

import json
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.net_tools.netbox.netbox_utils import (
    PyNetboxBase,
    netbox_argument_spec,
    IP_ADDRESS_STATUS,
    IP_ADDRESS_ROLE
)
from ansible.module_utils.compat import ipaddress

PYNETBOX_IMP_ERR = None
try:
    import pynetbox
    HAS_PYNETBOX = True
except ImportError:
    PYNETBOX_IMP_ERR = traceback.format_exc()
    HAS_PYNETBOX = False


class PyNetboxIP(PyNetboxBase):
    def __init__(self, module):
        """Constructor"""
        super(PyNetboxIP, self).__init__(module)
        self._set_endpoint('ip_addresses')
        # Some default failure messages for object manipulation
        self.param_usage = {
            'type': "IP",
            'success': "address",
            'fail': "address",
            'rname': "ip_address",
            'search': "address"
        }

    def run_module(self):
        """Main runner"""
        # Checks for existing IP and creates or updates as necessary
        if self.state == 'present':
            if 'address' in self.normalized_data:
                self.ensure_object_present()
            else:
                if 'interface' not in self.normalized_data or 'prefix' not in self.normalized_data:
                    raise ValueError("Both prefix and interface are required when ensuring IP is attached to an interface")
                query_params = {
                    "interface_id": self.normalized_data['interface'],
                    "parent": self.normalized_data['prefix']
                }
                if 'vrf' in self.normalized_data:
                    query_params['vrf_id'] = self.normalized_data['vrf']
                nb_prefix = self._search_prefix()
                attached_ips = nb_prefix.filter(**query_params)
                if attached_ips:
                    ip_addr = attached_ips[-1].serialize()
                    self.result.update({
                        'changed': False,
                        'msg': "IP Address %s already attached" % (ip_addr["address"])
                    })
                else:
                    self.fetch_new_ip()

        # Fetches new IP (first available in prefix) or recreates existing
        elif self.state == 'new':
            if 'address' in self.normalized_data:
                self._create_object()
            else:
                self.fetch_new_ip()

        # Deletes IP if present
        elif self.state == 'absent':
            query_params = {"address": self.normalized_data["address"]}
            if "vrf" in self.normalized_data:
                query_params["vrf_id"] = self.normalized_data["vrf"]
            self.ensure_object_absent(query_params, obj_name="IP address")

        # Unknown state
        else:
            self.module.fail_json(msg="Invalid state %s" % self.state)
        self.module.exit_json(**self.result)

    # Object manipulation helpers
    def fetch_new_ip(self):
        """Registers next available IP as taken"""
        nb_prefix = self._search_prefix()
        if not nb_prefix:
            self.module.fail_json(msg="%s does not exist - please create it first" % (self.normalized_data["prefix"]))
        elif nb_prefix.available_ips.list():
            self._create_object(endpoint=nb_prefix.available_ips)
        else:
            self.result['msg'] = "No available IPs within %s" % (self.normalized_data['prefix'])

    # Other internal helper functions
    def _check_and_adapt_data(self):
        """Overridden parent method"""
        data = self._find_ids()
        if 'vrf' in data and not isinstance(data["vrf"], int):
            raise ValueError(
                "%s does not exist - Please create VRF" % (data["vrf"])
            )
        if 'status' in data:
            data["status"] = IP_ADDRESS_STATUS.get(data["status"].lower())
        if 'role' in data:
            data["role"] = IP_ADDRESS_ROLE.get(data["role"].lower())
        self.normalized_data.update(data)

    def _search_prefix(self):
        """Return prefix-object from registered data"""
        prefix_query = {"prefix": self.normalized_data['prefix']}
        if 'vrf' in self.normalized_data:
            prefix_query['vrf_id'] = self.normalized_data['vrf']
        return self._retrieve_object(prefix_query, 'prefixes')

    def _multiple_results_error(self, data=None):
        """Overridden parent method"""
        if data is None:
            data = self.normalized_data
        if "vrf" in data:
            return {"msg": "Returned more than result", "changed": False}
        else:
            return {
                "msg": "Returned more than one result - Try specifying VRF.",
                "changed": False
            }


def main():
    '''
    Main entry point for module execution
    '''
    argument_spec = netbox_argument_spec()
    argument_spec.update(dict(
        state=dict(required=False, default='present', choices=['present', 'absent', 'new'])
    ))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    pynb = PyNetboxIP(module)

    try:
        pynb.run_module()
    except pynetbox.RequestError as e:
        return module.fail_json(msg=json.loads(e.error))
    except ValueError as e:
        return module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
