#!/usr/bin/python

# (c) 2016, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: netapp_e_snapshot_group
short_description: Manage snapshot groups
description:
    - Create, update, delete snapshot groups for NetApp E-series storage arrays
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
    state:
        description:
            - Whether to ensure the group is present or absent.
        required: True
        choices:
            - present
            - absent
    name:
        description:
            - The name to give the snapshot group
        required: True
    base_volume_name:
        description:
            - The name of the base volume or thin volume to use as the base for the new snapshot group.
            - If a snapshot group with an identical C(name) already exists but with a different base volume
              an error will be returned.
        required: True
    repo_pct:
        description:
            - The size of the repository in relation to the size of the base volume
        required: False
        default: 20
    warning_threshold:
        description:
            - The repository utilization warning threshold, as a percentage of the repository volume capacity.
        required: False
        default: 80
    delete_limit:
        description:
            - The automatic deletion indicator.
            - If non-zero, the oldest snapshot image will be automatically deleted when creating a new snapshot image to keep the total number of
              snapshot images limited to the number specified.
            - This value is overridden by the consistency group setting if this snapshot group is associated with a consistency group.
        required: False
        default: 30
    full_policy:
        description:
            - The behavior on when the data repository becomes full.
            - This value is overridden by consistency group setting if this snapshot group is associated with a consistency group
        required: False
        default: purgepit
        choices:
            - purgepit
            - unknown
            - failbasewrites
            - __UNDEFINED
    storage_pool_name:
        required: True
        description:
            - The name of the storage pool on which to allocate the repository volume.
    rollback_priority:
        required: False
        description:
            - The importance of the rollback operation.
            - This value is overridden by consistency group setting if this snapshot group is associated with a consistency group
        choices:
            - highest
            - high
            - medium
            - low
            - lowest
            - __UNDEFINED
        default: medium
"""

EXAMPLES = """
    - name: Configure Snapshot group
      netapp_e_snapshot_group:
        ssid: "{{ ssid }}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        validate_certs: "{{ netapp_api_validate_certs }}"
        base_volume_name: SSGroup_test
        name=: OOSS_Group
        repo_pct: 20
        warning_threshold: 85
        delete_limit: 30
        full_policy: purgepit
        storage_pool_name: Disk_Pool_1
        rollback_priority: medium
"""
RETURN = """
msg:
    description: Success message
    returned: success
    type: string
    sample: json facts for newly created snapshot group.
