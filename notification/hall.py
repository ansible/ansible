#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Billy Kimble <basslines@gmail.com>
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


DOCUMENTATION = """
module: hall
short_description: Send notification to Hall
description:
    - "The M(hall) module connects to the U(https://hall.com) messaging API and allows you to deliver notication messages to rooms."
version_added: "2.0"
author: Billy Kimble (@bkimble) <basslines@gmail.com>
options:
  room_token:
    description:
      - "Room token provided to you by setting up the Ansible room integation on U(https://hall.com)"
    required: true
  msg:
    description:
      - The message you wish to deliver as a notifcation
    required: true
  title:
    description:
      - The title of the message
    required: true
  picture:
    description:
      - "The full URL to the image you wish to use for the Icon of the message. Defaults to U(http://cdn2.hubspot.net/hub/330046/file-769078210-png/Official_Logos/ansible_logo_black_square_small.png?t=1421076128627)"
    required: false
"""

EXAMPLES = """
- name: Send Hall notifiation
  local_action:
    module: hall
    room_token: <hall room integration token>
    title: Nginx
    msg: Created virtual host file on {{ inventory_hostname }}

- name: Send Hall notification if EC2 servers were created.
  when: ec2.instances|length > 0
  local_action:
    module: hall
    room_token: <hall room integration token>
    title: Server Creation
    msg: "Created EC2 instance {{ item.id }} of type {{ item.instance_type }}.\\nInstance can be reached at {{ item.public_ip }} in the {{ item.region }} region."
  with_items: "{{ ec2.instances }}"
"""

HALL_API_ENDPOINT  = 'https://hall.com/api/1/services/generic/%s'

def send_request_to_hall(module, room_token, payload):
    headers = {'Content-Type': 'application/json'}
    payload=module.jsonify(payload)
    api_endpoint = HALL_API_ENDPOINT % (room_token)
    response, info = fetch_url(module, api_endpoint, data=payload, headers=headers)
    if info['status'] != 200:
        secure_url = HALL_API_ENDPOINT % ('[redacted]')
        module.fail_json(msg=" failed to send %s to %s: %s" % (payload, secure_url, info['msg']))

def main():
    module = AnsibleModule(
        argument_spec = dict(
            room_token  = dict(type='str', required=True),
            msg     = dict(type='str', required=True),
            title       = dict(type='str', required=True),
            picture     = dict(type='str', default='http://cdn2.hubspot.net/hub/330046/file-769078210-png/Official_Logos/ansible_logo_black_square_small.png?t=1421076128627'),
        )
    )

    room_token = module.params['room_token']
    message = module.params['msg']
    title = module.params['title']
    picture = module.params['picture']
    payload = {'title': title, 'message': message, 'picture': picture}
    send_request_to_hall(module, room_token, payload)
    module.exit_json(msg="OK")

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
main()
