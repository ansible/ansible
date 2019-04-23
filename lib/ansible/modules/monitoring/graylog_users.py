#!/usr/bin/python
# Copyright: (c) 2019, Whitney Champion <whitney.ellis.champion@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: graylog_users
short_description: Communicate with the Graylog API to manage users
description:
    - The Graylog user module manages Graylog users.
version_added: "2.9"
author: "Whitney Champion (@shortstack)"
options:
  endpoint:
    description:
      - Graylog endpoint. (i.e. graylog.mydomain.com:9000).
    required: false
    type: str
  graylog_user:
    description:
      - Graylog privileged user username, used to auth with Graylog API.
    required: false
    type: str
  graylog_password:
    description:
      - Graylog privileged user password, used to auth with Graylog API.
    required: false
    type: str
  action:
    description:
      - Action to take against user API.
    required: false
    default: list
    choices: [ create, update, delete, list ]
    type: str
  username:
    description:
      - Username.
    required: false
    type: str
  password:
    description:
      - Password.
    required: false
    type: str
  full_name:
    description:
      - Display name.
    required: false
    type: str
  email:
    description:
      - Email.
    required: false
    type: str
  roles:
    description:
      - List of role names to add the user to.
    required: false
    type: list
  permissions:
    description:
      - List of permission names to add the user to.
    required: false
    type: list
  timezone:
    description:
      - Timezone.
    required: false
    default: 'UTC'
    type: str
'''

EXAMPLES = '''
# List users
- graylog_users:
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"

# Create user
- graylog_users:
    action: create
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"
    username: "whitney"
    full_name: "Whitney"
    email: "whitney@unicorns.lol"
    password: "cookiesaredelicious"
    roles:
      - "analysts"
    permissions:
      - "*"

# Create user with role(s)
- graylog_users:
    action: create
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"
    username: "whitney"
    full_name: "Whitney"
    email: "whitney@unicorns.lol"
    password: "cookiesaredelicious"
    roles:
      - "analysts"

# Create multiple users with admin roles
- graylog_users:
    action: create
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"
    username: "{{ item.username }}"
    full_name: "{{ item.full_name }}"
    email: "{{ item.email }}"
    password: "{{ item.password }}"
    roles:
      - "admins"
  with_items:
    - { username: "alice", full_name: "Alice", email: "alice@aolcom", password: "ilovebob111" }
    - { username: "bob", full_name: "Bob", email: "bob@aolcom", password: "ilovealice111" }

# Update user's email address
- graylog_users:
    action: update
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"
    username: "whitney"
    email: "whitney@ihateunicorns.lol"

# Delete user
- graylog_users:
    action: delete
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"
    username: "whitney"
'''

RETURN = '''
json:
  description: The JSON response from the Graylog API
  returned: always
  type: complex
  contains:
      username:
          description: Username.
          returned: success
          type: str
          sample: 'john'
      id:
          description: User ID.
          returned: success
          type: str
          sample: '4bc73d5108e33b4810f3eab0'
      email:
          description: User email.
          returned: success
          type: str
          sample: 'john@domain.com'
      full_name:
          description: Full name of the user.
          returned: success
          type: str
          sample: 'John Smith'
      last_activity:
          description: Last user activity.
          returned: success
          type: str
          sample: '2019-04-21T23:16:53.500+0000'
      external:
          description: Whether or not the user was created from an external authentication source (such as LDAP).
          returned: success
          type: bool
          sample: true
      session_active:
          description: Whether or not the user's session is active.
          returned: success
          type: bool
          sample: true
      session_timeout_ms:
          description: Session automatically ends after this amount of time.
          returned: success
          type: int
          sample: 3600000
      startpage:
          description: User's start page.
          returned: success
          type: dict
          sample: { "id": "5b05eea33f5e865e57babfae", "type": "dashboard" }
      preferences:
          description: User's preferences.
          returned: success
          type: dict
          sample: { "enableSmartSearch": true }
      timezone:
          description: User's timezone.
          returned: success
          type: str
          sample: 'America/Chicago'
      permissions:
          description: User permissions (dashboards, streams, collectors, etc).
          returned: success
          type: list
          sample: [ "dashboards:read:4c58eef77ec84145c3a2d9f3" ]
      roles:
          description: User roles.
          returned: success
          type: list
          sample: [ "analyst", "Administrator" ]
      read_only:
          description: Whether or not the user is a read-only user.
          returned: success
          type: bool
          sample: false