"""
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}
import json

from ansible.module_utils.api import basic_auth_argument_spec
from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.pycompat24 import get_exception
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
    except HTTPError:
        err = get_exception()
        r = err.fp

    try:
        raw_data = r.read()
        if raw_data:
            data = json.loads(raw_data)
        else:
            raw_data = None
    except:
        if ignore_errors:
            pass
        else:
            raise Exception(raw_data)

    resp_code = r.getcode()

    if resp_code >= 400 and not ignore_errors:
        raise Exception(resp_code, data)
    else:
        return resp_code, data


class SnapshotGroup(object):
    def __init__(self):

        argument_spec = basic_auth_argument_spec()
        argument_spec.update(
            api_username=dict(type='str', required=True),
            api_password=dict(type='str', required=True, no_log=True),
            api_url=dict(type='str', required=True),
            state=dict(required=True, choices=['present', 'absent']),
            base_volume_name=dict(required=True),
            name=dict(required=True),
            repo_pct=dict(default=20, type='int'),
            warning_threshold=dict(default=80, type='int'),
            delete_limit=dict(default=30, type='int'),
            full_policy=dict(default='purgepit', choices=['unknown', 'failbasewrites', 'purgepit']),
            rollback_priority=dict(default='medium', choices=['highest', 'high', 'medium', 'low', 'lowest']),
            storage_pool_name=dict(type='str'),
            ssid=dict(required=True),
        )

        self.module = AnsibleModule(argument_spec=argument_spec)

        self.post_data = dict()
        self.warning_threshold = self.module.params['warning_threshold']
        self.base_volume_name = self.module.params['base_volume_name']
        self.name = self.module.params['name']
        self.repo_pct = self.module.params['repo_pct']
        self.delete_limit = self.module.params['delete_limit']
        self.full_policy = self.module.params['full_policy']
        self.rollback_priority = self.module.params['rollback_priority']
        self.storage_pool_name = self.module.params['storage_pool_name']
        self.state = self.module.params['state']

        self.url = self.module.params['api_url']
        self.user = self.module.params['api_username']
        self.pwd = self.module.params['api_password']
        self.certs = self.module.params['validate_certs']
        self.ssid = self.module.params['ssid']

        if not self.url.endswith('/'):
            self.url += '/'

        self.changed = False

    @property
    def pool_id(self):
        pools = 'storage-systems/%s/storage-pools' % self.ssid
        url = self.url + pools
        try:
            (rc, data) = request(url, headers=HEADERS, url_username=self.user, url_password=self.pwd)
        except:
            err = get_exception()
            self.module.fail_json(msg="Snapshot group module - Failed to fetch storage pools. " +
                                      "Id [%s]. Error [%s]." % (self.ssid, str(err)))

        for pool in data:
            if pool['name'] == self.storage_pool_name:
                self.pool_data = pool
                return pool['id']

        self.module.fail_json(msg="No storage pool with the name: '%s' was found" % self.name)

    @property
    def volume_id(self):
        volumes = 'storage-systems/%s/volumes' % self.ssid
        url = self.url + volumes
        try:
            rc, data = request(url, headers=HEADERS, url_username=self.user, url_password=self.pwd,
                               validate_certs=self.certs)
        except:
            err = get_exception()
            self.module.fail_json(msg="Snapshot group module - Failed to fetch volumes. " +
                                      "Id [%s]. Error [%s]." % (self.ssid, str(err)))
        qty = 0
        for volume in data:
            if volume['name'] == self.base_volume_name:
                qty += 1

                if qty > 1:
                    self.module.fail_json(msg="More than one volume with the name: %s was found, "
                                              "please ensure your volume has a unique name" % self.base_volume_name)
                else:
                    Id = volume['id']
                    self.volume = volume

        try:
            return Id
        except NameError:
            self.module.fail_json(msg="No volume with the name: %s, was found" % self.base_volume_name)

    @property
    def snapshot_group_id(self):
        url = self.url + 'storage-systems/%s/snapshot-groups' % self.ssid
        try:
            rc, data = request(url, headers=HEADERS, url_username=self.user, url_password=self.pwd,
                               validate_certs=self.certs)
        except:
            err = get_exception()
            self.module.fail_json(msg="Failed to fetch snapshot groups. " +
                                      "Id [%s]. Error [%s]." % (self.ssid, str(err)))
        for ssg in data:
            if ssg['name'] == self.name:
                self.ssg_data = ssg
                return ssg['id']

        return None

    @property
    def ssg_needs_update(self):
        if self.ssg_data['fullWarnThreshold'] != self.warning_threshold or \
                self.ssg_data['autoDeleteLimit'] != self.delete_limit or \
                self.ssg_data['repFullPolicy'] != self.full_policy or \
                self.ssg_data['rollbackPriority'] != self.rollback_priority:
            return True
        else:
            return False

    def create_snapshot_group(self):
        self.post_data = dict(
            baseMappableObjectId=self.volume_id,
            name=self.name,
            repositoryPercentage=self.repo_pct,
            warningThreshold=self.warning_threshold,
            autoDeleteLimit=self.delete_limit,
            fullPolicy=self.full_policy,
            storagePoolId=self.pool_id,
        )
        snapshot = 'storage-systems/%s/snapshot-groups' % self.ssid
        url = self.url + snapshot
        try:
            rc, self.ssg_data = request(url, data=json.dumps(self.post_data), method='POST', headers=HEADERS,
                                        url_username=self.user, url_password=self.pwd, validate_certs=self.certs)
        except:
            err = get_exception()
            self.module.fail_json(msg="Failed to create snapshot group. " +
                                      "Snapshot group [%s]. Id [%s]. Error [%s]." % (self.name,
                                                                                     self.ssid,
                                                                                     str(err)))

        if not self.snapshot_group_id:
            self.snapshot_group_id = self.ssg_data['id']

        if self.ssg_needs_update:
            self.update_ssg()
        else:
            self.module.exit_json(changed=True, **self.ssg_data)

    def update_ssg(self):
        self.post_data = dict(
            warningThreshold=self.warning_threshold,
            autoDeleteLimit=self.delete_limit,
            fullPolicy=self.full_policy,
            rollbackPriority=self.rollback_priority
        )

        url = self.url + "storage-systems/%s/snapshot-groups/%s" % (self.ssid, self.snapshot_group_id)
        try:
            rc, self.ssg_data = request(url, data=json.dumps(self.post_data), method='POST', headers=HEADERS,
                                        url_username=self.user, url_password=self.pwd, validate_certs=self.certs)
        except:
            err = get_exception()
            self.module.fail_json(msg="Failed to update snapshot group. " +
                                      "Snapshot group [%s]. Id [%s]. Error [%s]." % (self.name,
                                                                                     self.ssid,
                                                                                     str(err)))

    def apply(self):
        if self.state == 'absent':
            if self.snapshot_group_id:
                try:
                    rc, resp = request(
                        self.url + 'storage-systems/%s/snapshot-groups/%s' % (self.ssid, self.snapshot_group_id),
                        method='DELETE', headers=HEADERS, url_password=self.pwd, url_username=self.user,
                        validate_certs=self.certs)
                except:
                    err = get_exception()
                    self.module.fail_json(msg="Failed to delete snapshot group. " +
                                              "Snapshot group [%s]. Id [%s]. Error [%s]." % (self.name,
                                                                                             self.ssid,
                                                                                             str(err)))
                self.module.exit_json(changed=True, msg="Snapshot group removed", **self.ssg_data)
            else:
                self.module.exit_json(changed=False, msg="Snapshot group absent")

        elif self.snapshot_group_id:
            if self.ssg_needs_update:
                self.update_ssg()
                self.module.exit_json(changed=True, **self.ssg_data)
            else:
                self.module.exit_json(changed=False, **self.ssg_data)
        else:
            self.create_snapshot_group()


def main():
    vg = SnapshotGroup()
    vg.apply()


if __name__ == '__main__':
    main()
