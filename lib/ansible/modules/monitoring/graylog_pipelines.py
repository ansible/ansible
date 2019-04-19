#!/usr/bin/python
# (c) 2019, Whitney Champion <whitney.ellis.champion@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: graylog_pipelines
short_description: Communicate with the Graylog API to manage pipelines
description:
    - The Graylog pipelines module manages Graylog pipelines
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
      - Action to take against pipeline API.
    required: false
    default: list
    choices: [ create, create_connection, parse_rule, create_rule, update,
                update_connection, update_rule, delete, delete_rule, list, list_rules, query_rules, query_pipelines ]
  pipeline_id:
    description:
      - Pipeline id.
    required: false
  pipeline_name:
    description:
      - Pipeline name.
    required: false
  stream_ids:
    description:
      - Stream id.
    required: false
  rule_id:
    description:
      - Rule id.
    required: false
  rule_name:
    description:
      - Rule name.
    required: false
  title:
    description:
      - Title.
    required: false
  description:
    description:
      - Description.
    required: false
  source:
    description:
      - Rule source.
    required: false
'''

EXAMPLES = '''
# List pipelines
- graylog_pipelines:
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"

# Validate/parse pipeline rule
- graylog_pipelines:
    action: parse_rule
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"
    source: |
      rule "test_rule_domain_threat_intel"
      when
         has_field("dns_query")
      then
         let dns_query_intel = threat_intel_lookup_domain(to_string($message.dns_query), "dns_query");
         set_fields(dns_query_intel);
      end

# Create pipeline rule
- graylog_pipelines:
    action: create_rule
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"
    title: "test_rule"
    description: "test"
    source: |
      rule "test_rule_domain_threat_intel"
      when
         has_field("dns_query")
      then
         let dns_query_intel = threat_intel_lookup_domain(to_string($message.dns_query), "dns_query");
         set_fields(dns_query_intel);
      end

# Create pipeline with new rule
- graylog_pipelines:
    action: create
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"
    title: "test_pipeline"
    description: "test"
    source: |
      pipeline "test_pipeline"
      stage 1 match either
      rule "test_rule_domain_threat_intel
      end

# Get pipeline from pipeline name query_pipelines
- graylog_pipelines:
    action: query_pipelines
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"
    pipeline_name: "test_pipeline"
  register: pipeline

# Create Stream connection to processing pipeline
- graylog_pipelines:
    action: create_connection
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"
    pipeline_id: "{{ pipeline.json.id }}"
    stream_ids:
      - "{{ stream.json.id }}"

# Update Stream connection to processing pipeline
- graylog_pipelines:
    action: update_connection
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"
    pipeline_id: "{{ pipeline.json.id }}"
    stream_ids:
      - "{{ stream.json.id }}"

# Remove all Streams from a pipeline
- graylog_pipelines:
    action: update_connection
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"
    pipeline_id: "{{ pipeline.json.id }}"
    stream_ids: []
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


def create(module, pipeline_url, headers, title, description, source):

    url = pipeline_url

    payload = {}

    if title is not None:
        payload['title'] = title
    if description is not None:
        payload['description'] = description
    if source is not None:
        payload['source'] = source

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='POST', data=module.jsonify(payload))

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = response.read()
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def create_connection(module, connection_url, headers, pipeline_id, stream_ids):

    url = connection_url + "/to_pipeline"

    payload = {}

    if pipeline_id is not None:
        payload['pipeline_id'] = pipeline_id
    if stream_ids is not None:
        payload['stream_ids'] = stream_ids

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='POST', data=module.jsonify(payload))

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = response.read()
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def parse_rule(module, rule_url, headers, source):

    url = rule_url + "/parse"

    payload = {}

    if source is not None:
        payload['source'] = source

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='POST', data=module.jsonify(payload))

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = response.read()
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def create_rule(module, rule_url, headers, title, description, source):

    url = rule_url

    payload = {}

    if title is not None:
        payload['title'] = title
    if description is not None:
        payload['description'] = description
    if source is not None:
        payload['source'] = source

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='POST', data=module.jsonify(payload))

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = response.read()
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def update(module, pipeline_url, headers, pipeline_id, title, description, source):

    payload = {}

    if pipeline_id is not None:
        url = pipeline_url + "/%s" % (pipeline_id)
    else:
        url = pipeline_url

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='GET')

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = response.read()
        payload_current = json.loads(content)
    except AttributeError:
        content = info.pop('body', '')

    url = pipeline_url + "/%s" % (pipeline_id)

    if title is not None:
        payload['title'] = title
    if description is not None:
        payload['description'] = description
    if source is not None:
        payload['source'] = source
    else:
        payload['source'] = payload_current['source']

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='PUT', data=module.jsonify(payload))

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = response.read()
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def update_connection(module, connection_url, headers, pipeline_id, stream_ids):

    url = connection_url + "/to_pipeline"

    payload = {}

    if pipeline_id is not None:
        payload['pipeline_id'] = pipeline_id
    if stream_ids is not None:
        payload['stream_ids'] = stream_ids

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='POST', data=module.jsonify(payload))

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = response.read()
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def update_rule(module, rule_url, headers, rule_id, title, description, source):

    url = rule_url + "/%s" % (rule_id)

    payload = {}

    if title is not None:
        payload['title'] = title
    if description is not None:
        payload['description'] = description
    if source is not None:
        payload['source'] = source

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='PUT', data=module.jsonify(payload))

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = response.read()
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def delete(module, pipeline_url, headers, pipeline_id):

    url = pipeline_url + "/%s" % (pipeline_id)

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='DELETE')

    if info['status'] != 204:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = response.read()
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def delete_rule(module, rule_url, headers, rule_id):

    url = rule_url + "/%s" % (rule_id)

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='DELETE')

    if info['status'] != 204:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = response.read()
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def list(module, pipeline_url, headers, pipeline_id, query):

    if pipeline_id is not None and pipeline_id != "":
        url = pipeline_url + "/%s" % (pipeline_id)
    elif query == "yes" and pipeline_id == "":
        url = pipeline_url + "/0"
    else:
        url = pipeline_url

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='GET')

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = response.read()
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def list_rules(module, rule_url, headers, rule_id, query):

    if rule_id is not None and rule_id != "":
        url = rule_url + "/%s" % (rule_id)
    elif query == "yes" and rule_id == "":
        url = rule_url + "/0"
    else:
        url = rule_url

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='GET')

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = response.read()
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def query_pipelines(module, pipeline_url, headers, pipeline_name):

    url = pipeline_url

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='GET')

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = response.read()
        pipelines = json.loads(content)
    except AttributeError:
        content = info.pop('body', '')

    pipeline_id = ""
    if pipelines is not None:

        i = 0
        while i < len(pipelines):
            pipeline = pipelines[i]
            if pipeline_name == pipeline['title']:
                pipeline_id = pipeline['id']
                break
            i += 1

    return pipeline_id


