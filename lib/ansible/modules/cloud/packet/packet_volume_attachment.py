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
module: packet_volume_attachment

short_description: Attach/detach a volume to a device in the Packet host.

description:
     - Attach/detach a volume to a device in the Packet host.
     - API is documented at U(https://www.packet.com/developers/api/volumes/).
     - "This module creates the attachment route in the Packet API. In order to discover
       the block devices on the server, you have to run the Attach Scripts,
       as documented at U(https://help.packet.net/technical/storage/packet-block-storage-linux)."

version_added: "2.10"

author:
    - Tomas Karasek (@t0mk) <tom.to.the.k@gmail.com>
    - Nurfet Becirevic (@nurfet-becirevic) <nurfet.becirevic@gmail.com>

options:
  state:
    description:
      - Indicate desired state of the attachment.
    default: present
    choices: ['present', 'absent']
    type: str

  auth_token:
    description:
      - Packet api token. You can also supply it in env var C(PACKET_API_TOKEN).
    type: str

  project_id:
    description:
      - UUID of the project to which the device and volume belong.
    type: str

  volume:
    description:
      - Selector for the volume.
      - It can be a UUID, an API-generated volume name, or user-defined description string.
      - 'Example values: 4a347482-b546-4f67-8300-fb5018ef0c5, volume-4a347482, "my volume"'
    type: str

  device:
    description:
      - Selector for the device.
      - It can be a UUID of the device, or a hostname.
      - 'Example values: 98a14f7a-3d27-4478-b7cf-35b5670523f3, "my device"'
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
    volname: testvol
    devname: testdev
    project_id: 52000fb2-ee46-4673-93a8-de2c2bdba33b

  tasks:
    - name: test create volume
      packet_volume:
        description: "{{ volname }}"
        project_id: "{{ project_id }}"
        facility: ewr1
        plan: storage_1
        state: present
        size: 10
        snapshot_policy:
          snapshot_count: 10
          snapshot_frequency: 1day

    - packet_device:
        project_id: "{{ project_id }}"
        hostnames: "{{ devname }}"
        operating_system: ubuntu_16_04
        plan: baremetal_0
        facility: ewr1
        state: present

    - name: Attach testvol to testdev
      packet_volume_attachment:
        project_id: "{{ project_id }}"
        volume: "{{ volname }}"
        device: "{{ devname }}"

    - name: Detach testvol from testdev
      packet_volume_attachment:
        project_id: "{{ project_id }}"
        volume: "{{ volname }}"
        device: "{{ devname }}"
        state: absent

'''

RETURN = '''
volume_id:
    description: UUID of volume addressed by the module call.
    type: str
    returned: success

device_id:
    description: UUID of device addressed by the module call.
    type: str
    returned: success
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

STATES = ["present", "absent"]


def is_valid_uuid(myuuid):
    try:
        val = uuid.UUID(myuuid, version=4)
    except ValueError:
        return False
    return str(val) == myuuid


def get_volume_selector(spec):
    if is_valid_uuid(spec):
        return lambda v: v['id'] == spec
    else:
        return lambda v: v['name'] == spec or v['description'] == spec


def get_device_selector(spec):
    if is_valid_uuid(spec):
        return lambda v: v['id'] == spec
    else:
        return lambda v: v['hostname'] == spec


def do_attach(packet_conn, vol_id, dev_id):
    api_method = "storage/{0}/attachments".format(vol_id)
    packet_conn.call_api(
        api_method,
        params={"device_id": dev_id},
        type="POST")


def do_detach(packet_conn, vol, dev_id=None):
    def dev_match(a):
        return (dev_id is None) or (a['device']['id'] == dev_id)
    for a in vol['attachments']:
        if dev_match(a):
            print(a['href'])
            packet_conn.call_api(a['href'], type="DELETE")


def validate_selected(l, resource_type, spec):
    if len(l) > 1:
        _msg = ("more than one {0} matches specification {1}: {2}".format(
                resource_type, spec, l))
        raise Exception(_msg)
    if len(l) == 0:
        _msg = "no {0} matches specification: {1}".format(resource_type, spec)
        raise Exception(_msg)


def get_attached_dev_ids(volume_dict):
    if len(volume_dict['attachments']) == 0:
        return []
    else:
        return [a['device']['id'] for a in volume_dict['attachments']]


def act_on_volume_attachment(target_state, module, packet_conn):
    return_dict = {'changed': False}
    volspec = module.params.get("volume")
    devspec = module.params.get("device")
    if devspec is None and target_state == 'present':
        raise Exception("If you want to attach a volume, you must specify a device.")
    project_id = module.params.get("project_id")
    volumes_api_method = "projects/{0}/storage".format(project_id)
    volumes = packet_conn.call_api(volumes_api_method,
                                   params={'include': 'facility,attachments.device'})['volumes']
    v_match = get_volume_selector(volspec)
    matching_volumes = [v for v in volumes if v_match(v)]
    validate_selected(matching_volumes, "volume", volspec)
    volume = matching_volumes[0]
    return_dict['volume_id'] = volume['id']

    device = None
    if devspec is not None:
        devices_api_method = "projects/{0}/devices".format(project_id)
        devices = packet_conn.call_api(devices_api_method)['devices']
        d_match = get_device_selector(devspec)
        matching_devices = [d for d in devices if d_match(d)]
        validate_selected(matching_devices, "device", devspec)
        device = matching_devices[0]
        return_dict['device_id'] = device['id']

    attached_device_ids = get_attached_dev_ids(volume)

    if target_state == "present":
        if len(attached_device_ids) == 0:
            do_attach(packet_conn, volume['id'], device['id'])
            return_dict['changed'] = True
        elif device['id'] not in attached_device_ids:
            # Don't reattach volume which is attached to a different device.
            # Rather fail than force remove a device on state == 'present'.
            raise Exception("volume {0} is already attached to device {1}".format(
                            volume, attached_device_ids))
    else:
        if device is None:
            if len(attached_device_ids) > 0:
                do_detach(packet_conn, volume)
                return_dict['changed'] = True
        elif device['id'] in attached_device_ids:
            do_detach(packet_conn, volume, device['id'])
            return_dict['changed'] = True

    return return_dict


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(choices=STATES, default="present"),
            auth_token=dict(
                type='str',
                fallback=(env_fallback, [PACKET_API_TOKEN_ENV_VAR]),
                no_log=True
            ),
            volume=dict(type="str", required=True),
            project_id=dict(type="str", required=True),
            device=dict(type="str"),
        ),
        supports_check_mode=True,
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

    if state in STATES:
        if module.check_mode:
            module.exit_json(changed=False)

        try:
            module.exit_json(
                **act_on_volume_attachment(state, module, packet_conn))
        except Exception as e:
            module.fail_json(
                msg="failed to set volume_attachment state {0}: {1}".format(state, to_native(e)))
    else:
        module.fail_json(msg="{0} is not a valid state for this module".format(state))


if __name__ == '__main__':
    main()
