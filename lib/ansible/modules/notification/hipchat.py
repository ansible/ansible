#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: hipchat
version_added: "1.2"
short_description: Send a message to Hipchat.
description:
   - Send a message to a Hipchat room, with options to control the formatting.
options:
  token:
    description:
      - API token.
    required: true
  room:
    description:
      - ID or name of the room.
    required: true
  from:
    description:
      - Name the message will appear to be sent from. Max length is 15
        characters - above this it will be truncated.
    default: Ansible
  msg:
    description:
      - The message body.
    required: true
  color:
    description:
      - Background color for the message.
    default: yellow
    choices: [ "yellow", "red", "green", "purple", "gray", "random" ]
  msg_format:
    description:
      - Message format.
    default: text
    choices: [ "text", "html" ]
  notify:
    description:
      - If true, a notification will be triggered for users in the room.
    type: bool
    default: 'yes'
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used
        on personally controlled sites using self-signed certificates.
    type: bool
    default: 'yes'
    version_added: 1.5.1
  api:
    description:
      - API url if using a self-hosted hipchat server. For Hipchat API version
        2 use the default URI with C(/v2) instead of C(/v1).
    default: 'https://api.hipchat.com/v1'
    version_added: 1.6.0

author: "WAKAYAMA Shirou (@shirou), BOURDEL Paul (@pb8226)"
'''

EXAMPLES = '''
- hipchat:
    room: notif
    msg: Ansible task finished

# Use Hipchat API version 2
- hipchat:
    api: https://api.hipchat.com/v2/
    token: OAUTH2_TOKEN
    room: notify
    msg: Ansible task finished
'''

# ===========================================
# HipChat module specific support methods.
#

import json
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils.six.moves.urllib.request import pathname2url
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import fetch_url


DEFAULT_URI = "https://api.hipchat.com/v1"

MSG_URI_V1 = "/rooms/message"

NOTIFY_URI_V2 = "/room/{id_or_name}/notification"


def send_msg_v1(module, token, room, msg_from, msg, msg_format='text',
                color='yellow', notify=False, api=MSG_URI_V1):
    '''sending message to hipchat v1 server'''

    params = {}
    params['room_id'] = room
    params['from'] = msg_from[:15]  # max length is 15
    params['message'] = msg
    params['message_format'] = msg_format
    params['color'] = color
    params['api'] = api
    params['notify'] = int(notify)

    url = api + MSG_URI_V1 + "?auth_token=%s" % (token)
    data = urlencode(params)

    if module.check_mode:
        # In check mode, exit before actually sending the message
        module.exit_json(changed=False)

    response, info = fetch_url(module, url, data=data)
    if info['status'] == 200:
        return response.read()
    else:
        module.fail_json(msg="failed to send message, return status=%s" % str(info['status']))


def send_msg_v2(module, token, room, msg_from, msg, msg_format='text',
                color='yellow', notify=False, api=NOTIFY_URI_V2):
    '''sending message to hipchat v2 server'''

    headers = {'Authorization': 'Bearer %s' % token, 'Content-Type': 'application/json'}

    body = dict()
    body['message'] = msg
    body['color'] = color
    body['message_format'] = msg_format
    body['notify'] = notify

    POST_URL = api + NOTIFY_URI_V2

    url = POST_URL.replace('{id_or_name}', pathname2url(room))
    data = json.dumps(body)

    if module.check_mode:
        # In check mode, exit before actually sending the message
        module.exit_json(changed=False)

    response, info = fetch_url(module, url, data=data, headers=headers, method='POST')

    # https://www.hipchat.com/docs/apiv2/method/send_room_notification shows
    # 204 to be the expected result code.
    if info['status'] in [200, 204]:
        return response.read()
    else:
        module.fail_json(msg="failed to send message, return status=%s" % str(info['status']))


# ===========================================
# Module execution.
#

def main():

    module = AnsibleModule(
        argument_spec=dict(
            token=dict(required=True, no_log=True),
            room=dict(required=True),
            msg=dict(required=True),
            msg_from=dict(default="Ansible", aliases=['from']),
            color=dict(default="yellow", choices=["yellow", "red", "green",
                                                  "purple", "gray", "random"]),
            msg_format=dict(default="text", choices=["text", "html"]),
            notify=dict(default=True, type='bool'),
            validate_certs=dict(default='yes', type='bool'),
            api=dict(default=DEFAULT_URI),
        ),
        supports_check_mode=True
    )

    token = module.params["token"]
    room = str(module.params["room"])
    msg = module.params["msg"]
    msg_from = module.params["msg_from"]
    color = module.params["color"]
    msg_format = module.params["msg_format"]
    notify = module.params["notify"]
    api = module.params["api"]

    try:
        if api.find('/v2') != -1:
            send_msg_v2(module, token, room, msg_from, msg, msg_format, color, notify, api)
        else:
            send_msg_v1(module, token, room, msg_from, msg, msg_format, color, notify, api)
    except Exception as e:
        module.fail_json(msg="unable to send msg: %s" % to_native(e), exception=traceback.format_exc())

    changed = True
    module.exit_json(changed=changed, room=room, msg_from=msg_from, msg=msg)


if __name__ == '__main__':
    main()
