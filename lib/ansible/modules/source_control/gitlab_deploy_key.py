#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Marcus Watkins <marwatk@marcuswatkins.net>
# Based on code:
# (c) 2013, Phillip Gentry <phillip@cx.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: gitlab_deploy_key
short_description: Manages GitLab project deploy keys.
description:
     - Adds, updates and removes project deploy keys
version_added: "2.6"
options:
  api_url:
    description:
      - GitLab API url, e.g. https://gitlab.example.com/api
    required: true
  access_token:
    description:
      - The oauth key provided by GitLab. One of access_token or private_token is required. See https://docs.gitlab.com/ee/api/oauth2.html
    required: false
  private_token:
    description:
      - Personal access token to use. One of private_token or access_token is required. See https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html
    required: false
  project:
    description:
      - Numeric project id or name of project in the form of group/name
    required: true
  title:
    description:
      - Deploy key's title
    required: true
  key:
    description:
      - Deploy key
    required: true
  can_push:
    description:
      - Whether this key can push to the project
    type: bool
    default: 'no'
  state:
    description:
      - When C(present) the deploy key added to the project if it doesn't exist.
      - When C(absent) it will be removed from the project if it exists
    required: true
    default: present
    choices: [ "present", "absent" ]
author: "Marcus Watkins (@marwatk)"
'''

EXAMPLES = '''
# Example adding a project deploy key
- gitlab_deploy_key:
    api_url: https://gitlab.example.com/api
    access_token: "{{ access_token }}"
    project: "my_group/my_project"
    title: "Jenkins CI"
    state: present
    key: "ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAIEAiPWx6WM4lhHNedGfBpPJNPpZ7yKu+dnn1SJejgt4596k6YjzGGphH2TUxwKzxcKDKKezwkpfnxPkSMkuEspGRt/aZZ9w..."

# Update the above deploy key to add push access
- gitlab_deploy_key:
    api_url: https://gitlab.example.com/api
    access_token: "{{ access_token }}"
    project: "my_group/my_project"
    title: "Jenkins CI"
    state: present
    key: "ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAIEAiPWx6WM4lhHNedGfBpPJNPpZ7yKu+dnn1SJejgt4596k6YjzGGphH2TUxwKzxcKDKKezwkpfnxPkSMkuEspGRt/aZZ9w..."
    can_push: yes

# Remove the previous deploy key from the project
- gitlab_deploy_key:
    api_url: https://gitlab.example.com/api
    access_token: "{{ access_token }}"
    project: "my_group/my_project"
    state: absent
    key: "ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAIEAiPWx6WM4lhHNedGfBpPJNPpZ7yKu+dnn1SJejgt4596k6YjzGGphH2TUxwKzxcKDKKezwkpfnxPkSMkuEspGRt/aZZ9w..."

'''

RETURN = '''
msg:
    description: Success or failure message
    returned: always
    type: string
    sample: "Success"

result:
    description: json parsed response from the server
    returned: always
    type: dict

error:
    description: the error message returned by the Gitlab API
    returned: failed
    type: string
    sample: "400: key is already in use"

previous_version:
    description: object describing the state prior to this task
    returned: changed
    type: dict
'''


import json

from ansible.module_utils.basic import AnsibleModule
from copy import deepcopy
from ansible.module_utils.gitlab import request


def _list(module, api_url, project, access_token, private_token):
    path = "/deploy_keys"
    return request(module, api_url, project, path, access_token, private_token)


def _find(module, api_url, project, key, access_token, private_token):
    success, data = _list(module, api_url, project, access_token, private_token)
    if success:
        for i in data:
            if i["key"] == key:
                return success, i
        return success, None
    return success, data


def _publish(module, api_url, project, data, access_token, private_token):
    path = "/deploy_keys"
    method = "POST"
    if 'id' in data:
        path += "/%s" % str(data["id"])
        method = "PUT"
    data = deepcopy(data)
    data.pop('id', None)
    return request(module, api_url, project, path, access_token, private_token, json.dumps(data, sort_keys=True), method)


def _delete(module, api_url, project, key_id, access_token, private_token):
    path = "/deploy_keys/%s" % str(key_id)
    return request(module, api_url, project, path, access_token, private_token, method='DELETE')


def _are_equivalent(input, existing):
    for key in ['title', 'key', 'can_push']:
        if key in input and key not in existing:
            return False
        if key not in input and key in existing:
            return False
        if not input[key] == existing[key]:
            return False
    return True


def main():
    module = AnsibleModule(
        argument_spec=dict(
            api_url=dict(required=True),
            access_token=dict(required=False, no_log=True),
            private_token=dict(required=False, no_log=True),
            project=dict(required=True),
            key=dict(required=True),
            state=dict(default='present', choices=['present', 'absent']),
            can_push=dict(default='no', type='bool'),
            title=dict(required=True),
        ),
        mutually_exclusive=[
            ['access_token', 'private_token']
        ],
        required_one_of=[
            ['access_token', 'private_token']
        ],
        supports_check_mode=True,
    )

    api_url = module.params['api_url']
    access_token = module.params['access_token']
    private_token = module.params['private_token']
    project = module.params['project']
    state = module.params['state']

    if not access_token and not private_token:
        module.fail_json(msg="need either access_token or private_token")

    input = {}

    for key in ['title', 'key', 'can_push']:
        input[key] = module.params[key]

    success, existing = _find(module, api_url, project, input['key'], access_token, private_token)

    if not success:
        module.fail_json(msg="failed to list deploy keys", result=existing)

    if existing:
        input['id'] = existing['id']

    changed = False
    success = True
    response = None

    if state == 'present':
        if not existing or not _are_equivalent(existing, input):
            if not module.check_mode:
                success, response = _publish(module, api_url, project, input, access_token, private_token)
            changed = True
    else:
        if existing:
            if not module.check_mode:
                success, response = _delete(module, api_url, project, existing['id'], access_token, private_token)
            changed = True

    if success:
        module.exit_json(changed=changed, msg='Success', result=response, previous_version=existing)
    else:
        module.fail_json(msg='Failure', error=response)

if __name__ == '__main__':
    main()
