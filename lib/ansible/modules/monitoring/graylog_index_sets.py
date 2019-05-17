#!/usr/bin/python
# Copyright: (c) 2019, Whitney Champion <whitney.ellis.champion@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: graylog_index_sets
short_description: Communicate with the Graylog API to manage index sets
description:
    - The Graylog index sets module manages Graylog index sets.
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
      - Action to take against index API.
    required: false
    default: list
    choices: [ create, update, list, delete, query_index_sets ]
    type: str
  id:
    description:
      - Index set id.
    required: false
    type: str
  title:
    description:
      - Title.
    required: false
    type: str
  description:
    description:
      - Description.
    required: false
    type: str
  creation_date:
    description:
      - Index set creation date.
    required: false
    type: str
  index_prefix:
    description:
      - A unique prefix used in Elasticsearch indices belonging to this index set. The prefix must start
        with a letter or number, and can only contain letters, numbers, '_', '-' and '+'.
    required: false
    type: str
  field_type_refresh_interval:
    description:
      - How often the field type information for the active write index will be updated.
    required: false
    type: int
  index_analyzer:
    description:
      - Elasticsearch analyzer for this index set.
    required: false
    default: "standard"
    type: str
  shards:
    description:
      - Number of Elasticsearch shards used per index in this index set.
    required: false
    default: 4
    type: int
  replicas:
    description:
      - Number of Elasticsearch replicas used per index in this index set.
    required: false
    default: 1
    type: int
  rotation_strategy_class:
    description:
      - Rotation strategy class, ex. org.graylog2.indexer.rotation.strategies.TimeBasedRotationStrategy
    required: false
    default: "org.graylog2.indexer.rotation.strategies.TimeBasedRotationStrategy"
    type: str
  retention_strategy_class:
    description:
      - Retention strategy class, ex. org.graylog2.indexer.retention.strategies.DeletionRetentionStrategy
    required: false
    default: "org.graylog2.indexer.retention.strategies.DeletionRetentionStrategy"
    type: str
  rotation_strategy:
    description:
      - Graylog uses multiple indices to store documents in. You can configure the strategy it uses to determine
         when to rotate the currently active write index.
    required: false
    default: {'type': 'org.graylog2.indexer.rotation.strategies.TimeBasedRotationStrategyConfig', 'rotation_period': 'P1D'}
    type: dict
  retention_strategy:
    description:
      - Graylog uses a retention strategy to clean up old indices.
    required: false
    default: {'type': 'org.graylog2.indexer.retention.strategies.DeletionRetentionStrategyConfig', 'max_number_of_indices': 14}
    type: dict
  index_optimization_max_num_segments:
    description:
      - Maximum number of segments per Elasticsearch index after optimization (force merge).
    required: false
    default: 1
    type: int
  index_optimization_disabled:
    description:
      - Disable Elasticsearch index optimization (force merge) after rotation.
    required: false
    default: False
    type: bool
  writable:
    description:
      - Writable, true or false.
    required: false
    default: True
    type: bool
  default:
    description:
      - Default index set, true or false.
    required: false
    default: False
    type: bool
'''

EXAMPLES = '''
# List index sets
- graylog_index_sets:
    endpoint: "graylog.mydomain.com"
    graylog_user: "username"
    graylog_password: "password"

# Create index rule
- graylog_index_sets:
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
'''

RETURN = '''
json:
  description: The JSON response from the Graylog API
  returned: always
  type: complex
  contains:
      title:
          description: Title.
          returned: success
          type: str
          sample: 'Graylog'
      creation_date:
          description: Index set creation date.
          returned: success
          type: str
          sample: '2019-01-21T19:45:09.098Z'
      default:
          description: Whether or not it is the default index set.
          returned: success
          type: bool
          sample: false
      description:
          description: Index set description.
          returned: success
          type: str
          sample: 'Client X index set'
      field_type_refresh_interval:
          description: How often the field type information for the active write index will be updated.
          returned: success
          type: int
          sample: 5000
      id:
          description: Index set ID.
          returned: success
          type: str
          sample: '4a362233815c349e7e2b945c'
      index_analyzer:
          description: Index set analyzer.
          returned: success
          type: str
          sample: 'standard'
      index_optimization_disabled:
          description: Whether index set optimization is enabled or disabled.
          returned: success
          type: bool
          sample: false
      index_optimization_max_num_segments:
          description: Index optimization segments.
          returned: success
          type: int
          sample: 1
      index_prefix:
          description: Index set prefix.
          returned: success
          type: str
          sample: 'graylog'
      replicas:
          description: Number of replicas.
          returned: success
          type: int
          sample: 1
      retention_strategy:
          description: Index set retention strategy.
          returned: success
          type: dict
          sample: { "max_number_of_indices": 720, "type": "org.graylog2.indexer.retention.strategies.DeletionRetentionStrategyConfig" }
      rotation_strategy:
          description: Index set rotation strategy.
          returned: success
          type: dict
          sample: { "rotation_period": "PT6H", "type": "org.graylog2.indexer.rotation.strategies.TimeBasedRotationStrategyConfig" }
      retention_strategy_class:
          description: Retention strategy class.
          returned: success
          type: str
          sample: 'org.graylog2.indexer.retention.strategies.DeletionRetentionStrategy'
      rotation_strategy_class:
          description: Rotation strategy class.
          returned: success
          type: str
          sample: 'org.graylog2.indexer.rotation.strategies.TimeBasedRotationStrategy'
      shards:
          description: Number of shards.
          returned: success
          type: int
          sample: 4
      writable:
          description: Whether or not index set is writable.
          returned: success
          type: bool
          sample: true
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
import datetime
import base64
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url, to_text


