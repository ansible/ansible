#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Jonathan Mainguy <jon@soh.re>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# basis of code taken from the ansible twillio and nexmo modules

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: catapult
version_added: 2.4
short_description: Send a sms / mms using the catapult bandwidth api
description:
     - Allows notifications to be sent using sms / mms via the catapult bandwidth api.
options:
  src:
    description:
      - One of your catapult telephone numbers the message should come from (must be in E.164 format, like C(+19195551212)).
    required: true
    default: null
  dest:
    description:
      - The phone number or numbers the message should be sent to (must be in E.164 format, like C(+19195551212)).
    required: true
    default: null
  msg:
    description:
      - The contents of the text message (must be 2048 characters or less).
    required: true
    default: null
  media:
    description:
      - For MMS messages, a media url to the location of the media to be sent with the message.
  user_id:
    description:
      - User Id from Api account page.
    required: true
    default: null
  api_token:
    description:
      - Api Token from Api account page.
    required: true
    default: null
  api_secret:
    description:
      - Api Secret from Api account page.
    required: true
    default: null

author: "Jonathan Mainguy (@Jmainguy)"
notes:
    - Will return changed even if the media url is wrong.
    - Will return changed if the destination number is invalid.

'''

EXAMPLES = '''
- name: Send a mms to multiple users
  catapult:
    src: "+15035555555"
    dest:
      - "+12525089000"
      - "+12018994225"
    media: "http://example.com/foobar.jpg"
    msg: "Task is complete"
    user_id: "{{ user_id }}"
    api_token: "{{ api_token }}"
    api_secret: "{{ api_secret }}"

- name: Send a sms to a single user
  catapult:
    src: "+15035555555"
    dest: "+12018994225"
    msg: "Consider yourself notified"
    user_id: "{{ user_id }}"
    api_token: "{{ api_token }}"
    api_secret: "{{ api_secret }}"

'''

RETURN = '''
changed:
    description: Whether the api accepted the message.
    returned: always
    type: boolean
    sample: True
'''


import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


def send(module, src, dest, msg, media, user_id, api_token, api_secret):
    """
    Send the message
    """
    AGENT = "Ansible"
    URI = "https://api.catapult.inetwork.com/v1/users/%s/messages" % user_id
    data = {'from': src, 'to': dest, 'text': msg}
    if media:
        data['media'] = media

    headers = {'User-Agent': AGENT, 'Content-type': 'application/json'}

    # Hack module params to have the Basic auth params that fetch_url expects
    module.params['url_username'] = api_token.replace('\n', '')
    module.params['url_password'] = api_secret.replace('\n', '')

    return fetch_url(module, URI, data=json.dumps(data), headers=headers, method="post")


def main():
    module = AnsibleModule(
        argument_spec=dict(
            src=dict(required=True),
            dest=dict(required=True, type='list'),
            msg=dict(required=True),
            user_id=dict(required=True),
            api_token=dict(required=True, no_log=True),
            api_secret=dict(required=True, no_log=True),
            media=dict(default=None, required=False),
        ),
    )

    src = module.params['src']
    dest = module.params['dest']
    msg = module.params['msg']
    media = module.params['media']
    user_id = module.params['user_id']
    api_token = module.params['api_token']
    api_secret = module.params['api_secret']

    for number in dest:
        rc, info = send(module, src, number, msg, media, user_id, api_token, api_secret)
        if info["status"] != 201:
            body = json.loads(info["body"])
            fail_msg = body["message"]
            module.fail_json(msg=fail_msg)

    changed = True
    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
