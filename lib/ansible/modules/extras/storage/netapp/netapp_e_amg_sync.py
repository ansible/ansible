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
DOCUMENTATION = """
---
module: netapp_e_amg_sync
short_description: Conduct synchronization actions on asynchronous member groups.
description:
    - Allows for the initialization, suspension and resumption of an asynchronous mirror group's synchronization for NetApp E-series storage arrays.
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
        example:
        - https://prod-1.wahoo.acme.com/devmgr/v2
    validate_certs:
        required: false
        default: true
        description:
        - Should https certificates be validated?
    ssid:
        description:
            - The ID of the storage array containing the AMG you wish to target
    name:
        description:
            - The name of the async mirror group you wish to target
        required: yes
    state:
        description:
            - The synchronization action you'd like to take.
            - If C(running) then it will begin syncing if there is no active sync or will resume a suspended sync. If there is already a sync in progress, it will return with an OK status.
            - If C(suspended) it will suspend any ongoing sync action, but return OK if there is no active sync or if the sync is already suspended
        choices:
            - running
            - suspended
        required: yes
    delete_recovery_point:
        description:
            - Indicates whether the failures point can be deleted on the secondary if necessary to achieve the synchronization.
            - If true, and if the amount of unsynchronized data exceeds the CoW repository capacity on the secondary for any member volume, the last failures point will be deleted and synchronization will continue.
            - If false, the synchronization will be suspended if the amount of unsynchronized data exceeds the CoW Repository capacity on the secondary and the failures point will be preserved.
            - "NOTE: This only has impact for newly launched syncs."
        choices:
            - yes
            - no
        default: no
"""
EXAMPLES = """
    - name: start AMG async
      netapp_e_amg_sync:
        name: "{{ amg_sync_name }}"
        state: running
        ssid: "{{ ssid }}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
"""
RETURN = """
json:
    description: The object attributes of the AMG.
    returned: success
    type: string
    example:
        {
            "changed": false,
            "connectionType": "fc",
            "groupRef": "3700000060080E5000299C24000006EF57ACAC70",
            "groupState": "optimal",
            "id": "3700000060080E5000299C24000006EF57ACAC70",
            "label": "made_with_ansible",
            "localRole": "primary",
            "mirrorChannelRemoteTarget": "9000000060080E5000299C24005B06E557AC7EEC",
            "orphanGroup": false,
            "recoveryPointAgeAlertThresholdMinutes": 20,
            "remoteRole": "secondary",
            "remoteTarget": {
                "nodeName": {
                    "ioInterfaceType": "fc",
                    "iscsiNodeName": null,
                    "remoteNodeWWN": "20040080E5299F1C"
                },
                "remoteRef": "9000000060080E5000299C24005B06E557AC7EEC",
                "scsiinitiatorTargetBaseProperties": {
                    "ioInterfaceType": "fc",
                    "iscsiinitiatorTargetBaseParameters": null
                }
            },
            "remoteTargetId": "ansible2",
            "remoteTargetName": "Ansible2",
            "remoteTargetWwn": "60080E5000299F880000000056A25D56",
            "repositoryUtilizationWarnThreshold": 80,
            "roleChangeProgress": "none",
            "syncActivity": "idle",
            "syncCompletionTimeAlertThresholdMinutes": 10,
            "syncIntervalMinutes": 10,
            "worldWideName": "60080E5000299C24000006EF57ACAC70"
    }
"""
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


class AMGsync(object):
    def __init__(self):
        argument_spec = basic_auth_argument_spec()
        argument_spec.update(dict(
            api_username=dict(type='str', required=True),
            api_password=dict(type='str', required=True, no_log=True),
            api_url=dict(type='str', required=True),
            name=dict(required=True, type='str'),
            ssid=dict(required=True, type='str'),
            state=dict(required=True, type='str', choices=['running', 'suspended']),
            delete_recovery_point=dict(required=False, type='bool', default=False)
        ))
        self.module = AnsibleModule(argument_spec=argument_spec)
        args = self.module.params
        self.name = args['name']
        self.ssid = args['ssid']
        self.state = args['state']
        self.delete_recovery_point = args['delete_recovery_point']
        try:
            self.user = args['api_username']
            self.pwd = args['api_password']
            self.url = args['api_url']
        except KeyError:
            self.module.fail_json(msg="You must pass in api_username"
                                      "and api_password and api_url to the module.")
        self.certs = args['validate_certs']

        self.post_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self.amg_id, self.amg_obj = self.get_amg()

    def get_amg(self):
        endpoint = self.url + '/storage-systems/%s/async-mirrors' % self.ssid
        (rc, amg_objs) = request(endpoint, url_username=self.user, url_password=self.pwd, validate_certs=self.certs,
                                 headers=self.post_headers)
        try:
            amg_id = filter(lambda d: d['label'] == self.name, amg_objs)[0]['id']
            amg_obj = filter(lambda d: d['label'] == self.name, amg_objs)[0]
        except IndexError:
            self.module.fail_json(
                msg="There is no async mirror group  %s associated with storage array %s" % (self.name, self.ssid))
        return amg_id, amg_obj

    @property
    def current_state(self):
        amg_id, amg_obj = self.get_amg()
        return amg_obj['syncActivity']

    def run_sync_action(self):
        # If we get to this point we know that the states differ, and there is no 'err' state,
        # so no need to revalidate

        post_body = dict()
        if self.state == 'running':
            if self.current_state == 'idle':
                if self.delete_recovery_point:
                    post_body.update(dict(deleteRecoveryPointIfNecessary=self.delete_recovery_point))
                suffix = 'sync'
            else:
                # In a suspended state
                suffix = 'resume'
        else:
            suffix = 'suspend'

        endpoint = self.url + "/storage-systems/%s/async-mirrors/%s/%s" % (self.ssid, self.amg_id, suffix)

        (rc, resp) = request(endpoint, method='POST', url_username=self.user, url_password=self.pwd,
                             validate_certs=self.certs, data=json.dumps(post_body), headers=self.post_headers,
                             ignore_errors=True)

        if not str(rc).startswith('2'):
            self.module.fail_json(msg=str(resp['errorMessage']))

        return resp

    def apply(self):
        state_map = dict(
            running=['active'],
            suspended=['userSuspended', 'internallySuspended', 'paused'],
            err=['unkown', '_UNDEFINED'])

        if self.current_state not in state_map[self.state]:
            if self.current_state in state_map['err']:
                self.module.fail_json(
                    msg="The sync is a state of '%s', this requires manual intervention. " +
                        "Please investigate and try again" % self.current_state)
            else:
                self.amg_obj = self.run_sync_action()

        (ret, amg) = self.get_amg()
        self.module.exit_json(changed=False, **amg)


def main():
    sync = AMGsync()
    sync.apply()


if __name__ == '__main__':
    main()
