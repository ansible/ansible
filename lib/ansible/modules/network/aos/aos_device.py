#!/usr/bin/python
#
# (c) 2017 Apstra Inc, <community@apstra.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: aos_device
author: Damien Garros (@dgarros)
version_added: "2.3"
short_description: Manage Devices on AOS Server
description:
  - Apstra AOS Device module let you manage your devices in AOS easily. You can
    approve devices and define in which state the device should be. Currently
    only the state I(normal) is supported but the goal is to extend this module
    with additional state. This module is idempotent and support the I(check) mode.
    It's using the AOS REST API.
requirements:
  - "aos-pyez >= 0.6.0"
options:
  session:
    description:
      - An existing AOS session as obtained by M(aos_login) module.
    required: true
  name:
    description:
      - The device serial-number; i.e. uniquely identifies the device in the
        AOS system. Only one of I(name) or I(id) can be set.
  id:
    description:
      - The AOS internal id for a device; i.e. uniquely identifies the device in the
        AOS system. Only one of I(name) or I(id) can be set.
  state:
    description:
      - Define in which state the device should be. Currently only I(normal)
        is supported but the goal is to add I(maint) and I(decomm).
    default: normal
    choices: ['normal']
  approve:
    description:
      - The approve argument instruct the module to convert a device in quarantine
        mode into approved mode.
    default: "no"
    choices: [ "yes", "no" ]
  location:
    description:
      - When approving a device using the I(approve) argument, it's possible
        define the location of the device.
'''

EXAMPLES = '''

- name: Approve a new device
  aos_device:
    session: "{{ aos_session }}"
    name: D2060B2F105429GDABCD123
    state: 'normal'
    approve: true
    location: "rack-45, ru-18"
'''


RETURNS = '''
name:
  description: Name of the Device, usually the serial-number.
  returned: always
  type: str
  sample: Server-IpAddrs

id:
  description: AOS unique ID assigned to the Device
  returned: always
  type: str
  sample: fcc4ac1c-e249-4fe7-b458-2138bfb44c06

value:
  description: Value of the object as returned by the AOS Server
  returned: always
  type: dict
  sample: {'...'}
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.aos.aos import HAS_AOS_PYEZ, get_aos_session, check_aos_version, find_collection_item

if HAS_AOS_PYEZ:
    from apstra.aosom.exc import SessionError, SessionRqstError


def aos_device_normal(module, aos, dev):

    margs = module.params

    # If approve is define, check if the device needs to be approved or not
    if margs['approve'] is not None:

        if dev.is_approved:
            module.exit_json(changed=False,
                             name=dev.name,
                             id=dev.id,
                             value=dev.value)

        if not module.check_mode:
            try:
                dev.approve(location=margs['location'])
            except (SessionError, SessionRqstError):
                module.fail_json(msg="Unable to approve device")\

        module.exit_json(changed=True,
                         name=dev.name,
                         id=dev.id,
                         value=dev.value)
    else:
        # Check if the device is online
        if dev.state in ('OOS-READY', 'IS-READY'):
            module.exit_json(changed=False,
                             name=dev.name,
                             id=dev.id,
                             value=dev.value)
        else:
            module.fail_json(msg="Device is in '%s' state" % dev.state)


def aos_device(module):
    margs = module.params

    try:
        aos = get_aos_session(module, margs['session'])
    except:
        module.fail_json(msg="Unable to login to the AOS server")

    item_name = False
    item_id = False

    if margs['id'] is not None:
        item_id = margs['id']

    elif margs['name'] is not None:
        item_name = margs['name']

    # ----------------------------------------------------
    # Find Object if available based on ID or Name
    # ----------------------------------------------------
    dev = find_collection_item(aos.Devices,
                               item_name=item_name,
                               item_id=item_id)

    if dev.exists is False:
        module.fail_json(msg="unknown device '%s'" % margs['name'])

    # ----------------------------------------------------
    # Valid device state for reference
    # ----------------------------------------------------
        # DEVICE_STATE_IS_ACTIVE = 1;
        # DEVICE_STATE_IS_READY = 2;
        # DEVICE_STATE_IS_NOCOMMS = 3;
        # DEVICE_STATE_IS_MAINT = 4;
        # DEVICE_STATE_IS_REBOOTING = 5;
        # DEVICE_STATE_OOS_STOCKED = 6;
        # DEVICE_STATE_OOS_QUARANTINED = 7;
        # DEVICE_STATE_OOS_READY = 8;
        # DEVICE_STATE_OOS_NOCOMMS = 9;
        # DEVICE_STATE_OOS_DECOMM = 10;
        # DEVICE_STATE_OOS_MAINT = 11;
        # DEVICE_STATE_OOS_REBOOTING = 12;
        # DEVICE_STATE_ERROR = 13;
    # ----------------------------------------------------
    # State == Normal
    # ----------------------------------------------------
    if margs['state'] == 'normal':
        aos_device_normal(module, aos, dev)


def main():

    module = AnsibleModule(
        argument_spec=dict(
            session=dict(required=True, type="dict"),
            name=dict(required=False),
            id=dict(required=False),
            state=dict(choices=['normal'],
                       default='normal'),
            approve=dict(required=False, type='bool'),
            location=dict(required=False, default='')
        ),
        mutually_exclusive=[('name', 'id')],
        required_one_of=[('name', 'id')],
        supports_check_mode=True
    )

    # Check if aos-pyez is present and match the minimum version
    check_aos_version(module, '0.6.0')

    aos_device(module)

if __name__ == "__main__":
    main()
