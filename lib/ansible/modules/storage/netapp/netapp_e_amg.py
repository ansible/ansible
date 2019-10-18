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
module: netapp_e_amg
short_description: NetApp E-Series create, remove, and update asynchronous mirror groups
description:
    - Allows for the creation, removal and updating of Asynchronous Mirror Groups for NetApp E-series storage arrays
version_added: '2.2'
author: Kevin Hulquest (@hulquest)
extends_documentation_fragment:
    - netapp.eseries
options:
    name:
        description:
            - The name of the async array you wish to target, or create.
            - If C(state) is present and the name isn't found, it will attempt to create.
        required: yes
    secondaryArrayId:
        description:
            - The ID of the secondary array to be used in mirroring process
        required: yes
    syncIntervalMinutes:
        description:
            - The synchronization interval in minutes
        default: 10
    manualSync:
        description:
            - Setting this to true will cause other synchronization values to be ignored
        type: bool
        default: 'no'
    recoveryWarnThresholdMinutes:
        description:
            - Recovery point warning threshold (minutes). The user will be warned when the age of the last good failures point exceeds this value
        default: 20
    repoUtilizationWarnThreshold:
        description:
            - Recovery point warning threshold
        default: 80
    interfaceType:
        description:
            - The intended protocol to use if both Fibre and iSCSI are available.
        choices:
            - iscsi
            - fibre
    syncWarnThresholdMinutes:
        description:
            - The threshold (in minutes) for notifying the user that periodic synchronization has taken too long to complete.
        default: 10
    state:
        description:
            - A C(state) of present will either create or update the async mirror group.
            - A C(state) of absent will remove the async mirror group.
        choices: [ absent, present ]
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
    description: Successful creation
    returned: success
    type: str
    sample: '{"changed": true, "connectionType": "fc", "groupRef": "3700000060080E5000299C24000006E857AC7EEC", "groupState": "optimal", "id": "3700000060080E5000299C24000006E857AC7EEC", "label": "amg_made_by_ansible", "localRole": "primary", "mirrorChannelRemoteTarget": "9000000060080E5000299C24005B06E557AC7EEC", "orphanGroup": false, "recoveryPointAgeAlertThresholdMinutes": 20, "remoteRole": "secondary", "remoteTarget": {"nodeName": {"ioInterfaceType": "fc", "iscsiNodeName": null, "remoteNodeWWN": "20040080E5299F1C"}, "remoteRef": "9000000060080E5000299C24005B06E557AC7EEC", "scsiinitiatorTargetBaseProperties": {"ioInterfaceType": "fc", "iscsiinitiatorTargetBaseParameters": null}}, "remoteTargetId": "ansible2", "remoteTargetName": "Ansible2", "remoteTargetWwn": "60080E5000299F880000000056A25D56", "repositoryUtilizationWarnThreshold": 80, "roleChangeProgress": "none", "syncActivity": "idle", "syncCompletionTimeAlertThresholdMinutes": 10, "syncIntervalMinutes": 10, "worldWideName": "60080E5000299C24000006E857AC7EEC"}'
"""  # NOQA

import json
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.netapp import request, eseries_host_argument_spec


HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}


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
    except Exception as e:
        module.exit_json(msg="Error finding a match. Message: %s" % to_native(e), exception=traceback.format_exc())

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
    except Exception as e:
        module.exit_json(msg="Exception while creating aysnc mirror group. Message: %s" % to_native(e),
                         exception=traceback.format_exc())
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
    except Exception as e:
        module.exit_json(msg="Exception while updating async mirror group. Message: %s" % to_native(e),
                         exception=traceback.format_exc())

    return data


def remove_amg(module, ssid, api_url, pwd, user, async_id):
    endpoint = 'storage-systems/%s/async-mirrors/%s' % (ssid, async_id)
    url = api_url + endpoint
    try:
        rc, data = request(url, method='DELETE', url_username=user, url_password=pwd,
                           headers=HEADERS)
    except Exception as e:
        module.exit_json(msg="Exception while removing async mirror group. Message: %s" % to_native(e),
                         exception=traceback.format_exc())

    return


def main():
    argument_spec = eseries_host_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True, type='str'),
        new_name=dict(required=False, type='str'),
        secondaryArrayId=dict(required=True, type='str'),
        syncIntervalMinutes=dict(required=False, default=10, type='int'),
        manualSync=dict(required=False, default=False, type='bool'),
        recoveryWarnThresholdMinutes=dict(required=False, default=20, type='int'),
        repoUtilizationWarnThreshold=dict(required=False, default=80, type='int'),
        interfaceType=dict(required=False, choices=['fibre', 'iscsi'], type='str'),
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
