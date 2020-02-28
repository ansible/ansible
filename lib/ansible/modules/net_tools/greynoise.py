#!/usr/bin/python
# Copyright: (c) 2019, Whitney Champion <whitney.ellis.champion@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: greynoise
short_description: Communicate with the GreyNoise API
description:
    - The GreyNoise module queries the GreyNoise API.
version_added: "2.8"
author: "Whitney Champion (@shortstack)"
options:
  action:
    description:
      - Action to take against GreyNoise API.
    required: false
    default: list_tags
    choices: [ query_ip, query_tag, list_tags ]
    type: str
  ip:
    description:
      - IP to query.
    required: false
    type: str
  tag:
    description:
      - Tag to query.
    required: false
    type: str
  greynoise_api_key:
    description:
      - GreyNoise API key
    required: false
    type: str
'''

EXAMPLES = '''
# List all tags available
- greynoise:
    action: list_tags

# Query all tags associated with a given IP
- greynoise:
    action: query_ip
    ip: "8.8.8.8"
    greynoise_api_key: "API_KEY"

# Query all IPs that have a given tag
- greynoise:
    action: query_tag
    ip: "SHODAN"
    greynoise_api_key: "API_KEY"
'''

RETURN = '''
json:
  description: The JSON response from the GreyNoise API
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
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url, to_text


def list_tags(module, base_url, headers):

    url = "/".join([base_url, "experimental/gnql?query=tags"])

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='GET')

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = to_text(response.read(), errors='surrogate_or_strict')
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def query_ip(module, base_url, ip, headers):

    url = "/".join([base_url, "experimental/gnql?query=ip:%s" % ip])

    response, info = fetch_url(module=module, headers=json.loads(headers), url=url, method='GET')

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = to_text(response.read(), errors='surrogate_or_strict')
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def query_tag(module, base_url, tag, headers):

    url = "/".join([base_url, "experimental/gnql?query=tags:%s" % tag])

    response, info = fetch_url(module=module, url=url, headers=json.loads(headers), method='GET')

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = to_text(response.read(), errors='surrogate_or_strict')
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def main():
    module = AnsibleModule(
        argument_spec=dict(
            action=dict(type='str', required=False, default='list_tags', choices=['query_ip', 'query_tag', 'list_tags']),
            ip=dict(type='str'),
            tag=dict(type='str'),
            greynoise_api_key=dict(type='str', no_log=True)
        )
    )

    action = module.params['action']
    ip = module.params['ip']
    tag = module.params['tag']
    greynoise_api_key = module.params['greynoise_api_key']

    base_url = "https://api.greynoise.io/v2"
    headers = '{ "Accept": "application/json", \
                "Key": "%s" }' % greynoise_api_key

    if action == "query_ip":
        status, message, content, url = query_ip(module, base_url, ip, headers)
    elif action == "query_tag":
        status, message, content, url = query_tag(module, base_url, tag, headers)
    elif action == "list_tags":
        status, message, content, url = list_tags(module, base_url, headers)

    uresp = {}
    content = to_text(content, encoding='UTF-8')

    try:
        js = json.loads(content)
    except ValueError:
        js = ""

    uresp['status'] = status
    uresp['msg'] = message
    uresp['json'] = js
    uresp['url'] = url

    module.exit_json(**uresp)


if __name__ == '__main__':
    main()
