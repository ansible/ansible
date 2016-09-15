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
module: netapp_e_amg
short_description: Create, Remove, and Update Asynchronous Mirror Groups
description:
    - Allows for the creation, removal and updating of Asynchronous Mirror Groups for NetApp E-series storage arrays
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
    name:
        description:
            - The name of the async array you wish to target, or create.
            - If C(state) is present and the name isn't found, it will attempt to create.
        required: yes
    secondaryArrayId:
        description:
            - The ID of the secondary array to be used in mirroing process
        required: yes
    syncIntervalMinutes:
        description:
            - The synchronization interval in minutes
        required: no
        default: 10
    manualSync:
        description:
            - Setting this to true will cause other synchronization values to be ignored
        required: no
        default: no
    recoveryWarnThresholdMinutes:
        description:
            - Recovery point warning threshold (minutes). The user will be warned when the age of the last good failures point exceeds this value
        required: no
        default: 20
    repoUtilizationWarnThreshold:
        description:
            - Recovery point warning threshold
        required: no
        default: 80
    interfaceType:
        description:
            - The intended protocol to use if both Fibre and iSCSI are available.
        choices:
            - iscsi
            - fibre
        required: no
        default: null
    syncWarnThresholdMinutes:
        description:
            - The threshold (in minutes) for notifying the user that periodic synchronization has taken too long to complete.
        required: no
        default: 10
    ssid:
        description:
            - The ID of the primary storage array for the async mirror action
        required: yes
    state:
        description:
            - A C(state) of present will either create or update the async mirror group.
            - A C(state) of absent will remove the async mirror group.
        required: yes
"""

EXAMPLES = """
    - name: AMG removal
      na_eseries_amg:
        state: absent
        ssid: "{{ ssid }}"
        secondaryArrayId: "{{amg_secondaryArrayId}}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        new_name: "{{amg_array_name}}"
        name: "{{amg_name}}"
      when: amg_create

    - name: AMG create
      netapp_e_amg:
        state: present
        ssid: "{{ ssid }}"
        secondaryArrayId: "{{amg_secondaryArrayId}}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        new_name: "{{amg_array_name}}"
        name: "{{amg_name}}"
      when: amg_create
"""

RETURN = """
msg:
    description: Successful removal
    returned: success
    type: string
    sample: "Async mirror group removed."

msg:
    description: Successful creation
    returned: success
    type: string
    sample: '{"changed": true, "connectionType": "fc", "groupRef": "3700000060080E5000299C24000006E857AC7EEC", "groupState": "optimal", "id": "3700000060080E5000299C24000006E857AC7EEC", "label": "amg_made_by_ansible", "localRole": "primary", "mirrorChannelRemoteTarget": "9000000060080E5000299C24005B06E557AC7EEC", "orphanGroup": false, "recoveryPointAgeAlertThresholdMinutes": 20, "remoteRole": "secondary", "remoteTarget": {"nodeName": {"ioInterfaceType": "fc", "iscsiNodeName": null, "remoteNodeWWN": "20040080E5299F1C"}, "remoteRef": "9000000060080E5000299C24005B06E557AC7EEC", "scsiinitiatorTargetBaseProperties": {"ioInterfaceType": "fc", "iscsiinitiatorTargetBaseParameters": null}}, "remoteTargetId": "ansible2", "remoteTargetName": "Ansible2", "remoteTargetWwn": "60080E5000299F880000000056A25D56", "repositoryUtilizationWarnThreshold": 80, "roleChangeProgress": "none", "syncActivity": "idle", "syncCompletionTimeAlertThresholdMinutes": 10, "syncIntervalMinutes": 10, "worldWideName": "60080E5000299C24000006E857AC7EEC"}'
