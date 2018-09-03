#!/usr/bin/env python
# encoding: utf-8

DEFAULT_TTL = 86400
DEFAULT_PRIORITY = 0
DEFAULT_ENDPOINT = 'https://api.online.net'

import requests
from ansible.module_utils.basic import *
import json

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'domain-team@online.net'
}

DOCUMENTATION = '''
---
module: online-domain

short_description: This is a little ansible module to update online dns zone

version_added: "0.1"

description:
    - "This is a little ansible module to update online dns zone"

options:
  token:
    description:
    - This is the api's token of Online account
    required: true

    zone:
        description:
            - This is the zone requested
        required: true

    action:
      description:
      - This is action requested (list,delete)
      required: true

    endpoint:
      description:
      - This is the endpoint to use, will allow use of sandbox api
      required: false

extends_documentation_fragment

author:
    - domain-team@online.net
'''

EXAMPLES = '''
# To list the contents of a zone
```yaml
- name: list contents of example.com
    domain_online_zone:
      token: "ZETZEGERHG35ERHGERHERSDGDSGS"
      zone: "example.com"
      action: "list"
```

# To clear a zone to restart from scratch
```yaml
- name: list contents of example.com
    domain_online_zone:
      token: "ZETZEGERHG35ERHGERHERSDGDSGS"
      zone: "example.com"
      action: "reset"
```
'''

RETURN = '''
meta:
    status: The http code returned by the api
    data: The json error message
zone:
    the zone name requested
contents:
    array of zone's records
'''


def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        action=dict(choices=['list', 'reset'], required=True),
        endpoint=dict(type='str', required=False, default=DEFAULT_ENDPOINT),
        token=dict(type='str', required=True),
        zone=dict(type='str', required=True),
    )

    result = {}

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        return result

    if module.params['endpoint'] == '':
        module.params['endpoint'] = DEFAULT_ENDPOINT

    result['original_message'] = module.params['action'] + ' ' + module.params['zone']
    result['message'] = 'working'

    headers = {
        "Authorization": "Bearer " + module.params['token']
    }

    url = "{}{}{}{}".format(module.params['endpoint'], '/api/v1/domain/', module.params['zone'], '/version/active')

    changed = False

    if module.params['action'] == 'reset':
        result = requests.delete(url, headers=headers)
        if result.status_code != 204:
            # if error
            module.fail_json(msg='Your request failed', meta={"status": result.status_code, "data": result.json()})
        else:
            changed = True

    contents = []
    if module.params['action'] == 'list':
        result = requests.get(url, headers=headers)
        if result.status_code != 200:
            # if error
            module.fail_json(msg='Your request failed', meta={"status": result.status_code, "data": result.json()})
        else:
            zones = result.json()['zone']
            for z in zones.keys():

                if z != '$ref':
                    zone = {
                        "name": zones[z]['name'],
                        "ttl": zones[z]['ttl'],
                        "type": zones[z]['type'],
                        "content": zones[z]['data'],
                    }

                    if zone['type'] == 'MX':
                        zone['priority'] = zones[z]['aux']

                    contents.append(
                        zone
                    )

    module.exit_json(changed=changed, meta={"status": result.status_code}, zone=module.params['zone'],
                     contents=contents)


def main():
    run_module()


if __name__ == '__main__':
    main()
