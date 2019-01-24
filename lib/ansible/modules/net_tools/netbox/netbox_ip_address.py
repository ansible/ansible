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
ip_address:
  description: Serialized object as created or already existent within Netbox
  returned: on creation
  type: dict
msg:
  description: Message indicating failure or info about what has been achieved
  returned: always
  type: str
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.net_tools.netbox.netbox_utils import find_ids, normalize_data, IP_ADDRESS_ROLE, IP_ADDRESS_STATUS
import json

try:
    import pynetbox
    HAS_PYNETBOX = True
except ImportError:
    HAS_PYNETBOX = False


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
    norm_data = normalize_data(data)
    try:
        if 'present' in state:
            return module.exit_json(
                **ensure_ip_address_present(nb, nb_endpoint, norm_data)
            )
        else:
            return module.exit_json(
                **ensure_ip_address_absent(nb, nb_endpoint, norm_data)
            )
    except pynetbox.RequestError as e:
        return module.fail_json(msg=json.loads(e.error))
    except ValueError as e:
        return module.fail_json(msg=str(e))


def ensure_ip_address_present(nb, nb_endpoint, data):
    """
    :returns dict(ip_address, msg, changed): dictionary resulting of the request,
    where 'ip_address' is the serialized ip fetched or newly created in Netbox
    """
    data = find_ids(nb, data)
    if not isinstance(data, dict):
        changed = False
        return {"msg": data, "changed": changed}

    try:
        ip_addr = _search_ip(nb_endpoint, data)
    except ValueError:
        return _error_multiple_ip_results(data)

    if not ip_addr:
        ip_addr = nb_endpoint.create(data).serialize()
        changed = True
        msg = "IP Addresses %s created" % (data["address"])
    else:
        ip_addr = ip_addr.serialize()
        changed = False
        msg = "IP Address %s already exists" % (data["address"])

    return {"ip_address": ip_addr, "msg": msg, "changed": changed}


def _search_ip(nb_endpoint, data):
    if data.get("vrf") and not isinstance(data["vrf"], int):
        raise ValueError(
            "%s does not exist - Please create VRF" % (data["vrf"])
        )
    if data.get("status"):
        data["status"] = IP_ADDRESS_STATUS.get(data["status"].lower())
    if data.get("role"):
        data["role"] = IP_ADDRESS_ROLE.get(data["role"].lower())

    get_query_params = {"address": data["address"]}
    if data.get("vrf"):
        get_query_params["vrf_id"] = data["vrf"]

    ip_addr = nb_endpoint.get(**get_query_params)
    return ip_addr


def _error_multiple_ip_results(data):
    changed = False
    if data.get("vrf"):
        return {"msg": "Returned more than result", "changed": changed}
    else:
        return {
            "msg": "Returned more than one result - Try specifying VRF.",
            "changed": changed
        }


def ensure_ip_address_absent(nb, nb_endpoint, data):
    """
    :returns dict(msg, changed)
    """
    data = find_ids(nb, data)
    if not isinstance(data, dict):
        changed = False
        return {"msg": data, "changed": changed}

    try:
        ip_addr = _search_ip(nb_endpoint, data)
    except ValueError:
        return _error_multiple_ip_results(data)

    if ip_addr:
        ip_addr.delete()
        changed = True
        msg = "IP Address %s deleted" % (data["address"])
    else:
        changed = False
        msg = "IP Address %s already absent" % (data["address"])

    return {"msg": msg, "changed": changed}


if __name__ == "__main__":
    main()