"""

import json

from ansible.module_utils.api import basic_auth_argument_spec
from ansible.module_utils.basic import AnsibleModule, get_exception
from ansible.module_utils.urls import open_url
from ansible.module_utils.six.moves.urllib.error import HTTPError

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def request(url, data=None, headers=None, method='GET', use_proxy=True,
            force=False, last_mod_time=None, timeout=10, validate_certs=True,
            url_username=None, url_password=None, http_agent=None, force_basic_auth=False, ignore_errors=False):
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
            data = None
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


def has_match(module, ssid, api_url, api_pwd, api_usr, body):
    compare_keys = ['syncIntervalMinutes', 'syncWarnThresholdMinutes',
                    'recoveryWarnThresholdMinutes', 'repoUtilizationWarnThreshold']
    desired_state = dict((x, (body.get(x))) for x in compare_keys)
    label_exists = False
    matches_spec = False
    current_state = None
    async_id = None
    api_data = None
    desired_name = body.get('name')
    endpoint = 'storage-systems/%s/async-mirrors' % ssid
    url = api_url + endpoint
    try:
        rc, data = request(url, url_username=api_usr, url_password=api_pwd, headers=HEADERS)
    except Exception:
        error = get_exception()
        module.exit_json(exception="Error finding a match. Message: %s" % str(error))

    for async_group in data:
        if async_group['label'] == desired_name:
            label_exists = True
            api_data = async_group
            async_id = async_group['groupRef']
            current_state = dict(
                syncIntervalMinutes=async_group['syncIntervalMinutes'],
                syncWarnThresholdMinutes=async_group['syncCompletionTimeAlertThresholdMinutes'],
                recoveryWarnThresholdMinutes=async_group['recoveryPointAgeAlertThresholdMinutes'],
                repoUtilizationWarnThreshold=async_group['repositoryUtilizationWarnThreshold'],
            )

    if current_state == desired_state:
        matches_spec = True

    return label_exists, matches_spec, api_data, async_id


def create_async(module, ssid, api_url, api_pwd, api_usr, body):
    endpoint = 'storage-systems/%s/async-mirrors' % ssid
    url = api_url + endpoint
    post_data = json.dumps(body)
    try:
        rc, data = request(url, data=post_data, method='POST', url_username=api_usr, url_password=api_pwd,
                           headers=HEADERS)
    except Exception:
        error = get_exception()
        module.exit_json(exception="Exception while creating aysnc mirror group. Message: %s" % str(error))
    return data


def update_async(module, ssid, api_url, pwd, user, body, new_name, async_id):
    endpoint = 'storage-systems/%s/async-mirrors/%s' % (ssid, async_id)
    url = api_url + endpoint
    compare_keys = ['syncIntervalMinutes', 'syncWarnThresholdMinutes',
                    'recoveryWarnThresholdMinutes', 'repoUtilizationWarnThreshold']
    desired_state = dict((x, (body.get(x))) for x in compare_keys)

    if new_name:
        desired_state['new_name'] = new_name

    post_data = json.dumps(desired_state)

    try:
        rc, data = request(url, data=post_data, method='POST', headers=HEADERS,
                           url_username=user, url_password=pwd)
    except Exception:
        error = get_exception()
        module.exit_json(exception="Exception while updating async mirror group. Message: %s" % str(error))

    return data


def remove_amg(module, ssid, api_url, pwd, user, async_id):
    endpoint = 'storage-systems/%s/async-mirrors/%s' % (ssid, async_id)
    url = api_url + endpoint
    try:
        rc, data = request(url, method='DELETE', url_username=user, url_password=pwd,
                           headers=HEADERS)
    except Exception:
        error = get_exception()
        module.exit_json(exception="Exception while removing async mirror group. Message: %s" % str(error))

    return


def main():
    argument_spec = basic_auth_argument_spec()
    argument_spec.update(dict(
        api_username=dict(type='str', required=True),
        api_password=dict(type='str', required=True, no_log=True),
        api_url=dict(type='str', required=True),
        name=dict(required=True, type='str'),
        new_name=dict(required=False, type='str'),
        secondaryArrayId=dict(required=True, type='str'),
        syncIntervalMinutes=dict(required=False, default=10, type='int'),
        manualSync=dict(required=False, default=False, type='bool'),
        recoveryWarnThresholdMinutes=dict(required=False, default=20, type='int'),
        repoUtilizationWarnThreshold=dict(required=False, default=80, type='int'),
        interfaceType=dict(required=False, choices=['fibre', 'iscsi'], type='str'),
        ssid=dict(required=True, type='str'),
        state=dict(required=True, choices=['present', 'absent']),
        syncWarnThresholdMinutes=dict(required=False, default=10, type='int')
    ))

    module = AnsibleModule(argument_spec=argument_spec)

    p = module.params

    ssid = p.pop('ssid')
    api_url = p.pop('api_url')
    user = p.pop('api_username')
    pwd = p.pop('api_password')
    new_name = p.pop('new_name')
    state = p.pop('state')

    if not api_url.endswith('/'):
        api_url += '/'

    name_exists, spec_matches, api_data, async_id = has_match(module, ssid, api_url, pwd, user, p)

    if state == 'present':
        if name_exists and spec_matches:
            module.exit_json(changed=False, msg="Desired state met", **api_data)
        elif name_exists and not spec_matches:
            results = update_async(module, ssid, api_url, pwd, user,
                                   p, new_name, async_id)
            module.exit_json(changed=True,
                             msg="Async mirror group updated", async_id=async_id,
                             **results)
        elif not name_exists:
            results = create_async(module, ssid, api_url, user, pwd, p)
            module.exit_json(changed=True, **results)

    elif state == 'absent':
        if name_exists:
            remove_amg(module, ssid, api_url, pwd, user, async_id)
            module.exit_json(changed=True, msg="Async mirror group removed.",
                             async_id=async_id)
        else:
            module.exit_json(changed=False,
                             msg="Async Mirror group: %s already absent" % p['name'])


if __name__ == '__main__':
    main()