def create(module, base_url, headers, creation_date):

    url = base_url

    payload = {}

    for key in ['title', 'description', 'index_prefix', 'field_type_refresh_interval', 'writable', 'default',
                'index_analyzer', 'shards', 'replicas', 'rotation_strategy_class', 'retention_strategy_class',
                'rotation_strategy', 'retention_strategy', 'index_optimization_max_num_segments',
                'index_optimization_disabled']:
        if module.params[key] is not None:
            payload[key] = module.params[key]

    payload['creation_date'] = creation_date

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='POST', data=module.jsonify(payload))

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = to_text(response.read(), errors='surrogate_or_strict')
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def update(module, base_url, headers):

    url = "/".join([base_url, module.params['id']])

    payload = {}

    for key in ['title', 'description', 'index_prefix', 'field_type_refresh_interval', 'writable', 'default',
                'index_analyzer', 'shards', 'replicas', 'rotation_strategy_class', 'retention_strategy_class',
                'rotation_strategy', 'retention_strategy', 'index_optimization_max_num_segments',
                'index_optimization_disabled']:
        if module.params[key] is not None:
            payload[key] = module.params[key]

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='PUT', data=module.jsonify(payload))

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = to_text(response.read(), errors='surrogate_or_strict')
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def delete(module, base_url, headers, id):

    url = base_url + "/%s" % (id)

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='DELETE')

    if info['status'] != 204:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = to_text(response.read(), errors='surrogate_or_strict')
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def list(module, base_url, headers, id):

    if id is not None:
        url = base_url + "/%s" % (id)
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


def query_index_sets(module, base_url, headers, title):

    url = base_url

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='GET')

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = to_text(response.read(), errors='surrogate_or_strict')
        index_sets = json.loads(content)
    except AttributeError:
        content = info.pop('body', '')

    id = ""
    if index_sets is not None:

        i = 0
        while i < len(index_sets['index_sets']):
            index_set = index_sets['index_sets'][i]
            if title == index_set['title']:
                id = index_set['id']
                break
            i += 1

    return id


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
            action=dict(type='str', required=False, default='list', choices=['create', 'update', 'delete', 'list', 'query_index_sets']),
            title=dict(type='str'),
            description=dict(type='str'),
            creation_date=dict(type='str', required=False, default=datetime.datetime.utcnow().isoformat() + 'Z'),
            id=dict(type='str'),
            index_prefix=dict(type='str'),
            index_analyzer=dict(type='str', default="standard"),
            shards=dict(type='int', default=4),
            replicas=dict(type='int', default=1),
            field_type_refresh_interval=dict(type='int', default=5000),
            rotation_strategy_class=dict(type='str',
                                         default='org.graylog2.indexer.rotation.strategies.TimeBasedRotationStrategy'),
            retention_strategy_class=dict(type='str', default='org.graylog2.indexer.retention.strategies.DeletionRetentionStrategy'),
            rotation_strategy=dict(type='dict', default=dict(type='org.graylog2.indexer.rotation.strategies.TimeBasedRotationStrategyConfig',
                                   rotation_period='P1D')),
            retention_strategy=dict(type='dict', default=dict(type='org.graylog2.indexer.retention.strategies.DeletionRetentionStrategyConfig',
                                    max_number_of_indices=14)),
            index_optimization_max_num_segments=dict(type='int', default=1),
            index_optimization_disabled=dict(type='bool', default=False),
            writable=dict(type='bool', default=True),
            default=dict(type='bool', default=False)
        )
    )

    endpoint = module.params['endpoint']
    graylog_user = module.params['graylog_user']
    graylog_password = module.params['graylog_password']
    action = module.params['action']
    title = module.params['title']
    id = module.params['id']
    creation_date = datetime.datetime.utcnow().isoformat() + 'Z'

    base_url = "https://%s/api/system/indices/index_sets" % (endpoint)

    api_token = get_token(module, endpoint, graylog_user, graylog_password)
    headers = '{ "Content-Type": "application/json", "X-Requested-By": "Graylog API", "Accept": "application/json", \
                "Authorization": "Basic ' + api_token.decode() + '" }'

    if action == "create":
        status, message, content, url = create(module, base_url, headers, creation_date)
    elif action == "update":
        status, message, content, url = update(module, base_url, headers)
    elif action == "delete":
        status, message, content, url = delete(module, base_url, headers, id)
    elif action == "list":
        status, message, content, url = list(module, base_url, headers, id)
    elif action == "query_index_sets":
        id = query_index_sets(module, base_url, headers, title)
        status, message, content, url = list(module, base_url, headers, id)

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
