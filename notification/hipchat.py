#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
DOCUMENTATION = '''
---
module: hipchat
version_added: "1.2"
short_description: Send a message to hipchat.
description:
   - Send a message to hipchat
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
      - Name the message will appear be sent from. max 15 characters.
        Over 15, will be shorten.
    required: false
    default: Ansible
  msg:
    description:
      - The message body.
    required: true
    default: null
  color:
    description:
      - Background color for the message. Default is yellow.
    required: false
    default: yellow
    choices: [ "yellow", "red", "green", "purple", "gray", "random" ]
  msg_format:
    description:
      - message format. html or text. Default is text.
    required: false
    default: text
    choices: [ "text", "html" ]
  notify:
    description:
      - notify or not (change the tab color, play a sound, etc)
    required: false
    default: 'yes'
    choices: [ "yes", "no" ]
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used
        on personally controlled sites using self-signed certificates.
    required: false
    default: 'yes'
    choices: ['yes', 'no']
    version_added: 1.5.1
  api:
    description:
      - API url if using a self-hosted hipchat server. For hipchat api version 2 use C(/v2) path in URI
    required: false
    default: 'https://api.hipchat.com/v1'
    version_added: 1.6.0


requirements: [ ]
author: "WAKAYAMA Shirou (@shirou), BOURDEL Paul (@pb8226)"
'''

EXAMPLES = '''
- hipchat:  room=notify msg="Ansible task finished"

# Use Hipchat API version 2

- hipchat:
    api: "https://api.hipchat.com/v2/"
    token: OAUTH2_TOKEN
    room: notify
    msg: "Ansible task finished"
'''

# ===========================================
# HipChat module specific support methods.
#

import urllib

DEFAULT_URI = "https://api.hipchat.com/v1"

MSG_URI_V1 = "/rooms/message"

NOTIFY_URI_V2 = "/room/{id_or_name}/notification"

def send_msg_v1(module, token, room, msg_from, msg, msg_format='text',
             color='yellow', notify=False, api=MSG_URI_V1):
    '''sending message to hipchat v1 server'''
    print "Sending message to v1 server"

    params = {}
    params['room_id'] = room
    params['from'] = msg_from[:15]  # max length is 15
    params['message'] = msg
    params['message_format'] = msg_format
    params['color'] = color
    params['api'] = api
    params['notify'] = int(notify)

    url = api + MSG_URI_V1 + "?auth_token=%s" % (token)
    data = urllib.urlencode(params)

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
    print "Sending message to v2 server"

    headers = {'Authorization':'Bearer %s' % token, 'Content-Type':'application/json'}

    body = dict()
    body['message'] = msg
    body['color'] = color
    body['message_format'] = msg_format
    body['notify'] = notify

    POST_URL = api + NOTIFY_URI_V2

    url = POST_URL.replace('{id_or_name}', room)
    data = json.dumps(body)

    if module.check_mode:
        # In check mode, exit before actually sending the message
        module.exit_json(changed=False)

    response, info = fetch_url(module, url, data=data, headers=headers, method='POST')
    if info['status'] == 200:
        return response.read()
    else:
        module.fail_json(msg="failed to send message, return status=%s" % str(info['status']))


# ===========================================
# Module execution.
#

def main():

    module = AnsibleModule(
        argument_spec=dict(
            token=dict(required=True),
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
    except Exception, e:
        module.fail_json(msg="unable to send msg: %s" % e)

    changed = True
    module.exit_json(changed=changed, room=room, msg_from=msg_from, msg=msg)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

main()