def query_rules(module, rule_url, headers, rule_name):

    url = rule_url

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='GET')

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = response.read()
        rules = json.loads(content)
    except AttributeError:
        content = info.pop('body', '')

    rule_id = ""
    if rules is not None:

        i = 0
        while i < len(rules):
            rule = rules[i]
            if rule_name == rule['title']:
                rule_id = rule['id']
                break
            i += 1

    return rule_id


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
            action=dict(type='str', required=False, default='list',
                        choices=['create', 'create_connection', 'parse_rule', 'create_rule', 'update', 'update_connection',
                                 'update_rule', 'delete', 'delete_rule', 'list', 'list_rules', 'query_rules', 'query_pipelines']),
            pipeline_id=dict(type='str'),
            pipeline_name=dict(type='str'),
            rule_id=dict(type='str'),
            rule_name=dict(type='str'),
            stream_ids=dict(type='list'),
            title=dict(type='str'),
            description=dict(type='str'),
            source=dict(type='str')
        )
    )

    endpoint = module.params['endpoint']
    graylog_user = module.params['graylog_user']
    graylog_password = module.params['graylog_password']
    action = module.params['action']
    pipeline_id = module.params['pipeline_id']
    pipeline_name = module.params['pipeline_name']
    rule_id = module.params['rule_id']
    rule_name = module.params['rule_name']
    stream_ids = module.params['stream_ids']
    title = module.params['title']
    description = module.params['description']
    source = module.params['source']

    pipeline_url = "https://%s/api/system/pipelines/pipeline" % (endpoint)
    rule_url = "https://%s/api/system/pipelines/rule" % (endpoint)
    connection_url = "https://%s/api/system/pipelines/connections" % (endpoint)

    api_token = get_token(module, endpoint, graylog_user, graylog_password)
    headers = '{ "Content-Type": "application/json", "X-Requested-By": "Graylog API", "Accept": "application/json", \
                "Authorization": "Basic ' + api_token.decode() + '" }'

    if action == "create":
        status, message, content, url = create(module, pipeline_url, headers, title, description, source)
    elif action == "parse_rule":
        status, message, content, url = parse_rule(module, rule_url, headers, source)
    elif action == "create_rule":
        status, message, content, url = create_rule(module, rule_url, headers, title, description, source)
    elif action == "create_connection":
        status, message, content, url = create_connection(module, connection_url, headers, pipeline_id, stream_ids)
    elif action == "update":
        status, message, content, url = update(module, pipeline_url, headers, pipeline_id, title, description, source)
    elif action == "update_connection":
        status, message, content, url = update_connection(module, connection_url, headers, pipeline_id, stream_ids)
    elif action == "update_rule":
        status, message, content, url = update_rule(module, rule_url, headers, rule_id, title, description, source)
    elif action == "delete":
        status, message, content, url = delete(module, pipeline_url, headers, pipeline_id)
    elif action == "delete_rule":
        status, message, content, url = delete_rule(module, rule_url, headers, rule_id)
    elif action == "list":
        query = "no"
        status, message, content, url = list(module, pipeline_url, headers, pipeline_id, query)
    elif action == "query_pipelines":
        pipeline_id = query_pipelines(module, pipeline_url, headers, pipeline_name)
        query = "yes"
        status, message, content, url = list(module, pipeline_url, headers, pipeline_id, query)
    elif action == "list_rules":
        query = "no"
        status, message, content, url = list_rules(module, rule_url, headers, rule_id, query)
    elif action == "query_rules":
        rule_id = query_rules(module, rule_url, headers, rule_name)
        query = "yes"
        status, message, content, url = list_rules(module, rule_url, headers, rule_id, query)

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
