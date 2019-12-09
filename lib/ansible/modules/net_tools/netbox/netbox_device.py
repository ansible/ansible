#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Mikhail Yohman (@FragmentedPacket) <mikhail.yohman@gmail.com>
# Copyright: (c) 2018, David Gomez (@amb1s1) <david.gomez@networktocode.com>
# Copyright: (c) 2019, Alexander Stauch (@BlackestDawn) <blacke4dawn@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: netbox_device
short_description: Create, update or delete devices within Netbox
description:
  - Creates, updates or removes devices from Netbox
notes:
  - Tags should be defined as a YAML list
  - This should be ran with connection C(local) and hosts C(localhost)
author:
  - Mikhail Yohman (@FragmentedPacket)
  - David Gomez (@amb1s1)
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
      - Defines the device configuration
    suboptions:
      name:
        description:
          - The name of the device
        required: true
      device_type:
        description:
          - Required if I(state=present) and the device does not exist yet
      device_role:
        description:
          - Required if I(state=present) and the device does not exist yet
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
          - Required if I(state=present) and the device does not exist yet
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
          name: Test Device
          device_type: C9410R
          device_role: Core Switch
          site: Main
        state: present

    - name: Delete device within netbox
      netbox_device:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          name: Test Device
        state: absent

    - name: Create device with tags
      netbox_device:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          name: Another Test Device
          device_type: C9410R
          device_role: Core Switch
          site: Main
          tags:
            - Schnozzberry
        state: present

    - name: Update the rack and position of an existing device
      netbox_device:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          name: Test Device
          rack: Test Rack
          position: 10
          face: Front
        state: present
'''

RETURN = r'''
device:
  description: Serialized object as created or already existent within Netbox
  returned: success (when I(state=present))
  type: dict
msg:
  description: Message indicating failure or info about what has been achieved
  returned: always
  type: str
'''

import json
import traceback

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.net_tools.netbox.netbox_utils import *

PYNETBOX_IMP_ERR = None
try:
    import pynetbox
    HAS_PYNETBOX = True
except ImportError:
    PYNETBOX_IMP_ERR = traceback.format_exc()
    HAS_PYNETBOX = False

class PyNetboxDevice(PyNetboxBase):
    def __init__(self, module):
        """Constructor"""
        super(PyNetboxDevice, self).__init__(module)
        self._set_endpoint('devices')
        # Main parameters for status messages and return data
        self.param_usage = {
            'type': "device",
            'success': "name",
            'fail': "name",
            'rname': "device",
            'search': "name"
        }

    def run_module(self):
        """Main runner"""
        # Checks for existing device and creates or updates as necessary
        if self.state == "present":
            if "status" in self.normalized_data:
                self.normalized_data["status"] = DEVICE_STATUS.get(self.normalized_data["status"].lower())
            if "face" in self.normalized_data:
                self.normalized_data["face"] = FACE_ID.get(self.normalized_data["face"].lower())
            self._find_ids()
            self.ensure_object_present()

        # Deletes device if present
        elif self.state == "absent":
            self.ensure_object_absent()

        # Unknown state
        else:
            return self.module.fail_json(msg="Invalid state %s" % self.state)
        self.module.exit_json(**self.result)

def main():
    '''
    Main entry point for module execution
    '''
    argument_spec = netbox_argument_spec()
    argument_spec.update( dict(
        state=dict(required=False, default='present', choices=['present', 'absent'])
    ))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    pynb = PyNetboxDevice(module)

    try:
        pynb.run_module()
    except pynetbox.RequestError as e:
        return module.fail_json(msg=json.loads(e.error))
    except ValueError as e:
        return module.fail_json(msg=str(e))

if __name__ == "__main__":
    main()
