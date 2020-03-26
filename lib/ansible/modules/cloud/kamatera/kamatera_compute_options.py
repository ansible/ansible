#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: kamatera_compute_options

short_description: Get Kamatera compute options

version_added: "2.9"

description:
    - "Get Kamatera compute options which can be used to create resources on the Kamatera cloud."
    - "Get an API client ID and secret from the Kamatera console at https://console.kamatera.com/"

options:
    api_client_id:
        description:
            - The Kamatera API Client ID, get it from the Kamatera console
            - Can be set via environment variable KAMATERA_API_CLIENT_ID
        required: true
        type: str
    api_secret:
        description:
            - The Kamatera API Secret, get it from the Kamatera console
            - Can be set via environment variable KAMATERA_API_SECRET
        required: true
        type: str
    api_url:
        description:
            - The Kamatera API URL (should not be changed from the default)
        default: 'https://cloudcli.cloudwm.com'
        type: str
    datacenter:
        description:
            - If not provided - will list available datacenters
            - If provided - will return the options for this datacenter
        type: 'str'
    wait_timeout_seconds:
        description:
            - How long to wait for each operation
        type: 'int'
        default: 600

author:
    - Ori Hoch (@OriHoch)
'''

EXAMPLES = '''
- name: Get capabilities
  hosts: localhost
  vars:
    api_client_id: <Your Kamatera API Client ID>
    api_secret: <Your Kamatera API secret>
  tasks:
    - name: list_datacenters
      kamatera_compute_options:
        api_client_id: '{{ api_client_id }}'
        api_secret: '{{ api_secret }}'
      register: response
    - name: print
      debug:
        msg: '{{ response.datacenters }}'
    - name: get_capabilities
      kamatera_compute_options:
        api_client_id: '{{ api_client_id }}'
        api_secret: '{{ api_secret }}'
        api_url: '{{ api_url }}'
        datacenter: US-NY2
      register: response
    - name: print
      debug:
        msg: ['{{ response.images }}','{{ response.capabilities }}']
'''

RETURN = '''
datacenters:
    description: List of datacenter objects (if called without datacenter param)
    returned: optional
    type: list
images:
    description: List of OS image objects available for the selected datacenter
    returned: optional
    type: list
capabilities:
    description: Object with the available capabilities for the selected datacenter
    returned: optional
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.kamatera import request


def list_datacenters(module):
    module.exit_json(changed=False, datacenters=request(module, 'service/server?datacenter=1'))


def get_capabilities(module, datacenter):
    module.exit_json(
        changed=False,
        images=request(module, 'service/server?images=1&datacenter=%s' % datacenter),
        capabilities=request(module, 'service/server?capabilities=1&datacenter=%s' % datacenter)
    )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            api_client_id=dict(required=True, fallback=(env_fallback, ['KAMATERA_API_CLIENT_ID']), no_log=True),
            api_secret=dict(required=True, fallback=(env_fallback, ['KAMATERA_API_SECRET']), no_log=True),
            api_url=dict(fallback=(env_fallback, ['KAMATERA_API_URL']), default='https://cloudcli.cloudwm.com'),
            datacenter=dict(type='str'),
            wait_timeout_seconds=dict(type='int', default=600),
        )
    )
    datacenter = module.params.get('datacenter')
    if datacenter:
        get_capabilities(module, datacenter)
    else:
        list_datacenters(module)


if __name__ == '__main__':
    main()
