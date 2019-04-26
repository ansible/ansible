#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Mikhail Yohman (@FragmentedPacket) <mikhail.yohman@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {"metadata_version": "1.1",
                    "status": ["preview"],
                    "supported_by": "community"}

DOCUMENTATION = r"""
---
module: netbox_prefix
short_description: Creates or removes prefixes from Netbox
description:
  - Creates or removes prefixes from Netbox
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
    type: str
  netbox_token:
    description:
      - The token created within Netbox to authorize API access
    required: true
    type: str
  data:
    description:
      - Defines the prefix configuration
    suboptions:
      family:
        description:
          - Specifies which address family the prefix prefix belongs to
        choices:
          - 4
          - 6
        type: int
      prefix:
        description:
          - Required if state is C(present) and first_available is False. Will allocate or free this prefix.
        type: str
      parent:
        description:
          - Required if state is C(present) and first_available is C(yes). Will get a new available prefix in this parent prefix.
        type: str
      prefix_length:
        description:
          - |
            Required ONLY if state is C(present) and first_available is C(yes).
            Will get a new available prefix of the given prefix_length in this parent prefix.
        type: str
      site:
        description:
          - Site that prefix is associated with
        type: str
      vrf:
        description:
          - VRF that prefix is associated with
        type: str
      tenant:
        description:
          - The tenant that the prefix will be assigned to
        type: str
      vlan:
        description:
          - The VLAN the prefix will be assigned to
        type: dict
      status:
        description:
          - The status of the prefix
        choices:
          - Active
          - Container
          - Deprecated
          - Reserved
        type: str
      role:
        description:
          - The role of the prefix
        type: str
      is_pool:
        description:
          - All IP Addresses within this prefix are considered usable
        type: bool
      description:
        description:
          - The description of the prefix
        type: str
      tags:
        description:
          - Any tags that the prefix may need to be associated with
        type: list
      custom_fields:
        description:
          - Must exist in Netbox and in key/value format
        type: dict
    required: true
  state:
    description:
      - Use C(present) or C(absent) for adding or removing.
    choices: [ absent, present ]
    default: present
  first_available:
    description:
      - If C(yes) and state C(present), if an parent is given, it will get the
        first available prefix of the given prefix_length inside the given parent (and
        vrf, if given).
        Unused with state C(absent).
    default: 'no'
    type: bool
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used on personally controlled sites using self-signed certificates.
    default: "yes"
    type: bool
"""

EXAMPLES = r"""
- name: "Test Netbox prefix module"
  connection: local
  hosts: localhost
  gather_facts: False

  tasks:
    - name: Create prefix within Netbox with only required information
      netbox_prefix:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          prefix: 10.156.0.0/19
        state: present

    - name: Delete prefix within netbox
      netbox_prefix:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          prefix: 10.156.0.0/19
        state: absent

    - name: Create prefix with several specified options
      netbox_prefix:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          family: 4
          prefix: 10.156.32.0/19
          site: Test Site
          vrf: Test VRF
          tenant: Test Tenant
          vlan:
            name: Test VLAN
            site: Test Site
            tenant: Test Tenant
            vlan_group: Test Vlan Group
          status: Reserved
          role: Network of care
          description: Test description
          is_pool: true
          tags:
            - Schnozzberry
        state: present

    - name: Get a new /24 inside 10.156.0.0/19 within Netbox - Parent doesn't exist
      netbox_prefix:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          parent: 10.156.0.0/19
          prefix_length: 24
        state: present
        first_available: yes

    - name: Create prefix within Netbox with only required information
      netbox_prefix:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          prefix: 10.156.0.0/19
        state: present

    - name: Get a new /24 inside 10.156.0.0/19 within Netbox
      netbox_prefix:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          parent: 10.156.0.0/19
          prefix_length: 24
        state: present
        first_available: yes

    - name: Get a new /24 inside 10.157.0.0/19 within Netbox with additional values
      netbox_prefix:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          parent: 10.157.0.0/19
          prefix_length: 24
          vrf: Test VRF
          site: Test Site
        state: present
        first_available: yes
"""

RETURN = r"""
prefix:
  description: Serialized object as created or already existent within Netbox
  returned: on creation
  type: dict
msg:
  description: Message indicating failure or info about what has been achieved
  returned: always
  type: str
"""

