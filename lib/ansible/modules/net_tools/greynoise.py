#!/usr/bin/python
# (c) 2019, Whitney Champion <whitney.ellis.champion@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: greynoise
short_description: Communicate with the GreyNoise API
description:
    - The GreyNoise module queries the GreyNoise API
version_added: "1.0"
author: "Whitney Champion (@shortstack)"
options:
  action:
    description:
      - Action to take against GreyNoise API.
    required: true
    default: list_tags
    choices: [ query_ip, query_tag, list_tags ]
  ip:
    description:
      - IP to query.
    required: true
    default: None
  tag:
    description:
      - Tag to query.
    required: true
    default: None
  greynoise_api_key:
    description:
      - GreyNoise API key
    required: false
    default: None
'''

EXAMPLES = '''
# List all tags available
- greynoise:
    action: list_tags

# Query all tags associated with a given IP
- greynoise:
    action: query_ip
    ip: "8.8.8.8"
    greynoise_api_key: "<API_KEY>"

# Query all IPs that have a given tag
- greynoise:
    action: query_tag
    ip: "SHODAN"
    greynoise_api_key: "<API_KEY>"
'''

RETURN = r'''
json:
  description: The JSON response from the GreyNoise API
  returned: always
  type: complex
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


def list_tags(module, base_url):

    url = base_url + "list"

    response, info = fetch_url(module=module, url=url, method='GET')

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = response.read()
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def query_ip(module, base_url, ip, greynoise_api_key):

    url = base_url + "ip"

    data = 'key=%s&ip=%s' % (greynoise_api_key, ip)

    response, info = fetch_url(module=module, url=url, method='POST', data=data)

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = response.read()
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def query_tag(module, base_url, tag, greynoise_api_key):

    url = base_url + "tag"

    data = 'key=%s&tag=%s' % (greynoise_api_key, tag)

    response, info = fetch_url(module=module, url=url, method='POST', data=data)

    if info['status'] != 200:
        module.fail_json(msg="Fail: %s" % ("Status: " + str(info['msg']) + ", Message: " + str(info['body'])))

    try:
        content = response.read()
    except AttributeError:
        content = info.pop('body', '')

    return info['status'], info['msg'], content, url


def main():
    module = AnsibleModule(
        argument_spec=dict(
            action=dict(type='str', required=False, default='list_tags', choices=['query_ip', 'query_tag', 'list_tags']),
            ip=dict(type='str', default=None),
            tag=dict(type='str', default=None),
            greynoise_api_key=dict(type='str', default=None, no_log=True)
        )
    )

    action = module.params['action']
    ip = module.params['ip']
    tag = module.params['tag']
    greynoise_api_key = module.params['greynoise_api_key']

    base_url = "http://api.greynoise.io:8888/v1/query/"

    if action == "query_ip":
        status, message, content, url = query_ip(module, base_url, ip, greynoise_api_key)
    elif action == "query_tag":
        status, message, content, url = query_tag(module, base_url, tag, greynoise_api_key)
    elif action == "list_tags":
        status, message, content, url = list_tags(module, base_url)

    uresp = {}
    content = to_text(content, encoding='UTF-8')

    try:
        js = json.loads(content)
    except ValueError, e:
        js = ""

    uresp['status'] = status
    uresp['msg'] = message
    uresp['json'] = js
    uresp['url'] = url

    module.exit_json(**uresp)


# import module snippets
import json
import base64
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *


if __name__ == '__main__':
    main()
