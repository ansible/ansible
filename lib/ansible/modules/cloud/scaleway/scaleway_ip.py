#!/usr/bin/python
#
# Scaleway ip management module
#
# Copyright (C) 2018 Antoine Barbare (antoinebarbare@gmail.com).
#
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: scaleway_ip
short_description: Scaleway ip management module
version_added: "2.7"
author: Antoine Barbare (@_abarbare)
description:
    - This module manages ips on Scaleway account
      U(https://developer.scaleway.com)

options:
  server_id:
    description:
    - Scaleway Compute instance ID of the server
    required: true
  state:
    description:
     - Indicate desired state of the ip.
    required: true
    choices:
      - present
      - absent
  oauth_token:
    description:
     - Scaleway OAuth token.
    required: true
  region:
    description:
     - Scaleway region to use (for example par1).
    required: true
    choices:
      - ams1
      - EMEA-NL-EVS
      - par1
      - EMEA-FR-PAR1
  organization:
    description:
     - ScaleWay organization ID to which ip belongs.
  timeout:
    description:
    - Timeout for API calls
    default: 30
'''

EXAMPLES = '''
  - name: Create a public IPv4 address
    scaleway_ip:
      server_id: '1f7751cf-5a49-4ba1-9ade-cc4cb5d7d2b0'
      state: present
      region: par1
      organization: "{{ scw_org }}"
    register: server_creation_check_task

  - name: Make sure public IPv4 deleted
    scaleway_ip:
      server_id: '1f7751cf-5a49-4ba1-9ade-cc4cb5d7d2b0'
      state: absent
      region: par1

'''

RETURN = '''
data:
    description: This is only present when C(state=present)
    returned: when C(state=present)
    type: dict
    sample: {
      "ip": {
        "organization": "eea95185-710a-4916-991a-4e1fd4b0a3688",
        "reverse": null,
        "id": "cc45f92b-4a0a-4857-baa6-76129f795a98",
        "server": {
            "id": "1f7751cf-5a49-4ba1-9ade-cc4cb5d7d2b0",
            "name": "scw-440740"
        },
        "address": "51.15.232.254"
    }
}
'''

from ansible.module_utils.scaleway import ScalewayAPI, SCALEWAY_LOCATION
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.scaleway import ScalewayAPI


def delete_ip_address(compute_api, ip_id):
    response = compute_api.delete('/ips/%s' % ip_id)

    if not response.ok:
        msg = 'Error during IP address deleting: (%s) %s' % response.status_code, response.body
        compute_api.module.fail_json(msg=msg)

    return response


def patch_ip_address(compute_api, server_id, ip_id):
    payload = {'server': server_id}
    response = compute_api.patch('/ips/%s' % ip_id, payload)

    if not response.ok:
        msg = 'Error attaching ip address: (%s) %s' % (
            response.status_code, response.body)
        compute_api.module.fail_json(msg=msg)

    return response.json


def post_ip_address(compute_api, organization):
    payload = {'organization': organization}
    response = compute_api.post('/ips', payload)

    if not response.ok:
        msg = 'Error during ip reservation: (%s) %s' % (
            response.status_code, response.body)
        compute_api.module.fail_json(msg=msg)

    return response.json


def get_server_info(compute_api, server_id):
    compute_api.module.debug('Get server details')
    response = compute_api.get('servers/%s' % server_id)

    if not response.ok:
        msg = 'Error during server information processing: (%s) %s' % (
            response.status_code, response.body)
        compute_api.module.fail_json(msg=msg)

    return response.json['server']


def core(module):
    api_token = module.params['oauth_token']
    region = module.params['region']
    state = module.params['state']
    organization = module.params['organization']
    server_id = module.params['server_id']

    compute_api = ScalewayAPI(
        module,
        headers={
            'X-Auth-Token': api_token},
        base_url=SCALEWAY_LOCATION[region]['api_endpoint'])

    response = compute_api.get('ips')
    status_code = response.status_code

    if not response.ok:
        module.fail_json(msg='Error getting ip [{0}: {1}]'.format(
            status_code, response.json['message']))

    server_info = get_server_info(compute_api, server_id)

    if state in ('present',):
        if server_info['public_ip'] and not server_info['public_ip']['dynamic']:
            module.exit_json(changed=False)

        if module.check_mode:
            module.exit_json(changed=True)

        ip = post_ip_address(compute_api, organization)
        patch_ip_address(compute_api, server_id, ip['ip']['id'])
        module.exit_json(changed=True, data=ip)

    elif state in ('absent',):
        if not server_info['public_ip'] or server_info['public_ip']['dynamic']:
            module.exit_json(changed=False)

        if module.check_mode:
            module.exit_json(changed=True)

        response = delete_ip_address(
            compute_api, server_info['public_ip']['id'])
        module.exit_json(changed=True, data=response.json)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            oauth_token=dict(
                no_log=True,
                # Support environment variable for Scaleway OAuth Token
                fallback=(
                    env_fallback, [
                        'SCW_TOKEN', 'SCW_API_KEY', 'SCW_OAUTH_TOKEN']),
                required=True,
            ),
            state=dict(choices=['present', 'absent'], required=True),
            organization=dict(required=True),
            server_id=dict(required=True),
            timeout=dict(type='int', default=30),
            region=dict(required=True, choices=SCALEWAY_LOCATION.keys()),
        ),
        supports_check_mode=True,
    )

    core(module)


if __name__ == '__main__':
    main()
