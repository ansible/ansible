#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Billy Kimble <basslines@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
module: hall
short_description: Send notification to Hall
description:
    - "The C(hall) module connects to the U(https://hall.com) messaging API and allows you to deliver notication messages to rooms."
version_added: "2.0"
author: Billy Kimble (@bkimble) <basslines@gmail.com>
options:
  room_token:
    description:
      - "Room token provided to you by setting up the Ansible room integation on U(https://hall.com)"
    required: true
  msg:
    description:
      - The message you wish to deliver as a notification
    required: true
  title:
    description:
      - The title of the message
    required: true
  picture:
    description:
      - >
        The full URL to the image you wish to use for the Icon of the message. Defaults to
        U(http://cdn2.hubspot.net/hub/330046/file-769078210-png/Official_Logos/ansible_logo_black_square_small.png?t=1421076128627)
    required: false
"""

EXAMPLES = """
- name: Send Hall notifiation
  hall:
    room_token: <hall room integration token>
    title: Nginx
    msg: 'Created virtual host file on {{ inventory_hostname }}'
  delegate_to: loclahost

- name: Send Hall notification if EC2 servers were created.
  hall:
    room_token: <hall room integration token>
    title: Server Creation
    msg: 'Created instance {{ item.id }} of type {{ item.instance_type }}.\\nInstance can be reached at {{ item.public_ip }} in the {{ item.region }} region.'
  delegate_to: loclahost
  when: ec2.instances|length > 0
  with_items: '{{ ec2.instances }}'
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


HALL_API_ENDPOINT = 'https://hall.com/api/1/services/generic/%s'


def send_request_to_hall(module, room_token, payload):
    headers = {'Content-Type': 'application/json'}
    payload = module.jsonify(payload)
    api_endpoint = HALL_API_ENDPOINT % (room_token)
    response, info = fetch_url(module, api_endpoint, data=payload, headers=headers)
    if info['status'] != 200:
        secure_url = HALL_API_ENDPOINT % ('[redacted]')
        module.fail_json(msg=" failed to send %s to %s: %s" % (payload, secure_url, info['msg']))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            room_token=dict(type='str', required=True),
            msg=dict(type='str', required=True),
            title=dict(type='str', required=True),
            picture=dict(type='str',
                         default='http://cdn2.hubspot.net/hub/330046/file-769078210-png/Official_Logos/ansible_logo_black_square_small.png?t=1421076128627'),
        )
    )

    room_token = module.params['room_token']
    message = module.params['msg']
    title = module.params['title']
    picture = module.params['picture']
    payload = {'title': title, 'message': message, 'picture': picture}
    send_request_to_hall(module, room_token, payload)
    module.exit_json(msg="OK")


if __name__ == '__main__':
    main()
