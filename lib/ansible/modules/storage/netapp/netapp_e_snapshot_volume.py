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
module: netapp_e_snapshot_volume
short_description: NetApp E-Series manage snapshot volumes.
description:
    - Create, update, remove snapshot volumes for NetApp E/EF-Series storage arrays.
version_added: '2.2'
author: Kevin Hulquest (@hulquest)
notes:
  - Only I(full_threshold) is supported for update operations. If the snapshot volume already exists and the threshold matches, then an C(ok) status
    will be returned, no other changes can be made to a pre-existing snapshot volume.
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
        type: bool
    ssid:
      description:
          - storage array ID
      required: True
    snapshot_image_id:
      required: True
      description:
          - The identifier of the snapshot image used to create the new snapshot volume.
          - "Note: You'll likely want to use the M(netapp_e_facts) module to find the ID of the image you want."
    full_threshold:
      description:
          - The repository utilization warning threshold percentage
      default: 85
    name:
      required: True
      description:
          - The name you wish to give the snapshot volume
    view_mode:
      required: True
      description:
          - The snapshot volume access mode
      choices:
          - modeUnknown
          - readWrite
          - readOnly
          - __UNDEFINED
    repo_percentage:
      description:
          - The size of the view in relation to the size of the base volume
      default: 20
    storage_pool_name:
      description:
          - Name of the storage pool on which to allocate the repository volume.
      required: True
    state:
      description:
          - Whether to create or remove the snapshot volume
      required: True
      choices:
          - absent
          - present
"""
EXAMPLES = """
    - name: Snapshot volume
      netapp_e_snapshot_volume:
        ssid: "{{ ssid }}"
        api_url: "{{ netapp_api_url }}/"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        state: present
        storage_pool_name: "{{ snapshot_volume_storage_pool_name }}"
        snapshot_image_id: "{{ snapshot_volume_image_id }}"
        name: "{{ snapshot_volume_name }}"
"""
RETURN = """
msg:
    description: Success message
    returned: success
    type: str
    sample: Json facts for the volume that was created.
"""
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}
import json

from ansible.module_utils.api import basic_auth_argument_spec
from ansible.module_utils.basic import AnsibleModule

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


class SnapshotVolume(object):
    def __init__(self):
        argument_spec = basic_auth_argument_spec()
        argument_spec.update(dict(
            api_username=dict(type='str', required=True),
            api_password=dict(type='str', required=True, no_log=True),
            api_url=dict(type='str', required=True),
            ssid=dict(type='str', required=True),
            snapshot_image_id=dict(type='str', required=True),
            full_threshold=dict(type='int', default=85),
            name=dict(type='str', required=True),
            view_mode=dict(type='str', default='readOnly',
                           choices=['readOnly', 'readWrite', 'modeUnknown', '__Undefined']),
            repo_percentage=dict(type='int', default=20),
            storage_pool_name=dict(type='str', required=True),
            state=dict(type='str', required=True, choices=['absent', 'present'])
        ))

        self.module = AnsibleModule(argument_spec=argument_spec)
        args = self.module.params
        self.state = args['state']
        self.ssid = args['ssid']
        self.snapshot_image_id = args['snapshot_image_id']
        self.full_threshold = args['full_threshold']
        self.name = args['name']
        self.view_mode = args['view_mode']
        self.repo_percentage = args['repo_percentage']
        self.storage_pool_name = args['storage_pool_name']
        self.url = args['api_url']
        self.user = args['api_username']
        self.pwd = args['api_password']
        self.certs = args['validate_certs']

        if not self.url.endswith('/'):
            self.url += '/'

    @property
    def pool_id(self):
        pools = 'storage-systems/%s/storage-pools' % self.ssid
        url = self.url + pools
        (rc, data) = request(url, headers=HEADERS, url_username=self.user, url_password=self.pwd,
                             validate_certs=self.certs)

        for pool in data:
            if pool['name'] == self.storage_pool_name:
                self.pool_data = pool
                return pool['id']

        self.module.fail_json(msg="No storage pool with the name: '%s' was found" % self.name)

    @property
    def ss_vol_exists(self):
        rc, ss_vols = request(self.url + 'storage-systems/%s/snapshot-volumes' % self.ssid, headers=HEADERS,
                              url_username=self.user, url_password=self.pwd, validate_certs=self.certs)
        if ss_vols:
            for ss_vol in ss_vols:
                if ss_vol['name'] == self.name:
                    self.ss_vol = ss_vol
                    return True
        else:
            return False

        return False

    @property
    def ss_vol_needs_update(self):
        if self.ss_vol['fullWarnThreshold'] != self.full_threshold:
            return True
        else:
            return False

    def create_ss_vol(self):
        post_data = dict(
            snapshotImageId=self.snapshot_image_id,
            fullThreshold=self.full_threshold,
            name=self.name,
            viewMode=self.view_mode,
            repositoryPercentage=self.repo_percentage,
            repositoryPoolId=self.pool_id
        )

        rc, create_resp = request(self.url + 'storage-systems/%s/snapshot-volumes' % self.ssid,
                                  data=json.dumps(post_data), headers=HEADERS, url_username=self.user,
                                  url_password=self.pwd, validate_certs=self.certs, method='POST')

        self.ss_vol = create_resp
        # Doing a check after creation because the creation call fails to set the specified warning threshold
        if self.ss_vol_needs_update:
            self.update_ss_vol()
        else:
            self.module.exit_json(changed=True, **create_resp)

    def update_ss_vol(self):
        post_data = dict(
            fullThreshold=self.full_threshold,
        )

        rc, resp = request(self.url + 'storage-systems/%s/snapshot-volumes/%s' % (self.ssid, self.ss_vol['id']),
                           data=json.dumps(post_data), headers=HEADERS, url_username=self.user, url_password=self.pwd,
                           method='POST', validate_certs=self.certs)

        self.module.exit_json(changed=True, **resp)

    def remove_ss_vol(self):
        rc, resp = request(self.url + 'storage-systems/%s/snapshot-volumes/%s' % (self.ssid, self.ss_vol['id']),
                           headers=HEADERS, url_username=self.user, url_password=self.pwd, validate_certs=self.certs,
                           method='DELETE')
        self.module.exit_json(changed=True, msg="Volume successfully deleted")

    def apply(self):
        if self.state == 'present':
            if self.ss_vol_exists:
                if self.ss_vol_needs_update:
                    self.update_ss_vol()
                else:
                    self.module.exit_json(changed=False, **self.ss_vol)
            else:
                self.create_ss_vol()
        else:
            if self.ss_vol_exists:
                self.remove_ss_vol()
            else:
                self.module.exit_json(changed=False, msg="Volume already absent")


def main():
    sv = SnapshotVolume()
    sv.apply()


if __name__ == '__main__':
    main()
