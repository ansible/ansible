#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Mikhail Yohman (@FragmentedPacket) <mikhail.yohman@gmail.com>
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

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.net_tools.netbox.netbox_utils import (
    find_ids,
    normalize_data,
    create_netbox_object,
    delete_netbox_object,
    update_netbox_object,
    IP_ADDRESS_ROLE,
    IP_ADDRESS_STATUS
)
from ansible.module_utils.compat import ipaddress
from ansible.module_utils._text import to_text


PYNETBOX_IMP_ERR = None
try:
    import pynetbox
    HAS_PYNETBOX = True
except ImportError:
    PYNETBOX_IMP_ERR = traceback.format_exc()
    HAS_PYNETBOX = False


def main():
    '''
    Main entry point for module execution
    '''
    argument_spec = dict(
        netbox_url=dict(type="str", required=True),
        netbox_token=dict(type="str", required=True, no_log=True),
        data=dict(type="dict", required=True),
        state=dict(required=False, default='present', choices=['present', 'absent', 'new']),
        validate_certs=dict(type="bool", default=True)
    )

    global module
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    # Fail module if pynetbox is not installed
    if not HAS_PYNETBOX:
        module.fail_json(msg=missing_required_lib('pynetbox'), exception=PYNETBOX_IMP_ERR)

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
    norm_data = normalize_data(data)
    try:
        norm_data = _check_and_adapt_data(nb, norm_data)
        if state in ("new", "present"):
            return _handle_state_new_present(
                module, state, nb_app, nb_endpoint, norm_data
            )
        elif state == "absent":
            return module.exit_json(
                **ensure_ip_address_absent(nb_endpoint, norm_data)
            )
        else:
            return module.fail_json(msg="Invalid state %s" % state)
    except pynetbox.RequestError as e:
        return module.fail_json(msg=json.loads(e.error))
    except ValueError as e:
        return module.fail_json(msg=str(e))


def _check_and_adapt_data(nb, data):
    data = find_ids(nb, data)

    if data.get("vrf") and not isinstance(data["vrf"], int):
        raise ValueError(
            "%s does not exist - Please create VRF" % (data["vrf"])
        )
    if data.get("status"):
        data["status"] = IP_ADDRESS_STATUS.get(data["status"].lower())
    if data.get("role"):
        data["role"] = IP_ADDRESS_ROLE.get(data["role"].lower())

    return data


def _handle_state_new_present(module, state, nb_app, nb_endpoint, data):
    if data.get("address"):
        if state == "present":
            return module.exit_json(
                **ensure_ip_address_present(nb_endpoint, data)
            )
        elif state == "new":
            return module.exit_json(
                **create_ip_address(nb_endpoint, data)
            )
    else:
        if state == "present":
            return module.exit_json(
                **ensure_ip_in_prefix_present_on_netif(
                    nb_app, nb_endpoint, data
                )
            )
        elif state == "new":
            return module.exit_json(
                **get_new_available_ip_address(nb_app, data)
            )


def ensure_ip_address_present(nb_endpoint, data):
    """
    :returns dict(ip_address, msg, changed): dictionary resulting of the request,
    where 'ip_address' is the serialized ip fetched or newly created in Netbox
    """
    if not isinstance(data, dict):
        changed = False
        return {"msg": data, "changed": changed}

    try:
        nb_addr = _search_ip(nb_endpoint, data)
    except ValueError:
        return _error_multiple_ip_results(data)

    result = {}
    if not nb_addr:
        return create_ip_address(nb_endpoint, data)
    else:
        ip_addr, diff = update_netbox_object(nb_addr, data, module.check_mode)
        if ip_addr is False:
            module.fail_json(
                msg="Request failed, couldn't update IP: %s" % (data["address"])
            )
        if diff:
            msg = "IP Address %s updated" % (data["address"])
            changed = True
            result["diff"] = diff
        else:
            ip_addr = nb_addr.serialize()
            changed = False
            msg = "IP Address %s already exists" % (data["address"])

        return {"ip_address": ip_addr, "msg": msg, "changed": changed}


