#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Mikhail Yohman (@FragmentedPacket) <mikhail.yohman@gmail.com>
# Copyright: (c) 2018, David Gomez (@amb1s1) <david.gomez@networktocode.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: netbox_device
short_description: Create or delete devices within Netbox
description:
  - Creates or removes devices from Netbox
notes:
  - Tags should be defined as a YAML list
  - This should be ran with connection C(local) and hosts C(localhost)
author:
  - Mikhail Yohman (@FragmentedPacket)
  - David Gomez (@amb1s1)
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
      - Defines the device configuration
    suboptions:
      name:
        description:
          - The name of the device
      device_type:
        description:
          - Required if I(state=present)
      device_role:
        description:
          - Required if I(state=present)
      tenant:
        description:
          - The tenant that the device will be assigned to
      platform:
        description:
          - The platform of the device
      serial:
        description:
          - Serial number of the device
      asset_tag:
        description:
          - Asset tag that is associated to the device
      site:
        description:
          - Required if I(state=present)
      rack:
        description:
          - The name of the rack to assign the device to
      position:
        description:
          - The position of the device in the rack defined above
      face:
        description:
          - Required if I(rack) is defined
      status:
        description:
          - The status of the device
        choices:
          - Active
          - Offline
          - Planned
          - Staged
          - Failed
          - Inventory
      cluster:
        description:
          - Cluster that the device will be assigned to
      comments:
        description:
          - Comments that may include additional information in regards to the device
      tags:
        description:
          - Any tags that the device may need to be associated with
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
- name: "Test Netbox modules"
  connection: local
  hosts: localhost
  gather_facts: False

  tasks:
    - name: Create device within Netbox with only required information
      netbox_device:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          name: Test (not really required, but helpful)
          device_type: C9410R
          device_role: Core Switch
          site: Main
        state: present

    - name: Delete device within netbox
      netbox_device:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          name: Test
        state: absent

    - name: Create device with tags
      netbox_device:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          name: Test
          device_type: C9410R
          device_role: Core Switch
          site: Main
          tags:
            - Schnozzberry
        state: present

    - name: Create device and assign to rack and position
      netbox_device:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          name: Test
          device_type: C9410R
          device_role: Core Switch
          site: Main
          rack: Test Rack
          position: 10
          face: Front
'''

RETURN = r'''
device:
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
from ansible.module_utils.net_tools.netbox.netbox_utils import find_ids, normalize_data, DEVICE_STATUS, FACE_ID

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
        state=dict(required=False, default='present', choices=['present', 'absent']),
        validate_certs=dict(type="bool", default=True)
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False)

    # Fail module if pynetbox is not installed
    if not HAS_PYNETBOX:
        module.fail_json(msg=missing_required_lib('pynetbox'), exception=PYNETBOX_IMP_ERR)

    # Assign variables to be used with module
    app = 'dcim'
    endpoint = 'devices'
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
                **ensure_device_present(nb, nb_endpoint, norm_data)
            )
        else:
            return module.exit_json(
                **ensure_device_absent(nb_endpoint, norm_data)
            )
    except pynetbox.RequestError as e:
        return module.fail_json(msg=json.loads(e.error))


def ensure_device_present(nb, nb_endpoint, data):
    '''
    :returns dict(device, msg, changed): dictionary resulting of the request,
        where `device` is the serialized device fetched or newly created in
        Netbox
    '''
    nb_device = nb_endpoint.get(name=data["name"])
    if not nb_device:
        device = _netbox_create_device(nb, nb_endpoint, data).serialize()
        changed = True
        msg = "Device %s created" % (data["name"])
    else:
        msg = "Device %s already exists" % (data["name"])
        device = nb_device.serialize()
        changed = False

    return {"device": device, "msg": msg, "changed": changed}


def _netbox_create_device(nb, nb_endpoint, data):
    if data.get("status"):
        data["status"] = DEVICE_STATUS.get(data["status"].lower(), 0)
    if data.get("face"):
        data["face"] = FACE_ID.get(data["face"].lower(), 0)
    data = find_ids(nb, data)
    return nb_endpoint.create(data)


def ensure_device_absent(nb_endpoint, data):
    '''
    :returns dict(msg, changed)
    '''
    device = nb_endpoint.get(name=data["name"])
    if device:
        device.delete()
        msg = 'Device %s deleted' % (data["name"])
        changed = True
    else:
        msg = 'Device %s already absent' % (data["name"])
        changed = False

    return {"msg": msg, "changed": changed}


if __name__ == "__main__":
    main()
