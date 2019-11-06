#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2019, Sebastien Wains <swains@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
version_added: "2.10"
module: gotify
short_description: Send a message to Gotify
description:
  - Send messages to a Gotify server, notifying your devices (Android or browser)
notes:
  - An application must be created in Gotify. A token is automatically generated for the application.
  - More info about Gotify can be found at U(https://gotify.net/)
  - Full API documentation can be found at U(https://gotify.net/api-docs)
options:
  url:
    description:
      - URL to connect to
    required: true
  token:
    description:
      - Application token
    required: true
  title:
    description:
      - The title of the message
    default: Ansible Notification
    required: False
  msg:
    description:
      - The message body
    required: true
  priority:
    description:
      - The message priority (0 to 5)
    default: 2
    type: int

author: 
    - "Sebastien Wains <swains@redhat.com>"
'''

EXAMPLES = '''
# send a message
- gotify:
    url: https://gotify.example.org
    token: APuAua7NNgVwhV5
    title: My Ansible Notification
    msg: Ansible task finished

# send a message with higher priority
- gotify:
    url: https://gotify.example.org
    token: APuAua7NNgVwhV5
    title: My Ansible Notification
    msg: Ansible task finished
    priority: 4

# send a message to a non TLS Gotify instance, running on a non standard port and under /mygotify/ path
- gotify:
    url: http://www.example.org:88/gotify/
    token: APuAua7NNgVwhV5
    title: My Ansible Notification
    msg: Ansible task finished
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url

def run_module():

    module_args = dict(
        url=dict(type='str', required=True),
        token=dict(type='str', required=True, no_log=True),
        msg=dict(type='str', required=True),
        priority=dict(type='int', default=2, required=False),
        title=dict(type='str', default='Ansible Notification', required=False),
    )

    result = dict(
        changed=False
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    token = module.params['token']
    msg = module.params['msg']
    title = module.params['title']
    url = module.params['url']
    priority = module.params['priority']

    # If URL has no trailing slash, add it
    if url[len(url)-1] != "/":
        url += "/"

    full_url = "%smessage?token=%s" % (url, token)

    # In check mode, exit before actually sending the message
    # Check mode will only tell you if a required option is missing and won't 
    # check if Gotify is available or if the token is valid.
    if module.check_mode:
        module.exit_json(changed=False)

    payload={
            "message": msg,
            "priority": priority,
            "title": title
    }

    result = module.params

    payload = module.jsonify(payload)

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    response, info = fetch_url(module=module, 
                                url=full_url, 
                                headers=headers, 
                                method='POST', 
                                data=payload)

    result['http result'] = info['status']

    if info['status'] != 200:
        result['error'] = info['body']
        module.fail_json(**result)

    result['changed'] = True
    module.exit_json(**result)

if __name__ == '__main__':
    run_module()
