#!/usr/bin/python
# Copyright: (c) 2019, Whitney Champion <whitney.ellis.champion@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: graylog_streams
short_description: Communicate with the Graylog API to manage streams
description:
    - The Graylog streams module manages Graylog streams.
version_added: "2.9"
author: "Whitney Champion (@shortstack)"
options:
  endpoint:
    description:
      - Graylog endoint. (i.e. graylog.mydomain.com).
    required: false
    type: str
  graylog_user:
    description:
      - Graylog privileged user username.
    required: false
    type: str
  graylog_password:
    description:
      - Graylog privileged user password.
    required: false
    type: str
  action:
    description:
      - Action to take against stream API.
    required: false
    default: list
    choices: [ create, create_rule, start, pause, update, update_rule, delete, delete_rule, list, query_streams ]
    type: str
  title:
    description:
      - Stream title.
    required: false
    type: str
  description:
    description:
      - Stream description.
    required: false
    type: str
  stream_id:
    description:
      - Stream ID.
    required: false
    type: str
  rule_id:
    description:
      - Rule ID.
    required: false
    type: str
  index_set_id:
    description:
      - Index set ID.
    required: false
    type: str
  matching_type:
    description:
      - Matching type for the stream rules.
    required: false
    type: str
  remove_matches_from_default_stream:
    description:
      - Remove matches from default stream, true or false.
    required: false
    default: False
    type: bool
  stream_name:
    description:
      - Stream name to use with the query_streams action.
    required: false
    type: str
  field:
    description:
      - Field name for the stream rule to check.
    required: false
    type: str
  type:
    description:
      - Rule type for the stream rule, 1-7.
    required: false
    default: 1
    type: int
  value:
    description:
      - Value to check rule against.
    required: false
    type: str
  inverted:
    description:
      - Invert rule (must not match value).
    required: false
    default: False
    type: bool
  rules:
    description:
      - List of rules associated with a stream.
    required: false
    type: list
'''

EXAMPLES = '''
# List streams
- graylog_streams:
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"

# Get stream from stream name query_streams
- graylog_streams:
    action: query_streams
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"
    stream_name: "test_stream"
  register: stream

# List single stream by ID
- graylog_streams:
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"
    stream_id: "{{ stream.json.id }}"

# Create stream
- graylog_streams:
    action: create
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"
    title: "Client XYZ"
    description: "Windows and IIS logs"
    matching_type: "AND"
    remove_matches_from_default_stream: False
    rules:
      - '{"field":"message", "type":"6", "value":"test", "inverted":true, "description":"testrule"}'

# Update stream
- graylog_streams:
    action: update
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"
    stream_id: "{{ stream.json.id }}"
    remove_matches_from_default_stream: True

# Create stream rule
- graylog_streams:
    action: create_rule
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"
    stream_id: "{{ stream.json.id }}"
    description: "Windows Security Logs"
    field: "winlogbeat_log_name"
    type: 1
    value: "Security"
    inverted: False

# Start stream
- graylog_streams:
    action: start
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"
    stream_id: "{{ stream.json.id }}"

# Pause stream
- graylog_streams:
    action: pause
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"
    stream_id: "{{ stream.json.id }}"

# Update stream rule
- graylog_streams:
    action: update_rule
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"
    stream_id: "{{ stream.json.id }}"
    rule_id: "{{ rule.json.id }}"
    description: "Windows Security and Application Logs"

# Delete stream rule
- graylog_streams:
    action: delete_rule
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"
    stream_id: "{{ stream.json.id }}"
    rule_id: "{{ rule.json.id }}"

# Delete stream
- graylog_streams:
    action: delete
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"
    stream_id: "{{ stream.json.id }}"
