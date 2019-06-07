#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Mikhail Yohman (@fragmentedpacket) <mikhail.yohman@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {"metadata_version": "1.1",
                    "status": ["preview"],
                    "supported_by": "community"}

DOCUMENTATION = r"""
---
module: netbox_tenant
short_description: Creates or removes tenants from Netbox
description:
  - Creates or removes tenants from Netbox
notes:
  - Tags should be defined as a YAML list
  - This should be ran with connection C(local) and hosts C(localhost)
author:
  - Amy Liebowitz (@amylieb)
  - Adapted from netbox_site module by Mikhail Yohman (@FragmentedPacket)
requirements:
  - pynetbox
version_added: "2.8"
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
      - Defines the site configuration
    suboptions:
      name:
        description:
          - Name of the tenant to be created
        required: true
        type: str
      group:
        description:
          - Tenant group this tenant should be in
        type: str
      description:
        description:
          - The description of the tenant
        type: str
      comments:
        description:
          - Comments for the tenant. This can be markdown syntax
        type: str
      tags:
        description:
          - Any tags that the tenant may need to be associated with
        type: list
      custom_fields:
        description:
          - must exist in Netbox
        type: dict
    required: true
  state:
    description:
      - Use C(present) or C(absent) for adding or removing.
    choices: [ absent, present ]
    default: present
    type: str
  validate_certs:
    description:
      - |
        If C(no), SSL certificates will not be validated.
        This should only be used on personally controlled sites using self-signed certificates.
    default: "yes"
    type: bool
"""

EXAMPLES = r"""
- name: "Test Netbox tenant module"
  connection: local
  hosts: localhost
  gather_facts: False
  tasks:
    - name: Create tenant within Netbox with only required information
      netbox_tenant:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          name: Tenant ABC
        state: present

    - name: Delete tenant within netbox
      netbox_tenant:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          name: Tenant ABC
        state: absent

    - name: Create tenant with all parameters
      netbox_tenant:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          name: Tenant ABC
          group: Very Special Tenants
          description: ABC Incorporated
          comments: "### This tenant is super cool"
          tags:
            - tagA
            - tagB
            - tagC
          custom_fields:
            acct_id: 123456
            customer_id: 78910
        state: present
"""

RETURN = r"""
tenant:
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

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.net_tools.netbox.netbox_utils import (
    find_ids,
    normalize_data,
    create_netbox_object,
    delete_netbox_object,
    update_netbox_object
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
        validate_certs=dict(type="bool", default=True)
    )

    global module
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    # Fail module if pynetbox is not installed
    if not HAS_PYNETBOX:
        module.fail_json(msg=missing_required_lib('pynetbox'), exception=PYNETBOX_IMP_ERR)
    # Assign variables to be used with module
    app = "tenancy"
    endpoint = "tenants"
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
    _check_and_adapt_data(nb,data)

    try:

        if "present" in state:
            return module.exit_json(
                **ensure_tenant_present(nb, nb_endpoint, norm_data)
            )
        else:
            return module.exit_json(
                **ensure_tenant_absent(nb, nb_endpoint, norm_data)
            )
    except pynetbox.RequestError as e:
        return module.fail_json(msg=json.loads(e.error))
    except ValueError as e:
        return module.fail_json(msg=str(e))
    except AttributeError as e:
        return module.fail_json(msg=str(e))

def _slugify(input):

    if "-" in input:
        input = input.replace(" ", "").lower()
    elif " " in input:
        input = input.replace(" ", "-").lower()
    else:
        input = input.lower()

    return input


def _check_and_adapt_data(nb,data):
    
    # group ID lookup
    if "group" in data:
      group_id = find_ids(nb,{"tenant_group":_slugify(data["group"])})
      data["group"] = group_id["tenant_group"]

    # slug required for creation
    data["slug"] = _slugify(data["name"])
    
    return data


def ensure_tenant_present(nb, nb_endpoint, data):
    """
    :returns dict(tenant, msg, changed): dictionary resulting of the request,
    where 'tenant' is the serialized tenant fetched or newly created in Netbox
    """

    if not isinstance(data, dict):
        changed = False
        return {"msg": data, "changed": changed}

    # can't query this endpoint based on slug, querying by name instead
    nb_tenant = nb_endpoint.get(name=data["name"])
    result = dict()
    if not nb_tenant:
        tenant, diff = create_netbox_object(nb_endpoint, data, module.check_mode)
        changed = True
        msg = "Tenant %s created" % (data["name"])
        result["diff"] = diff
    else:
        tenant, diff = update_netbox_object(nb_tenant, data, module.check_mode)
        if tenant is False:
            module.fail_json(
                msg="Request failed, couldn't update tenant: %s" % (data["name"])
            )
        if diff:
            msg = "Tenant %s updated" % (data["name"])
            changed = True
            result["diff"] = diff
        else:
            msg = "Tenant %s already exists" % (data["name"])
            changed = False

    result.update({"tenant": tenant, "msg": msg, "changed": changed})
    return result


def ensure_tenant_absent(nb, nb_endpoint, data):
    """
    :returns dict(msg, changed)
    """
    nb_tenant = nb_endpoint.get(name=data["name"])
    result = dict()
    if nb_tenant:
        dummy, diff = delete_netbox_object(nb_tenant, module.check_mode)
        changed = True
        msg = "Tenant %s deleted" % (data["name"])
        result["diff"] = diff
    else:
        msg = "Tenant %s already absent" % (data["name"])
        changed = False

    result.update({"msg": msg, "changed": changed})
    return result


if __name__ == "__main__":
    main()
