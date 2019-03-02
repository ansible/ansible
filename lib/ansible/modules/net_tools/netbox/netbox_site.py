#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Mikhail Yohman (@fragmentedpacket) <mikhail.yohman@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {"metadata_version": "1.1",
                    "status": ["preview"],
                    "supported_by": "community"}

DOCUMENTATION = r"""
---
module: netbox_site
short_description: Creates or removes sites from Netbox
description:
  - Creates or removes sites from Netbox
notes:
  - Tags should be defined as a YAML list
  - This should be ran with connection C(local) and hosts C(localhost)
author:
  - Mikhail Yohman (@FragmentedPacket)
requirements:
  - pynetbox
version_added: "2.8"
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
      - Defines the site configuration
    suboptions:
      name:
        description:
          - Name of the site to be created
        required: true
      status:
        description:
          - Status of the site
        choices:
          - Active
          - Planned
          - Retired 
      region:
        description:
          - The region that the site should be associated with 
      tenant:
        description:
          - The tenant the site will be assigned to
      facility:
        description:
          - |
            Data center provider or facility
            ex. Equinix NY7
      asn:
        description:
          - The ASN associated with the site
        type: integer
      time_zone:
        description:
          - |
            Timezone associated with the site
            ex. America/Denver
      description:
        description:
          - The description of the prefix
      physical_address:
        description:
          - Physical address of site 
      shipping_address:
        description:
          - Shipping address of site
      latitude:
        description:
          - Latitude in decimal format
      longitude:
        description:
          - Longitude in decimal format
      contact_name:
        description:
          - Name of contact for site
      contact_phone:
        description:
          - Contact phone number for site
      contact_email:
        description:
          - Contact email for site
      comments:
        description:
          - Comments for the site. This can be markdown syntax
      tags:
        description:
          - Any tags that the prefix may need to be associated with
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
      - |
        If C(no), SSL certificates will not be validated.
        This should only be used on personally controlled sites using self-signed certificates.
    default: "yes"
    type: bool
"""

EXAMPLES = r"""
- name: "Test Netbox site module"
  connection: local
  hosts: localhost
  gather_facts: False
  tasks:
    - name: Create site within Netbox with only required information
      netbox_site:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          name: Test - Colorado
        state: present

    - name: Delete site within netbox
      netbox_site:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          name: Test - Colorado 
        state: absent

    - name: Create site with all parameters
      netbox_site:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          name: Test - California 
          status: Planned
          region: Test Region
          tenant: Test Tenant
          facility: EquinoxCA7
          asn: 65001
          time_zone: America/Los Angeles
          description: This is a test description
          physical_address: Hollywood, CA, 90210
          shipping_address: Hollywood, CA, 90210
          latitude: 10.100000
          longitude: 12.200000
          contact_name: Jenny
          contact_phone: 867-5309
          contact_email: jenny@changednumber.com
          comments: ### Placeholder
        state: present
"""

RETURN = r"""
site:
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
from ansible.module_utils.net_tools.netbox.netbox_utils import find_ids, normalize_data, SITE_STATUS 
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
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False)
    # Fail module if pynetbox is not installed
    if not HAS_PYNETBOX:
        module.fail_json(msg=missing_required_lib('pynetbox'), exception=PYNETBOX_IMP_ERR)
    # Assign variables to be used with module
    app = "dcim"
    endpoint = "sites"
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

        if "present" in state:
            return module.exit_json(
                **ensure_site_present(nb, nb_endpoint, norm_data)
            )
        else:
            return module.exit_json(
                **ensure_site_absent(nb, nb_endpoint, norm_data)
            )
    except pynetbox.RequestError as e:
        return module.fail_json(msg=json.loads(e.error))
    except ValueError as e:
        return module.fail_json(msg=str(e))
    except AttributeError as e:
        return module.fail_json(msg=str(e))


def _check_and_adapt_data(nb, data):
    data = find_ids(nb, data)

    if data.get("status"):
        data["status"] = SITE_STATUS.get(data["status"].lower())

    if "-" in data["name"]:
        site_slug = data["name"].replace(" ", "").lower()
    elif " " in data["name"]:
        site_slug = data["name"].replace(" ", "-").lower()
    else:
        site_slug = data["name"].lower()

    data["slug"] = site_slug

    return data


def ensure_site_present(nb, nb_endpoint, data):
    """
    :returns dict(interface, msg, changed): dictionary resulting of the request,
    where 'site' is the serialized interface fetched or newly created in Netbox
    """

    if not isinstance(data, dict):
        changed = False
        return {"msg": data, "changed": changed}

    site = nb_endpoint.get(slug=data["slug"])

    if not site:
        site = nb_endpoint.create(data).serialize()
        changed = True
        msg = "Site %s created" % (data["name"])
    else:
        site = site.serialize()
        msg = "Site %s already exists" % (data["name"])
        changed = False

    return {"site": site, "msg": msg, "changed": changed}


def ensure_site_absent(nb, nb_endpoint, data):
    """
    :returns dict(msg, changed)
    """
    site = nb_endpoint.get(slug=data["slug"])

    if site:
        site.delete()
        changed = True
        msg = "Site %s deleted" % (data["name"])
    else:
        msg = "Site %s already absent" % (data["name"])
        changed = False

    return {"msg": msg, "changed": changed}


if __name__ == "__main__":
    main()
