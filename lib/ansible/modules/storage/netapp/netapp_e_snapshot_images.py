#!/usr/bin/python

# (c) 2016, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: netapp_e_snapshot_images
short_description: NetApp E-Series create and delete snapshot images
description:
    - Create and delete snapshots images on snapshot groups for NetApp E-series storage arrays.
    - Only the oldest snapshot image can be deleted so consistency is preserved.
    - "Related: Snapshot volumes are created from snapshot images."
version_added: '2.2'
author: Kevin Hulquest (@hulquest)
options:
    api_username:
        required: true
        description:
        - The username to authenticate with the SANtricity WebServices Proxy or embedded REST API.
    api_password:
        required: true
        description:
        - The password to authenticate with the SANtricity WebServices Proxy or embedded REST API.
    api_url:
        required: true
        description:
        - The url to the SANtricity WebServices Proxy or embedded REST API.
    validate_certs:
        required: false
        default: true
        description:
        - Should https certificates be validated?
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
    msg:
        description: State of operation
        type: str
        returned: always
        sample: "Created snapshot image"
    image_id:
        description: ID of snaphot image
        type: str
        returned: state == created
        sample: "3400000060080E5000299B640063074057BC5C5E "
"""

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}
import json

from ansible.module_utils.api import basic_auth_argument_spec
from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils._text import to_native
from ansible.module_utils.urls import open_url
from ansible.module_utils.six.moves.urllib.error import HTTPError


def request(url, data=None, headers=None, method='GET', use_proxy=True,
            force=False, last_mod_time=None, timeout=10, validate_certs=True,
            url_username=None, url_password=None, http_agent=None, force_basic_auth=True, ignore_errors=False):
    try:
        r = open_url(url=url, data=data, headers=headers, method=method, use_proxy=use_proxy,
                     force=force, last_mod_time=last_mod_time, timeout=timeout, validate_certs=validate_certs,
                     url_username=url_username, url_password=url_password, http_agent=http_agent,
                     force_basic_auth=force_basic_auth)
    except HTTPError as err:
        r = err.fp

    try:
        raw_data = r.read()
        if raw_data:
            data = json.loads(raw_data)
        else:
            raw_data = None
    except Exception:
        if ignore_errors:
            pass
        else:
            raise Exception(raw_data)

    resp_code = r.getcode()

    if resp_code >= 400 and not ignore_errors:
        raise Exception(resp_code, data)
    else:
        return resp_code, data


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
    except Exception as err:
        module.fail_json(msg="Failed to get snapshot images for group. Group [%s]. Id [%s]. Error [%s]" %
                             (name, ssid, to_native(err)))
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
    except Exception as e:
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
