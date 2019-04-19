#!/usr/bin/python
# (c) 2019, Whitney Champion <whitney.ellis.champion@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: graylog_roles
short_description: Communicate with the Graylog API to manage roles
description:
    - The Graylog roles module manages Graylog roles
version_added: "2.9"
author: "Whitney Champion (@shortstack)"
options:
  endpoint:
    description:
      - Graylog endoint. (i.e. graylog.mydomain.com).
    required: false
  graylog_user:
    description:
      - Graylog privileged user username.
    required: false
  graylog_password:
    description:
      - Graylog privileged user password.
    required: false
  action:
    description:
      - Action to take against role API.
    required: false
    default: list
    choices: [ create, update, delete, list ]
  name:
    description:
      - Role name.
    required: false
  description:
    description:
      - Role description.
    required: false
  permissions:
    description:
      - Permissions list for role.
    required: false
  read_only:
    description:
      - Read only, true or false.
    required: false
    default: "false"
'''

EXAMPLES = '''
# List roles
- graylog_roles:
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"

# Create role
- graylog_roles:
    action: create
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"
    name: "analysts"
    description: "Analyst role"
    permissions:
      - "streams:read"
      - "dashboards:read"
    read_only: "true"

# Create admin role
- graylog_roles:
    action: create
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"
    name: "admins"
    description: "Admin role"
    permissions:
      - "*"
    read_only: "false"

# Delete role
- graylog_roles:
    action: delete
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"
    name: "admins"
'''

RETURN = '''
json:
  description: The JSON response from the Graylog API
  returned: always
  type: str
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


def create(module, base_url, headers, name, description, permissions, read_only):

    url = base_url

    payload = {}

    if name is not None:
        payload['name'] = name
    if description is not None:
        payload['description'] = description
    if permissions is not None:
        payload['permissions'] = permissions
    if read_only is not None:
        payload['read_only'] = read_only

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='POST', data=module.jsonify(payload))

    if info['status'] != 201:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = response.read()
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def update(module, base_url, headers, name, description, permissions, read_only):

    url = base_url + "/%s" % (name)

    payload = {}

    if name is not None:
        payload['name'] = name
    if description is not None:
        payload['description'] = description
    if permissions is not None:
        payload['permissions'] = permissions
    if read_only is not None:
        payload['read_only'] = read_only

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='PUT', data=module.jsonify(payload))

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = response.read()
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def delete(module, base_url, headers, name):

    url = base_url + "/%s" % (name)

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='DELETE')

    if info['status'] != 204:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = response.read()
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def list(module, base_url, headers):

    url = base_url

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='GET')

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = response.read()
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
        content = response.read()
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
            action=dict(type='str', default='list', choices=['create', 'update', 'delete', 'list']),
            name=dict(type='str'),
            description=dict(type='str'),
            permissions=dict(type='list'),
            read_only=dict(type='str', default="false")
        )
    )

    endpoint = module.params['endpoint']
    graylog_user = module.params['graylog_user']
    graylog_password = module.params['graylog_password']
    action = module.params['action']
    name = module.params['name']
    description = module.params['description']
    permissions = module.params['permissions']
    read_only = module.params['read_only']

    base_url = "https://%s/api/roles" % (endpoint)

    api_token = get_token(module, endpoint, graylog_user, graylog_password)
    headers = '{ "Content-Type": "application/json", "X-Requested-By": "Graylog API", "Accept": "application/json", \
                "Authorization": "Basic ' + api_token.decode() + '" }'

    if action == "create":
        status, message, content, url = create(module, base_url, headers, name, description, permissions, read_only)
    elif action == "update":
        status, message, content, url = update(module, base_url, headers, name, description, permissions, read_only)
    elif action == "delete":
        status, message, content, url = delete(module, base_url, headers, name)
    elif action == "list":
        status, message, content, url = list(module, base_url, api_token)

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