'''

RETURN = '''
json:
  description: The JSON response from the Graylog API
  returned: always
  type: complex
  contains:
    title:
      description: Stream title.
      returned: success
      type: str
      sample: 'Windows Logs'
    alert_conditions:
      description: Alert conditions.
      returned: success
      type: dict
      sample: |
        [
            {
                "created_at": "2018-10-18T18:40:21.582+0000",
                "creator_user_id": "admin",
                "id": "cc43d4e7-e7b2-4abc-7c44-4b29cadaf364",
                "parameters": {
                    "backlog": 1,
                    "grace": 0,
                    "repeat_notifications": true,
                    "threshold": 0,
                    "threshold_type": "MORE",
                    "time": 1
                },
                "title": "Failed Logon",
                "type": "message_count"
            }
        ]
    alert_receivers:
        description: Alert receivers.
        returned: success
        type: dict
        sample: '{ "emails": [], "users": [] }'
    content_pack:
        description: Content pack.
        returned: success
        type: str
        sample: null
    created_at:
        description: Stream creation time.
        returned: success
        type: str
        sample: "2018-10-17T15:29:20.735Z"
    creator_user_id:
        description: Stream creator.
        returned: success
        type: str
        sample: "admin"
    description:
        description: Stream description.
        returned: success
        type: str
        sample: "Stream for Windows logs"
    disabled:
        description: Whether or not the stream is enabled.
        returned: success
        type: bool
        sample: false
    id:
        description: Stream ID.
        returned: success
        type: str
        sample: "5bc7666089675c7f7d7f08d7"
    index_set_id:
        description: Index set ID associated with the stream.
        returned: success
        type: str
        sample: "4bc7444089575c7f7d7f08d7"
    is_default:
        description: Whether or not it is the default stream.
        returned: success
        type: bool
        sample: false
    matching_type:
        description: Stream rule matching type.
        returned: success
        type: str
        sample: "AND"
    outputs:
        description: Stream outputs.
        returned: success
        type: dict
        sample: []
    remove_matches_from_default_stream:
        description: Whether or messages are removed from the default stream.
        returned: success
        type: bool
        sample: false
    rules:
        description: Rules associated with the stream.
        returned: success
        type: dict
        sample: []
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


def create(module, base_url, headers, index_set_id):

    url = base_url

    payload = {}

    for key in ['title', 'description', 'remove_matches_from_default_stream', 'matching_type', 'rules']:
        if module.params[key] is not None and module.params[key] != "":
            payload[key] = module.params[key]

    payload['index_set_id'] = index_set_id

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='POST', data=module.jsonify(payload))

    if info['status'] != 201:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = to_text(response.read(), errors='surrogate_or_strict')
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def create_rule(module, base_url, headers):

    url = "/".join([base_url, module.params['stream_id'], "rules"])

    payload = {}

    for key in ['field', 'type', 'value', 'inverted', 'description']:
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


def update(module, base_url, headers, stream_id, title, description, remove_matches_from_default_stream, matching_type, rules, index_set_id):

    url = "/".join([base_url, stream_id])

    payload = {}

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='GET')

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = to_text(response.read(), errors='surrogate_or_strict')
        payload_current = json.loads(content)
    except AttributeError:
        content = info.pop('body', '')

    if title is not None:
        payload['title'] = title
    else:
        payload['title'] = payload_current['title']
    if description is not None:
        payload['description'] = description
    else:
        payload['description'] = payload_current['description']
    if remove_matches_from_default_stream is not None:
        payload['remove_matches_from_default_stream'] = remove_matches_from_default_stream
    else:
        payload['remove_matches_from_default_stream'] = payload_current['remove_matches_from_default_stream']
    if matching_type is not None:
        payload['matching_type'] = matching_type
    else:
        payload['matching_type'] = payload_current['matching_type']
    if rules is not None:
        payload['rules'] = rules
    else:
        payload['rules'] = payload_current['rules']
    if index_set_id is not None:
        payload['index_set_id'] = index_set_id
    else:
        payload['index_set_id'] = payload_current['index_set_id']

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='PUT', data=module.jsonify(payload))

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = to_text(response.read(), errors='surrogate_or_strict')
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def update_rule(module, base_url, headers, stream_id, rule_id, field, type, value, inverted, description):

    payload = {}

    url = "/".join([base_url, stream_id, "rules", rule_id])

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='GET')

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = to_text(response.read(), errors='surrogate_or_strict')
        payload_current = json.loads(content)
    except AttributeError:
        content = info.pop('body', '')

    if field is not None:
        payload['field'] = field
    else:
        payload['field'] = payload_current['field']
    if type is not None:
        payload['type'] = type
    else:
        payload['type'] = payload_current['type']
    if value is not None:
        payload['value'] = value
    else:
        payload['value'] = payload_current['value']
    if inverted is not None:
        payload['inverted'] = inverted
    else:
        payload['inverted'] = payload_current['inverted']
    if description is not None:
        payload['description'] = description
    else:
        payload['description'] = payload_current['description']

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='PUT', data=module.jsonify(payload))

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = to_text(response.read(), errors='surrogate_or_strict')
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def delete(module, base_url, headers, stream_id):

    url = "/".join([base_url, stream_id])

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='DELETE')

    if info['status'] != 204:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = to_text(response.read(), errors='surrogate_or_strict')
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def delete_rule(module, base_url, headers, stream_id, rule_id):

    url = "/".join([base_url, stream_id, "rules", rule_id])

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='DELETE')

    if info['status'] != 204:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = to_text(response.read(), errors='surrogate_or_strict')
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def start(module, base_url, headers, stream_id):

    url = "/".join([base_url, stream_id, "resume"])

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='POST')

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = to_text(response.read(), errors='surrogate_or_strict')
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def pause(module, base_url, headers, stream_id):

    url = "/".join([base_url, stream_id, "pause"])

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='POST')

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = to_text(response.read(), errors='surrogate_or_strict')
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def list(module, base_url, headers, stream_id):

    if stream_id is not None:
        url = "/".join([base_url, stream_id])
    else:
        url = base_url

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='GET')

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = to_text(response.read(), errors='surrogate_or_strict')
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def query_streams(module, base_url, headers, stream_name):

    url = base_url

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='GET')

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = to_text(response.read(), errors='surrogate_or_strict')
        streams = json.loads(content)
    except AttributeError:
        content = info.pop('body', '')

    stream_id = ""
    if streams is not None:

        i = 0
        while i < len(streams['streams']):
            stream = streams['streams'][i]
            if stream_name == stream['title']:
                stream_id = stream['id']
                break
            i += 1

    return stream_id