msg:
  description: The HTTP message from the request
  returned: always
  type: str
  sample: OK (unknown bytes)
status:
  description: The HTTP status code from the request
  returned: always
  type: int
  sample: 200
url:
  description: The actual URL used for the request
  returned: always
  type: str
  sample: https://www.ansible.com/
'''


# import module snippets
import json
import base64
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url, to_text


def create(module, base_url, headers):

    url = base_url

    payload = {}

    for key in ['full_name', 'email', 'username', 'password', 'roles', 'permissions', 'timezone']:
        if module.params[key] is not None:
            payload[key] = module.params[key]

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='POST', data=module.jsonify(payload))

    if info['status'] != 201:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = to_text(response.read(), errors='surrogate_or_strict')
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def update(module, base_url, headers):

    url = "/".join([base_url, module.params['username']])

    payload = {}

    for key in ['full_name', 'email', 'username', 'password', 'roles', 'permissions', 'timezone']:
        if module.params[key] is not None:
            payload[key] = module.params[key]

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='PUT', data=module.jsonify(payload))

    if info['status'] != 204:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = to_text(response.read(), errors='surrogate_or_strict')
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def delete(module, base_url, headers):

    url = "/".join([base_url, module.params['username']])

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='DELETE')

    if info['status'] != 204:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = to_text(response.read(), errors='surrogate_or_strict')
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def list(module, base_url, headers):

    url = base_url

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='GET')

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = to_text(response.read(), errors='surrogate_or_strict')
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def get_token(module, endpoint, username, password):

    headers = '{ "Content-Type": "application/json", "X-Requested-By": "Graylog API", "Accept": "application/json" }'

    url = "https://%s/api/system/sessions" % (endpoint)

    payload = {}
    payload['username'] = username
    payload['password'] = password
    payload['host'] = endpoint

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='POST', data=module.jsonify(payload))

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = to_text(response.read(), errors='surrogate_or_strict')
        session = json.loads(content)
    except AttributeError:
        content = info.pop('body', '')

    session_string = session['session_id'] + ":session"
    session_bytes = session_string.encode('utf-8')
    session_token = base64.b64encode(session_bytes)

    return session_token


def main():
    module = AnsibleModule(
        argument_spec=dict(
            endpoint=dict(type='str'),
            graylog_user=dict(type='str'),
            graylog_password=dict(type='str', no_log=True),
            action=dict(type='str', required=False, default='list', choices=['create', 'update', 'delete', 'list']),
            username=dict(type='str'),
            password=dict(type='str', no_log=True),
            full_name=dict(type='str'),
            email=dict(type='str'),
            timezone=dict(type='str', default='UTC'),
            roles=dict(type='list'),
            permissions=dict(type='list', default=[])
        )
    )

    endpoint = module.params['endpoint']
    graylog_user = module.params['graylog_user']
    graylog_password = module.params['graylog_password']
    action = module.params['action']

    base_url = "https://%s/api/users" % (endpoint)

    api_token = get_token(module, endpoint, graylog_user, graylog_password)
    headers = '{ "Content-Type": "application/json", "X-Requested-By": "Graylog API", "Accept": "application/json", \
                "Authorization": "Basic ' + api_token.decode() + '" }'

    if action == "create":
        status, message, content, url = create(module, base_url, headers)
    elif action == "update":
        status, message, content, url = update(module, base_url, headers)
    elif action == "delete":
        status, message, content, url = delete(module, base_url, headers)
    elif action == "list":
        status, message, content, url = list(module, base_url, headers)

    uresp = {}
    content = to_text(content, encoding='UTF-8')

    try:
        js = json.loads(content)
    except ValueError:
        js = ""

    uresp['json'] = js
    uresp['status'] = status
    uresp['msg'] = message
    uresp['url'] = url

    module.exit_json(**uresp)


if __name__ == '__main__':
    main()
