#!/usr/bin/python

# (c) 2016, NetApp, Inc
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
ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = """
---
module: netapp_e_snapshot_images
short_description: Create and delete snapshot images
description:
    - Create and delete snapshots images on snapshot groups for NetApp E-series storage arrays.
    - Only the oldest snapshot image can be deleted so consistency is preserved.
    - "Related: Snapshot volumes are created from snapshot images."
version_added: '2.2'
author: Kevin Hulquest (@hulquest)
extends_documentation_fragment:
    - netapp.eseries
options:
    snapshot_group:
        description:
            - The name of the snapshot group in which you want to create a snapshot image.
        required: True
    state:
        description:
            - Whether a new snapshot image should be created or oldest be deleted.
        required: True
        choices: ['create', 'remove']
"""
EXAMPLES = """
    - name: Create Snapshot
      netapp_e_snapshot_images:
        ssid: "{{ ssid }}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        validate_certs: "{{ validate_certs }}"
        snapshot_group: "3300000060080E5000299C24000005B656D9F394"
        state: 'create'
"""
RETURN = """
---
    changed: true
    msg: "Created snapshot image"
    image_id: "3400000060080E5000299B640063074057BC5C5E "
"""

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}
import json

from ansible.module_utils.api import basic_auth_argument_spec
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netapp import request
from ansible.module_utils.pycompat24 import get_exception


def snapshot_group_from_name(module, ssid, api_url, api_pwd, api_usr, name):
    snap_groups = 'storage-systems/%s/snapshot-groups' % ssid
    snap_groups_url = api_url + snap_groups
    (ret, snapshot_groups) = request(snap_groups_url, url_username=api_usr, url_password=api_pwd, headers=HEADERS,
                                     validate_certs=module.params['validate_certs'])

    snapshot_group_id = None
    for snapshot_group in snapshot_groups:
        if name == snapshot_group['label']:
            snapshot_group_id = snapshot_group['pitGroupRef']
            break
    if snapshot_group_id is None:
        module.fail_json(msg="Failed to lookup snapshot group.  Group [%s]. Id [%s]." % (name, ssid))

    return snapshot_group


def oldest_image(module, ssid, api_url, api_pwd, api_usr, name):
    get_status = 'storage-systems/%s/snapshot-images' % ssid
    url = api_url + get_status

    try:
        (ret, images) = request(url, url_username=api_usr, url_password=api_pwd, headers=HEADERS,
                                validate_certs=module.params['validate_certs'])
    except:
        err = get_exception()
        module.fail_json(msg="Failed to get snapshot images for group. Group [%s]. Id [%s]. Error [%s]" %
                             (name, ssid, str(err)))
    if not images:
        module.exit_json(msg="There are no snapshot images to remove.  Group [%s]. Id [%s]." % (name, ssid))

    oldest = min(images, key=lambda x: x['pitSequenceNumber'])
    if oldest is None or "pitRef" not in oldest:
        module.fail_json(msg="Failed to lookup oldest snapshot group.  Group [%s]. Id [%s]." % (name, ssid))

    return oldest


def create_image(module, ssid, api_url, pwd, user, p, snapshot_group):
    snapshot_group_obj = snapshot_group_from_name(module, ssid, api_url, pwd, user, snapshot_group)
    snapshot_group_id = snapshot_group_obj['pitGroupRef']
    endpoint = 'storage-systems/%s/snapshot-images' % ssid
    url = api_url + endpoint
    post_data = json.dumps({'groupId': snapshot_group_id})

    image_data = request(url, data=post_data, method='POST', url_username=user, url_password=pwd, headers=HEADERS,
                         validate_certs=module.params['validate_certs'])

    if image_data[1]['status'] == 'optimal':
        status = True
        id = image_data[1]['id']
    else:
        status = False
        id = ''

    return status, id


def delete_image(module, ssid, api_url, pwd, user, snapshot_group):
    image = oldest_image(module, ssid, api_url, pwd, user, snapshot_group)
    image_id = image['pitRef']
    endpoint = 'storage-systems/%s/snapshot-images/%s' % (ssid, image_id)
    url = api_url + endpoint

    try:
        (ret, image_data) = request(url, method='DELETE', url_username=user, url_password=pwd, headers=HEADERS,
                                    validate_certs=module.params['validate_certs'])
    except Exception:
        e = get_exception()
        image_data = (e[0], e[1])

    if ret == 204:
        deleted_status = True
        error_message = ''
    else:
        deleted_status = False
        error_message = image_data[1]['errorMessage']

    return deleted_status, error_message


def main():
    argument_spec = basic_auth_argument_spec()
    argument_spec.update(dict(
        snapshot_group=dict(required=True, type='str'),
        ssid=dict(required=True, type='str'),
        api_url=dict(required=True),
        api_username=dict(required=False),
        api_password=dict(required=False, no_log=True),
        validate_certs=dict(required=False, default=True),
        state=dict(required=True, choices=['create', 'remove'], type='str'),
    ))
    module = AnsibleModule(argument_spec)

    p = module.params

    ssid = p.pop('ssid')
    api_url = p.pop('api_url')
    user = p.pop('api_username')
    pwd = p.pop('api_password')
    snapshot_group = p.pop('snapshot_group')
    desired_state = p.pop('state')

    if not api_url.endswith('/'):
        api_url += '/'

    if desired_state == 'create':
        created_status, snapshot_id = create_image(module, ssid, api_url, pwd, user, p, snapshot_group)

        if created_status:
            module.exit_json(changed=True, msg='Created snapshot image', image_id=snapshot_id)
        else:
            module.fail_json(
                msg="Could not create snapshot image on system %s, in snapshot group %s" % (ssid, snapshot_group))
    else:
        deleted, error_msg = delete_image(module, ssid, api_url, pwd, user, snapshot_group)

        if deleted:
            module.exit_json(changed=True, msg='Deleted snapshot image for snapshot group [%s]' % (snapshot_group))
        else:
            module.fail_json(
                msg="Could not create snapshot image on system %s, in snapshot group %s --- %s" % (
                    ssid, snapshot_group, error_msg))


if __name__ == '__main__':
    main()
