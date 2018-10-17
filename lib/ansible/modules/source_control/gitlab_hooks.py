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
module: gitlab_hooks
short_description: Manages GitLab project hooks.
description:
     - Adds, updates and removes project hooks
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
  hook_url:
    description:
      - The url that you want GitLab to post to, this is used as the primary key for updates and deletion.
    required: true
  state:
    description:
      - When C(present) the hook will be updated to match the input or created if it doesn't exist. When C(absent) it will be deleted if it exists.
    required: true
    default: present
    choices: [ "present", "absent" ]
  push_events:
    description:
      - Trigger hook on push events
    type: bool
    default: 'yes'
  issues_events:
    description:
      - Trigger hook on issues events
    type: bool
    default: 'no'
  merge_requests_events:
    description:
      - Trigger hook on merge requests events
    type: bool
    default: 'no'
  tag_push_events:
    description:
      - Trigger hook on tag push events
    type: bool
    default: 'no'
  note_events:
    description:
      - Trigger hook on note events
    type: bool
    default: 'no'
  job_events:
    description:
      - Trigger hook on job events
    type: bool
    default: 'no'
  pipeline_events:
    description:
      - Trigger hook on pipeline events
    type: bool
    default: 'no'
  wiki_page_events:
    description:
      - Trigger hook on wiki events
    type: bool
    default: 'no'
  enable_ssl_verification:
    description:
      - Whether GitLab will do SSL verification when triggering the hook
    type: bool
    default: 'no'
  token:
    description:
      - Secret token to validate hook messages at the receiver.
      - If this is present it will always result in a change as it cannot be retrieved from GitLab.
      - Will show up in the X-Gitlab-Token HTTP request header
    required: false
author: "Marcus Watkins (@marwatk)"
'''

EXAMPLES = '''
# Example creating a new project hook
- gitlab_hooks:
    api_url: https://gitlab.example.com/api
    access_token: "{{ access_token }}"
    project: "my_group/my_project"
    hook_url: "https://my-ci-server.example.com/gitlab-hook"
    state: present
    push_events: yes
    enable_ssl_verification: no
    token: "my-super-secret-token-that-my-ci-server-will-check"

# Update the above hook to add tag pushes
- gitlab_hooks:
    api_url: https://gitlab.example.com/api
    access_token: "{{ access_token }}"
    project: "my_group/my_project"
    hook_url: "https://my-ci-server.example.com/gitlab-hook"
    state: present
    push_events: yes
    tag_push_events: yes
    enable_ssl_verification: no
    token: "my-super-secret-token-that-my-ci-server-will-check"

# Delete the previous hook
- gitlab_hooks:
    api_url: https://gitlab.example.com/api
    access_token: "{{ access_token }}"
    project: "my_group/my_project"
    hook_url: "https://my-ci-server.example.com/gitlab-hook"
    state: absent

# Delete a hook by numeric project id
- gitlab_hooks:
    api_url: https://gitlab.example.com/api
    access_token: "{{ access_token }}"
    project: 10
    hook_url: "https://my-ci-server.example.com/gitlab-hook"
    state: absent
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
    path = "/hooks"
    return request(module, api_url, project, path, access_token, private_token)


def _find(module, api_url, project, hook_url, access_token, private_token):
    success, data = _list(module, api_url, project, access_token, private_token)
    if success:
        for i in data:
            if i["url"] == hook_url:
                return success, i
        return success, None
    return success, data


def _publish(module, api_url, project, data, access_token, private_token):
    path = "/hooks"
    method = "POST"
    if 'id' in data:
        path += "/%s" % str(data["id"])
        method = "PUT"
    data = deepcopy(data)
    data.pop('id', None)
    return request(module, api_url, project, path, access_token, private_token, json.dumps(data, sort_keys=True), method)


def _delete(module, api_url, project, hook_id, access_token, private_token):
    path = "/hooks/%s" % str(hook_id)
    return request(module, api_url, project, path, access_token, private_token, method='DELETE')


def _are_equivalent(input, existing):
    for key in [
            'url', 'push_events', 'issues_events', 'merge_requests_events',
            'tag_push_events', 'note_events', 'job_events', 'pipeline_events', 'wiki_page_events',
            'enable_ssl_verification']:
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
            hook_url=dict(required=True),
            state=dict(default='present', choices=['present', 'absent']),
            push_events=dict(default='yes', type='bool'),
            issues_events=dict(default='no', type='bool'),
            merge_requests_events=dict(default='no', type='bool'),
            tag_push_events=dict(default='no', type='bool'),
            note_events=dict(default='no', type='bool'),
            job_events=dict(default='no', type='bool'),
            pipeline_events=dict(default='no', type='bool'),
            wiki_page_events=dict(default='no', type='bool'),
            enable_ssl_verification=dict(default='no', type='bool'),
            token=dict(required=False, no_log=True),
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

    input = {'url': module.params['hook_url']}

    for key in [
            'push_events', 'issues_events', 'merge_requests_events',
            'tag_push_events', 'note_events', 'job_events', 'pipeline_events', 'wiki_page_events',
            'enable_ssl_verification', 'token']:
        input[key] = module.params[key]

    success, existing = _find(module, api_url, project, input['url'], access_token, private_token)

    if not success:
        module.fail_json(msg="failed to list hooks", result=existing)

    if existing:
        input['id'] = existing['id']

    changed = False
    success = True
    response = None

    if state == 'present':
        if not existing or input['token'] or not _are_equivalent(existing, input):
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
