#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Mikhail Yohman (@fragmentedpacket) <mikhail.yohman@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: netbox_device
short_description: Manage devices
description:
- Creates or removes devices from Netbox
notes:
- Place holder for notes once this module starts to get tested.
author:
- Mikhail Yohman (@FragmentedPacket)
requirements:
- N/A
version_added: '2.8'
options:
  api_endpoint:
    description:
      - URL of the Netbox instance resolvable by Ansible control host
    required: true
  api_token:
    description:
      - The token created within Netbox to authorize API access
    required: true
  data:
    description:
      - Defines the device configuration
    choices:
      - name
      - device_type (required if state is C(present))
      - device_role (required if state is C(present))
      - tenant
      - platform
      - serial
      - asset_tag
      - site (required if state is C(present)
      - rack
      - position
      - face
      - status
      - cluster
      - comments
      - tags
      - custom_fields (must exist in Netbox)
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
    type: boolean
'''

EXAMPLES = r'''
name: Create device within Netbox with only required information
netbox_device:
  api_endpoint: http://netbox.local
  api_token: thisIsMyToken
  data:
    name: Test
    device_type: C9410R
    device_role: Core Switch
    site: Main
  state: present


'''

RETURN = r'''
Placeholder
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.net_tools.netbox.netbox_utils import netbox_add, netbox_delete

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
        data=dict(type="str", required=True),
        state=dict(required=False, default='present', choices=['present', 'absent']),
        validate_certs=dict(type="bool", default=True)
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False)
    if not HAS_PYNETBOX:
        module.fail_json(msg='pynetbox is required for this module')
    changed=False
    app = 'dcim'
    endpoint = 'devices'
    url = module.params["netbox_url"]
    token = module.params["netbox_token"]
    data = module.params["data"]
    state = module.params["state"]
    validate_certs = module.params["validate_certs"]
    nb = pynetbox.api(url, token=token, ssl_verify=validate_certs)
    nb_app = getattr(nb, app)
    nb_endpoint = getattr(nb_app, endpoint)
    if 'present' in state:
        response = netbox_add(nb, nb_endpoint, data)
    else:
        response = netbox_delete(nb_endpoint, data)
    module.exit_json(changed=changed, meta=response)


if __name__ == "__main__":
    main()

