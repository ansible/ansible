#!/usr/bin/env python
# encoding: utf-8


ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': '#domain'
}

DOCUMENTATION = '''
---
module: online_domain_record
description:
    - Online DNS record management module
options:

  zone:
    description:
    - This is the zone requested
    required: true

  name:
    description:
    - This is the name of the record to update
    required: true

  type:
    description:
    - This is the type of the record to update
    choices:
      - A
      - AAAA
      - MX
      - CNAME
      - TXT
      - SRV
    required: true

  state:
    description:
    - This is state requested
    choice:
      - present
      - absent
    required: true

  content:
    description:
    - This is content requested
    required: false

  unique:
    description:
    - This allows or not multiple contents on same name
    required: false
    default: false

  priority:
    description:
    - This is priority requested (for MX)
    required: true

  endpoint:
    description:
    - This is the endpoint to use, will allow use of sandbox api
    required: false

extends_documentation_fragment: online

author:
  - domain-team@online.net
  - rleone@scaleway.com
'''

EXAMPLES = '''
# Ensure A record

- online_domain_record:
    name: host01.example.com.
    type: A
    content: 192.168.1.234
    ttl: 1440
    state: present
    unique: true

# Ensure AAAA record

- online_domain_record:
    name: host01.example.com.
    type: AAAA
    content: 2001:cdba:0000:0000:0000:0000:3257:9652
    ttl: 1440
    state: present
    unique: true

# Ensure CNAME record

- online_domain_record:
    name: database.example.com.
    type: CNAME
    content: host01.zone01.internal.example.com
    state: present

# Ensure record is absent

- online_domain_record:
    name: database.example.com.
    type: CNAME
    state: absent

# Ensure record is absent with filter on content

- online_domain_record:
    name: database.example.com.
    type: A
    content: 192.168.1.234
    state: absent

# update a record with unique content
- online_domain_record:
    name: host01
    zone: example.com
    type: A
    content: 192.168.1.234
    ttl: 1440
    state: present
    unique: true

# update a record with multiple contents

- online_domain_record:
    name: host01
    zone: example.com
    type: A
    content: 192.168.1.234
    ttl: 1440
    state: present

- online_domain_record:
    name: host01
    zone: example.com
    type: A
    content: 192.168.1.235
    ttl: 1440
    state: present

# delete all record with same name and type
- online_domain_record:
    name: host01
    zone: example.com
    type: A
    state: absent
'''

DEFAULT_TTL = 86400
DEFAULT_PRIORITY = 0

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.online import online_argument_spec
from ansible.module_utils.urls import Request


def main():
    argument_spec = online_argument_spec()
    argument_spec.update(dict(
        token=dict(required=True),
        name=dict(required=True),
        zone=dict(type='str', required=True),
        type=dict(choices=['A', 'AAAA', 'MX', 'CNAME', 'TXT', 'SRV'], required=True),
        content=dict(required=False, default=''),
        ttl=dict(type='int', required=False, default=DEFAULT_TTL),
        priority=dict(type='int', required=False, default=DEFAULT_PRIORITY),
        state=dict(choices=['present', 'absent'], required=False, default='present'),
        unique=dict(type='bool', required=False, default=False)
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    # if module.check_mode:
    #     module.exit_json(changed=False)
    #
    # if module.params['endpoint'] == '':
    #     module.params['endpoint'] = DEFAULT_ENDPOINT
    #
    # result['original_message'] = module.params['name'] + ' ' + module.params['type']
    # result['message'] = 'working'
    #
    # headers = {
    #     "Authorization": "Bearer " + module.params['token']
    # }
    #
    # url = "{}{}{}{}".format(module.params['endpoint'], '/api/v1/domain/', module.params['zone'], '/version/active')
    #
    # data = {
    #     "name": module.params['name'],
    #     "type": module.params['type'],
    #     "records": [
    #         {
    #             "name": module.params['name'],
    #             "type": module.params['type'],
    #             "ttl": module.params['ttl'],
    #             "data": module.params['content'],
    #         }
    #     ]
    # }
    #
    # if data["type"] == "MX":
    #     data["records"][0]["priority"] = module.params['priority']
    #
    # if (module.params['state'] == 'present') and (module.params['content'] == ''):
    #     module.fail_json(msg='content empty')
    #
    # if module.params['state'] == 'present':
    #     if module.params['unique']:
    #         change_type = 'REPLACE'
    #     else:
    #         change_type = 'ADD'
    #
    # else:
    #     change_type = 'DELETE'
    #     data['records'] = []
    #     if module.params['content'] != '':
    #         data['data'] = module.params['content']
    #
    # data['changeType'] = change_type
    #
    # r = Request()
    # result = r.patch(url, json.dumps([data]), headers=headers)
    #
    # if result.status_code != 204:
    #     # if error
    #     module.fail_json(msg='Your request failed', meta={"status": result.status_code, "data": result.json()})
    #
    # # check on api return
    # # actually always true
    # try:
    #     changed = result.headers['X-Old-Serial'] != result.headers['X-New-Serial']
    # except:
    #     changed = True
    #     module.exit_json(changed=changed, meta={"status": result.status_code})
    #
    module.exit_json(changed=changed, meta={"status": result.status_code, "serial": result.headers['X-New-Serial']})


if __name__ == '__main__':
    main()