def _search_ip(nb_endpoint, data):
    get_query_params = {"address": data["address"]}
    if data.get("vrf"):
        get_query_params["vrf_id"] = data["vrf"]

    ip_addr = nb_endpoint.get(**get_query_params)
    return ip_addr


def _error_multiple_ip_results(data):
    changed = False
    if "vrf" in data:
        return {"msg": "Returned more than result", "changed": changed}
    else:
        return {
            "msg": "Returned more than one result - Try specifying VRF.",
            "changed": changed
        }


def create_ip_address(nb_endpoint, data):
    if not isinstance(data, dict):
        changed = False
        return {"msg": data, "changed": changed}

    ip_addr, diff = create_netbox_object(nb_endpoint, data, module.check_mode)
    changed = True
    msg = "IP Addresses %s created" % (data["address"])

    return {"ip_address": ip_addr, "msg": msg, "changed": changed, "diff": diff}


def ensure_ip_in_prefix_present_on_netif(nb_app, nb_endpoint, data):
    """
    :returns dict(ip_address, msg, changed): dictionary resulting of the request,
    where 'ip_address' is the serialized ip fetched or newly created in Netbox
    """
    if not isinstance(data, dict):
        changed = False
        return {"msg": data, "changed": changed}

    if not data.get("interface") or not data.get("prefix"):
        raise ValueError("A prefix and interface are required")

    get_query_params = {
        "interface_id": data["interface"], "parent": data["prefix"],
    }
    if data.get("vrf"):
        get_query_params["vrf_id"] = data["vrf"]

    attached_ips = nb_endpoint.filter(**get_query_params)
    if attached_ips:
        ip_addr = attached_ips[-1].serialize()
        changed = False
        msg = "IP Address %s already attached" % (ip_addr["address"])

        return {"ip_address": ip_addr, "msg": msg, "changed": changed}
    else:
        return get_new_available_ip_address(nb_app, data)


def get_new_available_ip_address(nb_app, data):
    prefix_query = {"prefix": data["prefix"]}
    if data.get("vrf"):
        prefix_query["vrf_id"] = data["vrf"]

    result = {}
    prefix = nb_app.prefixes.get(**prefix_query)
    if not prefix:
        changed = False
        msg = "%s does not exist - please create first" % (data["prefix"])
        return {"msg": msg, "changed": changed}
    elif prefix.available_ips.list():
        ip_addr, diff = create_netbox_object(prefix.available_ips, data, module.check_mode)
        changed = True
        msg = "IP Addresses %s created" % (ip_addr["address"])
        result["diff"] = diff
    else:
        changed = False
        msg = "No available IPs available within %s" % (data['prefix'])
        return {"msg": msg, "changed": changed}

    result.update({"ip_address": ip_addr, "msg": msg, "changed": changed})
    return result


def _get_prefix_id(nb_app, prefix, vrf_id=None):
    ipaddr_prefix = ipaddress.ip_network(prefix)
    network = to_text(ipaddr_prefix.network_address)
    mask = ipaddr_prefix.prefixlen

    prefix_query_params = {
        "prefix": network,
        "mask_length": mask
    }
    if vrf_id:
        prefix_query_params["vrf_id"] = vrf_id

    prefix_id = nb_app.prefixes.get(prefix_query_params)
    if not prefix_id:
        if vrf_id:
            raise ValueError("Prefix %s does not exist in VRF %s - Please create it" % (prefix, vrf_id))
        else:
            raise ValueError("Prefix %s does not exist - Please create it" % (prefix))

    return prefix_id


def ensure_ip_address_absent(nb_endpoint, data):
    """
    :returns dict(msg, changed)
    """
    if not isinstance(data, dict):
        changed = False
        return {"msg": data, "changed": changed}

    try:
        ip_addr = _search_ip(nb_endpoint, data)
    except ValueError:
        return _error_multiple_ip_results(data)

    result = {}
    if ip_addr:
        dummy, diff = delete_netbox_object(ip_addr, module.check_mode)
        changed = True
        msg = "IP Address %s deleted" % (data["address"])
        result["diff"] = diff
    else:
        changed = False
        msg = "IP Address %s already absent" % (data["address"])

    result.update({"msg": msg, "changed": changed})
    return result


if __name__ == "__main__":
    main()
