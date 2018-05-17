#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: typetalk
version_added: "1.6"
short_description: Send a message to typetalk
description:
  - Send a message to typetalk using typetalk API ( http://developers.typetalk.in/ )
options:
  client_id:
    description:
      - OAuth2 client ID
    required: true
  client_secret:
    description:
      - OAuth2 client secret
    required: true
  topic:
    description:
      - topic id to post message
    required: true
  msg:
    description:
      - message body
    required: true
requirements: [ json ]
author: "Takashi Someda (@tksmd)"
'''

EXAMPLES = '''
- typetalk:
    client_id: 12345
    client_secret: 12345
    topic: 1
    msg: install completed
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils.urls import fetch_url, ConnectionError


def do_request(module, url, params, headers=None):
    data = urlencode(params)
    if headers is None:
        headers = dict()
    headers = dict(headers, **{
        'User-Agent': 'Ansible/typetalk module',
    })
    r, info = fetch_url(module, url, data=data, headers=headers)
    if info['status'] != 200:
        exc = ConnectionError(info['msg'])
        exc.code = info['status']
        raise exc
    return r


def get_access_token(module, client_id, client_secret):
    params = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
        'scope': 'topic.post'
    }
    res = do_request(module, 'https://typetalk.in/oauth2/access_token', params)
    return json.load(res)['access_token']


def send_message(module, client_id, client_secret, topic, msg):
    """
    send message to typetalk
    """
    try:
        access_token = get_access_token(module, client_id, client_secret)
        url = 'https://typetalk.in/api/v1/topics/%d' % topic
        headers = {
            'Authorization': 'Bearer %s' % access_token,
        }
        do_request(module, url, {'message': msg}, headers)
        return True, {'access_token': access_token}
    except ConnectionError as e:
        return False, e


def main():

    module = AnsibleModule(
        argument_spec=dict(
            client_id=dict(required=True),
            client_secret=dict(required=True, no_log=True),
            topic=dict(required=True, type='int'),
            msg=dict(required=True),
        ),
        supports_check_mode=False
    )

    if not json:
        module.fail_json(msg="json module is required")

    client_id = module.params["client_id"]
    client_secret = module.params["client_secret"]
    topic = module.params["topic"]
    msg = module.params["msg"]

    res, error = send_message(module, client_id, client_secret, topic, msg)
    if not res:
        module.fail_json(msg='fail to send message with response code %s' % error.code)

    module.exit_json(changed=True, topic=topic, msg=msg)


if __name__ == '__main__':
    main()