import json
import traceback
import re

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.net_tools.netbox.netbox_utils import (
    find_ids,
    normalize_data,
    create_netbox_object,
    delete_netbox_object,
    update_netbox_object,
    PREFIX_STATUS,
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
    """
    Main entry point for module execution
    """
    argument_spec = dict(
        netbox_url=dict(type="str", required=True),
        netbox_token=dict(type="str", required=True, no_log=True),
        data=dict(type="dict", required=True),
        state=dict(required=False, default="present", choices=["present", "absent"]),
        first_available=dict(type="bool", required=False, default=False),
        validate_certs=dict(type="bool", default=True),
    )

    global module
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    # Fail module if pynetbox is not installed
    if not HAS_PYNETBOX:
        module.fail_json(msg=missing_required_lib('pynetbox'), exception=PYNETBOX_IMP_ERR)

    # Assign variables to be used with module
    app = "ipam"
    endpoint = "prefixes"
    url = module.params["netbox_url"]
    token = module.params["netbox_token"]
    data = module.params["data"]
    state = module.params["state"]
    first_available = module.params["first_available"]
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
        if "present" in state:
            return module.exit_json(**ensure_prefix_present(
                nb, nb_endpoint, norm_data, first_available
            ))
        else:
            return module.exit_json(
                **ensure_prefix_absent(nb, nb_endpoint, norm_data)
            )
    except pynetbox.RequestError as e:
        return module.fail_json(msg=json.loads(e.error))
    except ValueError as e:
        return module.fail_json(msg=str(e))
    except AttributeError as e:
        return module.fail_json(msg=str(e))


def ensure_prefix_present(nb, nb_endpoint, data, first_available=False):
    """
    :returns dict(prefix, msg, changed): dictionary resulting of the request,
    where 'prefix' is the serialized device fetched or newly created in Netbox
    """
    if not isinstance(data, dict):
        changed = False
        return {"msg": data, "changed": changed}

    if first_available:
        for k in ("parent", "prefix_length"):
            if k not in data:
                raise ValueError("'%s' is required with first_available" % k)

        return get_new_available_prefix(nb_endpoint, data)
    else:
        if "prefix" not in data:
            raise ValueError("'prefix' is required without first_available")

        return get_or_create_prefix(nb_endpoint, data)


def _check_and_adapt_data(nb, data):
    data = find_ids(nb, data)

    if data.get("vrf") and not isinstance(data["vrf"], int):
        raise ValueError(
            "%s does not exist - Please create VRF" % (data["vrf"])
        )

    if data.get("status"):
        data["status"] = PREFIX_STATUS.get(data["status"].lower())

    return data


def _search_prefix(nb_endpoint, data):
    if data.get("prefix"):
        prefix = ipaddress.ip_network(data["prefix"])
    elif data.get("parent"):
        prefix = ipaddress.ip_network(data["parent"])

    network = to_text(prefix.network_address)
    mask = prefix.prefixlen

    if data.get("vrf"):
        if not isinstance(data["vrf"], int):
            raise ValueError("%s does not exist - Please create VRF" % (data["vrf"]))
        else:
            prefix = nb_endpoint.get(q=network, mask_length=mask, vrf_id=data["vrf"])
    else:
        prefix = nb_endpoint.get(q=network, mask_length=mask, vrf="null")

    return prefix


def _error_multiple_prefix_results(data):
    changed = False

    if data.get("vrf"):
        return {"msg": "Returned more than one result", "changed": changed}
    else:
        return {
            "msg": "Returned more than one result - Try specifying VRF.",
            "changed": changed
        }


def get_or_create_prefix(nb_endpoint, data):
    try:
        nb_prefix = _search_prefix(nb_endpoint, data)
    except ValueError:
        return _error_multiple_prefix_results(data)

    result = dict()
    if not nb_prefix:
        prefix, diff = create_netbox_object(nb_endpoint, data, module.check_mode)
        changed = True
        msg = "Prefix %s created" % (prefix["prefix"])
        result["diff"] = diff
    else:
        prefix, diff = update_netbox_object(nb_prefix, data, module.check_mode)
        if prefix is False:
            module.fail_json(
                msg="Request failed, couldn't update prefix: %s" % (data["prefix"])
            )
        if diff:
            msg = "Prefix %s updated" % (data["prefix"])
            changed = True
            result["diff"] = diff
        else:
            msg = "Prefix %s already exists" % (data["prefix"])
            changed = False

    result.update({"prefix": prefix, "msg": msg, "changed": changed})
    return result


def get_new_available_prefix(nb_endpoint, data):
    try:
        parent_prefix = _search_prefix(nb_endpoint, data)
    except ValueError:
        return _error_multiple_prefix_results(data)

    result = dict()
    if not parent_prefix:
        changed = False
        msg = "Parent prefix does not exist: %s" % (data["parent"])
        return {"msg": msg, "changed": changed}
    elif parent_prefix.available_prefixes.list():
        prefix, diff = create_netbox_object(parent_prefix.available_prefixes, data, module.check_mode)
        changed = True
        msg = "Prefix %s created" % (prefix["prefix"])
        result["diff"] = diff
    else:
        changed = False
        msg = "No available prefixes within %s" % (data["parent"])

    result.update({"prefix": prefix, "msg": msg, "changed": changed})
    return result


def ensure_prefix_absent(nb, nb_endpoint, data):
    """
    :returns dict(msg, changed)
    """
    try:
        nb_prefix = _search_prefix(nb_endpoint, data)
    except ValueError:
        return _error_multiple_prefix_results(data)

    result = dict()
    if nb_prefix:
        dummy, diff = delete_netbox_object(nb_prefix, module.check_mode)
        changed = True
        msg = "Prefix %s deleted" % (nb_prefix.prefix)
        result["diff"] = diff
    else:
        msg = "Prefix %s already absent" % (data["prefix"])
        changed = False

    result.update({"msg": msg, "changed": changed})
    return result


if __name__ == "__main__":
    main()