def default_index_set(module, endpoint, base_url, headers):

    url = "https://%s/api/system/indices/index_sets?skip=0&limit=0&stats=false" % (endpoint)

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='GET')

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = to_text(response.read(), errors='surrogate_or_strict')
        indices = json.loads(content)
    except AttributeError:
        content = info.pop('body', '')

    default_index_set_id = ""
    if indices is not None:
        default_index_set_id = indices['index_sets'][0]['id']

    return default_index_set_id


def get_token(module, endpoint, username, password):

    headers = '{ "Content-Type": "application/json", "X-Requested-By": "Graylog API", "Accept": "application/json" }'

    url = "https://%s/api/system/sessions" % (endpoint)

    payload = {
        'username': username,
        'password': password,
        'host': endpoint
    }

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
            action=dict(type='str', required=False, default='list', choices=['create', 'create_rule', 'start', 'pause',
                        'update', 'update_rule', 'delete', 'delete_rule', 'list', 'query_streams']),
            stream_id=dict(type='str'),
            stream_name=dict(type='str'),
            rule_id=dict(type='str'),
            title=dict(type='str'),
            field=dict(type='str'),
            type=dict(type='int', default=1),
            value=dict(type='str'),
            index_set_id=dict(type='str'),
            inverted=dict(type='bool', default=False),
            description=dict(type='str'),
            remove_matches_from_default_stream=dict(type='bool', default=False),
            matching_type=dict(type='str'),
            rules=dict(type='list')
        )
    )

    endpoint = module.params['endpoint']
    graylog_user = module.params['graylog_user']
    graylog_password = module.params['graylog_password']
    action = module.params['action']
    stream_id = module.params['stream_id']
    stream_name = module.params['stream_name']
    rule_id = module.params['rule_id']
    title = module.params['title']
    field = module.params['field']
    type = module.params['type']
    value = module.params['value']
    index_set_id = module.params['index_set_id']
    inverted = module.params['inverted']
    description = module.params['description']
    remove_matches_from_default_stream = module.params['remove_matches_from_default_stream']
    matching_type = module.params['matching_type']
    rules = module.params['rules']

    base_url = "https://%s/api/streams" % (endpoint)

    api_token = get_token(module, endpoint, graylog_user, graylog_password)
    headers = '{ "Content-Type": "application/json", "X-Requested-By": "Graylog API", "Accept": "application/json", \
                "Authorization": "Basic ' + api_token.decode() + '" }'

    if action == "create":
        if index_set_id is None:
            index_set_id = default_index_set(module, endpoint, base_url, headers)
        status, message, content, url = create(module, base_url, headers, index_set_id)
    elif action == "create_rule":
        status, message, content, url = create_rule(module, base_url, headers)
    elif action == "update":
        status, message, content, url = update(module, base_url, headers, stream_id, title,
                                              description, remove_matches_from_default_stream, matching_type, rules, index_set_id)
    elif action == "update_rule":
        status, message, content, url = update_rule(module, base_url, headers, stream_id, rule_id, field, type, value, inverted, description)
    elif action == "delete":
        status, message, content, url = delete(module, base_url, headers, stream_id)
    elif action == "delete_rule":
        status, message, content, url = delete_rule(module, base_url, headers, stream_id, rule_id)
    elif action == "start":
        status, message, content, url = start(module, base_url, headers, stream_id)
    elif action == "pause":
        status, message, content, url = pause(module, base_url, headers, stream_id)
    elif action == "list":
        status, message, content, url = list(module, base_url, headers, stream_id)
    elif action == "query_streams":
        stream_id = query_streams(module, base_url, headers, stream_name)
        status, message, content, url = list(module, base_url, headers, stream_id)

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
