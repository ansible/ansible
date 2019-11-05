#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Nurfet Becirevic <nurfet.becirevic@gmail.com>
# Copyright: (c) 2017, Tomas Karasek <tom.to.the.k@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: packet_volume

short_description: Create/delete a volume in Packet host.

description:
     - Create/delete a volume in Packet host.
     - API is documented at U(https://www.packet.com/developers/api/#volumes).

version_added: "2.10"

author:
    - Tomas Karasek (@t0mk) <tom.to.the.k@gmail.com>
    - Nurfet Becirevic (@nurfet-becirevic) <nurfet.becirevic@gmail.com>

options:
  state:
    description:
      - Desired state of the volume.
    default: present
    choices: ['present', 'absent']
    type: str

  project_id:
    description:
      - ID of project of the device.
    required: true
    type: str

  auth_token:
    description:
      - Packet api token. You can also supply it in env var C(PACKET_API_TOKEN).
    type: str

  name:
    description:
      - Selector for API-generated name of the volume
    type: str

  description:
    description:
      - User-defined description attribute for Packet volume.
      - "It is used used as idempotent identifier - if volume with given
        description exists, new one is not created."
    type: str

  id:
    description:
      - UUID of a volume.
    type: str

  plan:
    description:
      - storage_1 for standard tier, storage_2 for premium (performance) tier.
      - Tiers are described at U(https://www.packet.com/cloud/storage/).
    choices: ['storage_1', 'storage_2']
    default: 'storage_1'
    type: str

  facility:
    description:
      - Location of the volume.
      - Volumes can only be attached to device in the same location.
    type: str

  size:
    description:
      - Size of the volume in gigabytes.
    type: int

  locked:
    description:
     - Create new volume locked.
    type: bool
    default: False

  billing_cycle:
    description:
      - Billing cycle for new volume.
    choices: ['hourly', 'monthly']
    default: 'hourly'
    type: str

  snapshot_policy:
    description:
      - Snapshot policy for new volume.
    type: dict

    suboptions:
      snapshot_count:
        description:
          - How many snapshots to keep, a positive integer.
        required: True
        type: int

      snapshot_frequency:
        description:
          - Frequency of snapshots.
        required: True
        choices: ["15min", "1hour", "1day", "1week", "1month", "1year"]
        type: str

requirements:
  - "python >= 2.6"
  - "packet-python >= 1.35"

'''

EXAMPLES = '''
# All the examples assume that you have your Packet API token in env var PACKET_API_TOKEN.
# You can also pass the api token in module param auth_token.

- hosts: localhost
  vars:
    volname: testvol123
    project_id: 53000fb2-ee46-4673-93a8-de2c2bdba33b

  tasks:
    - name: test create volume
      packet_volume:
        description: "{{ volname }}"
        project_id: "{{ project_id }}"
        facility: 'ewr1'
        plan: 'storage_1'
        state: present
        size: 10
        snapshot_policy:
          snapshot_count: 10
          snapshot_frequency: 1day
      register: result_create

    - name: test delete volume
      packet_volume:
        id: "{{ result_create.id }}"
        project_id: "{{ project_id }}"
        state: absent
'''

RETURN = '''
id:
    description: UUID of specified volume
    type: str
    returned: success
    sample: 53000fb2-ee46-4673-93a8-de2c2bdba33c
name:
    description: The API-generated name of the volume resource.
    type: str
    returned: if volume is attached/detached to/from some device
    sample: "volume-a91dc506"
description:
    description: The user-defined description of the volume resource.
    type: str
    returned: success
    sample: "Just another volume"
'''

import uuid

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils._text import to_native

HAS_PACKET_SDK = True


try:
    import packet
except ImportError:
    HAS_PACKET_SDK = False


PACKET_API_TOKEN_ENV_VAR = "PACKET_API_TOKEN"

VOLUME_PLANS = ["storage_1", "storage_2"]
VOLUME_STATES = ["present", "absent"]
BILLING = ["hourly", "monthly"]


def is_valid_uuid(myuuid):
    try:
        val = uuid.UUID(myuuid, version=4)
    except ValueError:
        return False
    return str(val) == myuuid


def get_volume_selector(module):
    if module.params.get('id'):
        i = module.params.get('id')
        if not is_valid_uuid(i):
            raise Exception("Volume ID '{0}' is not a valid UUID".format(i))
        return lambda v: v['id'] == i
    elif module.params.get('name'):
        n = module.params.get('name')
        return lambda v: v['name'] == n
    elif module.params.get('description'):
        d = module.params.get('description')
        return lambda v: v['description'] == d


def get_or_fail(params, key):
    item = params.get(key)
    if item is None:
        raise Exception("{0} must be specified for new volume".format(key))
    return item


def act_on_volume(target_state, module, packet_conn):
    return_dict = {'changed': False}
    s = get_volume_selector(module)
    project_id = module.params.get("project_id")
    api_method = "projects/{0}/storage".format(project_id)
    all_volumes = packet_conn.call_api(api_method, "GET")['volumes']
    matching_volumes = [v for v in all_volumes if s(v)]

    if target_state == "present":
        if len(matching_volumes) == 0:
            params = {
                "description": get_or_fail(module.params, "description"),
                "size": get_or_fail(module.params, "size"),
                "plan": get_or_fail(module.params, "plan"),
                "facility": get_or_fail(module.params, "facility"),
                "locked": get_or_fail(module.params, "locked"),
                "billing_cycle": get_or_fail(module.params, "billing_cycle"),
                "snapshot_policies": module.params.get("snapshot_policy"),
            }

            new_volume_data = packet_conn.call_api(api_method, "POST", params)
            return_dict['changed'] = True
            for k in ['id', 'name', 'description']:
                return_dict[k] = new_volume_data[k]

        else:
            for k in ['id', 'name', 'description']:
                return_dict[k] = matching_volumes[0][k]

    else:
        if len(matching_volumes) > 1:
            _msg = ("More than one volume matches in module call for absent state: {0}".format(
                    to_native(matching_volumes)))
            module.fail_json(msg=_msg)

        if len(matching_volumes) == 1:
            volume = matching_volumes[0]
            packet_conn.call_api("storage/{0}".format(volume['id']), "DELETE")
            return_dict['changed'] = True
            for k in ['id', 'name', 'description']:
                return_dict[k] = volume[k]

    return return_dict


def main():
    module = AnsibleModule(
        argument_spec=dict(
            id=dict(type='str', default=None),
            description=dict(type="str", default=None),
            name=dict(type='str', default=None),
            state=dict(choices=VOLUME_STATES, default="present"),
            auth_token=dict(
                type='str',
                fallback=(env_fallback, [PACKET_API_TOKEN_ENV_VAR]),
                no_log=True
            ),
            project_id=dict(required=True),
            plan=dict(choices=VOLUME_PLANS, default="storage_1"),
            facility=dict(type="str"),
            size=dict(type="int"),
            locked=dict(type="bool", default=False),
            snapshot_policy=dict(type='dict', default=None),
            billing_cycle=dict(type='str', choices=BILLING, default="hourly"),
        ),
        supports_check_mode=True,
        required_one_of=[("name", "id", "description")],
        mutually_exclusive=[
            ('name', 'id'),
            ('id', 'description'),
            ('name', 'description'),
        ]
    )

    if not HAS_PACKET_SDK:
        module.fail_json(msg='packet required for this module')

    if not module.params.get('auth_token'):
        _fail_msg = ("if Packet API token is not in environment variable {0}, "
                     "the auth_token parameter is required".format(PACKET_API_TOKEN_ENV_VAR))
        module.fail_json(msg=_fail_msg)

    auth_token = module.params.get('auth_token')

    packet_conn = packet.Manager(auth_token=auth_token)

    state = module.params.get('state')

    if state in VOLUME_STATES:
        if module.check_mode:
            module.exit_json(changed=False)

        try:
            module.exit_json(**act_on_volume(state, module, packet_conn))
        except Exception as e:
            module.fail_json(
                msg="failed to set volume state {0}: {1}".format(
                    state, to_native(e)))
    else:
        module.fail_json(msg="{0} is not a valid state for this module".format(state))


if __name__ == '__main__':
    main()
