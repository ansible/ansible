#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Mikhail Yohman (@FragmentedPacket) <mikhail.yohman@gmail.com>
# Copyright: (c) 2019, Alexander Stauch (@BlackestDawn) <blacke4dawn@gmail.com>
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
  - Alexander Stauch (@BlackestDawn)
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
        type: int
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
from ansible.module_utils.net_tools.netbox.netbox_utils import *
from ansible.module_utils.compat import ipaddress
from ansible.module_utils._text import to_text


PYNETBOX_IMP_ERR = None
try:
    import pynetbox
    HAS_PYNETBOX = True
except ImportError:
    PYNETBOX_IMP_ERR = traceback.format_exc()
    HAS_PYNETBOX = False

class PyNetboxPrefix(PyNetboxBase):
    def __init__(self, module):
        """Constructor"""
        super(PyNetboxPrefix, self).__init__(module)
        self.first_available = module.params["first_available"]
        self._set_endpoint('prefixes')
        # Main parameters for status messages and return data
        self.param_usage = {
            'type': "prefix",
            'success': "prefix",
            'fail': "prefix",
            'rname': "prefix",
            'search': "prefix"
        }

    def run_module(self):
        """Main runner"""
        # Creates or updates prefix as necessary
        if self.state == "present":
            if self.first_available:
                if (
                    'parent' in self.normalized_data and
                    'prefix_length' in self.normalized_data
                ):
                    parent_prefix = self._search_prefix()
                    if not parent_prefix:
                        self.module.fail_json(msg="Parent prefix does not exist: %s" % (self.normalized_data['parent']))
                    elif parent_prefix.available_prefixes.list():
                        self._create_object(endpoint=parent_prefix.available_prefixes, fail_param="parent")
                    else:
                        self.result['msg'] = "No available prefixes within %s" % (self.normalized_data['prefix'])
                else:
                    raise ValueError("'prefix' and 'prefix_length' is required with first_available")
            else:
                if 'prefix' in self.normalized_data:
                    self.ensure_object_present()
                else:
                    self.module.fail_json(msg="'prefix' is required without first_available")

        # Removes prefix if present
        elif self.state == "absent":
            self.ensure_object_absent()

        # Unknown state
        else:
            return self.module.fail_json(msg="Invalid state %s" % self.state)
        self.module.exit_json(**self.result)

    # Helper methods
    def _check_and_adapt_data(self):
        """Overridden parent method"""
        data = self._find_ids(self.normalized_data)
        if 'vrf' in data and not isinstance(data["vrf"], int):
            raise ValueError(
                "%s does not exist - Please create VRF" % (data["vrf"])
            )
        if 'status' in data:
            data["status"] = PREFIX_STATUS.get(data["status"].lower())
        self.normalized_data.update(data)

    def _multiple_results_error(self, data=None):
        """Overridden parent method"""
        if data is None:
            data = self.normalized_data
        if 'vrf' in self.normalized_data:
            return {"msg": "Returned more than one result", "changed": False}
        else:
            return {
                "msg": "Returned more than one result - Try specifying VRF.",
                "changed": False
            }

    def _search_prefix(self):
        """Returns prefix object"""
        if 'prefix' in self.normalized_data:
            prefix = ipaddress.ip_network(self.normalized_data["prefix"])
        elif 'parent' in self.normalized_data:
            prefix = ipaddress.ip_network(self.normalized_data["parent"])
        query_params = {
            'q': to_text(prefix.network_address),
            'mask_length': prefix.prefixlen,
            'vrf': "null"
        }
        if 'vrf' in self.normalized_data:
            query_params['vrf_id'] = self.normalized_data['vrf']
        return self._retrieve_object(query_params)

def main():
    """
    Main entry point for module execution
    """
    argument_spec = netbox_argument_spec()
    argument_spec.update( dict(
        state=dict(required=False, default="present", choices=["present", "absent"]),
        first_available=dict(type="bool", required=False, default=False),
    ))

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)
    pynb = PyNetboxPrefix(module)

    try:
        pynb.run_module()
    except pynetbox.RequestError as e:
        return module.fail_json(msg=json.loads(e.error))
    except ValueError as e:
        return module.fail_json(msg=str(e))
    except AttributeError as e:
        return module.fail_json(msg=str(e))

if __name__ == "__main__":
    main()