#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Mikhail Yohman (@fragmentedpacket) <mikhail.yohman@gmail.com>
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
          - The name and device of the interface that the IP address should be assigned to
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
      - Use C(present) or C(absent) for adding or removing.
    choices: [ absent, present ]
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
'''

RETURN = r'''
meta:
  description: Message indicating failure or returns results with the object created within Netbox
  returned: always
  type: list
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.net_tools.netbox.netbox_utils import find_ids, normalize_data, IP_ADDRESS_ROLE, IP_ADDRESS_STATUS
import json

try:
    import pynetbox
    HAS_PYNETBOX = True
except ImportError:
    HAS_PYNETBOX = False


def netbox_create_ip_address(nb, nb_endpoint, data):
    result = []
    if data.get('vrf'):
        norm_data = normalize_data(data)
        if norm_data.get("status"):
            norm_data["status"] = IP_ADDRESS_STATUS.get(norm_data["status"].lower())
        if norm_data.get("role"):
            norm_data["role"] = IP_ADDRESS_ROLE.get(norm_data["role"].lower())
        data = find_ids(nb, norm_data)
        if data.get('failed'):
            result.append(data)
            return result

        if not nb_endpoint.get(address=data["address"], vrf_id=data['vrf']):
            try:
                return nb_endpoint.create([data])
            except pynetbox.RequestError as e:
                return json.loads(e.error)
        else:
            result.append({'failed': '%s already exists in Netbox' % (data["address"])})
    else:
        if not nb_endpoint.get(address=data["address"]):
            norm_data = normalize_data(data)
            if norm_data.get("status"):
                norm_data["status"] = IP_ADDRESS_STATUS.get(norm_data["status"].lower())
            if norm_data.get("role"):
                norm_data["role"] = IP_ADDRESS_ROLE.get(norm_data["role"].lower())
            data = find_ids(nb, norm_data)

            try:
                return nb_endpoint.create([data])
            except pynetbox.RequestError as e:
                return json.loads(e.error)
        else:
            result.append({'failed': '%s already exists in Netbox' % (data["address"])})

    return result


def netbox_delete_ip_address(nb, nb_endpoint, data):
    norm_data = normalize_data(data)
    result = []
    if data.get('vrf'):
        data = find_ids(nb, norm_data)
        endpoint = nb_endpoint.get(address=norm_data["address"], vrf_id=data['vrf'])
    else:
        endpoint = nb_endpoint.get(address=norm_data["address"])

    try:
        if endpoint.delete():
            result.append({'success': '%s deleted from Netbox' % (norm_data["address"])})
    except AttributeError:
        result.append({'failed': '%s not found' % (norm_data["address"])})
    return result


def main():
    '''
    Main entry point for module execution
    '''
    argument_spec = dict(
        netbox_url=dict(type="str", required=True),
        netbox_token=dict(type="str", required=True, no_log=True),
        data=dict(type="dict", required=True),
        state=dict(required=False, default='present', choices=['present', 'absent']),
        validate_certs=dict(type="bool", default=True)
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False)

    # Fail module if pynetbox is not installed
    if not HAS_PYNETBOX:
        module.fail_json(msg='pynetbox is required for this module')

    # Assign variables to be used with module
    changed = False
    app = 'ipam'
    endpoint = 'ip_addresses'
    url = module.params["netbox_url"]
    token = module.params["netbox_token"]
    data = module.params["data"]
    state = module.params["state"]
    validate_certs = module.params["validate_certs"]

    # Attempt to create Netbox API object
    try:
        nb = pynetbox.api(url, token=token, ssl_verify=validate_certs)
    except Exception:
        module.fail_json(msg="Failed to establish connection to Netbox API")
    try:
        nb_app = getattr(nb, app)
    except AttributeError:
        module.fail_json(msg="Incorrect application specified: %s" % (app))

    nb_endpoint = getattr(nb_app, endpoint)
    if 'present' in state:
        response = netbox_create_ip_address(nb, nb_endpoint, data)
        if response[0].get('created'):
            changed = True
    else:
        response = netbox_delete_ip_address(nb, nb_endpoint, data)
        if 'success' in response[0]:
            changed = True
    module.exit_json(changed=changed, meta=response)


if __name__ == "__main__":
    main()
