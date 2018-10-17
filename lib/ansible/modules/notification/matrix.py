#!/usr/bin/python
# coding: utf-8

# (c) 2018, Jan Christian Grünhage <jan.christian@gruenhage.xyz>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
author: "Jan Christian Grünhage (@jcgruenhage)"
requirements: [ matrix-client ]
module: matrix
short_description: Send notifications to matrix
description:
    - This module sends html formatted notifications to matrix rooms.
version_added: "2.8"
options:
    msg_plain:
        description:
            - Plain text form of the message to send to matrix, usually markdown
        required: true
    msg_html:
        description:
            - HTML form of the message to send to matrix
        required: true
    room_id:
        description:
            - ID of the room to send the notification to
        required: true
    hs_url:
        description:
            - URL of the homeserver, where the CS-API is reachable
        required: true
    token:
        description:
            - Authentication token for the API call. If provided, user_id and password are not required
    user_id:
        description:
            - The user id of the user
    password:
        description:
            - The password to log in with
notes:
    - Requires matrix-client (python library) on the executing host.
'''

EXAMPLES = '''
# Send matrix notification with token
- matrix:
    msg_plain: "**hello world**"
    msg_html: "<b>hello world</b>"
    room_id: "!12345678:server.tld"
    hs_url: "https://matrix.org"
    token: "{{ matrix_auth_token }}"

# Send matrix notification with user_id and password
- matrix:
    msg_plain: "**hello world**"
    msg_html: "<b>hello world</b>"
    room_id: "!12345678:server.tld"
    hs_url: "https://matrix.org"
    user_id: "ansible_notification_bot"
    password: "{{ matrix_auth_password }}"
'''

RETURN = '''
'''
from ansible.module_utils.basic import AnsibleModule

try:
    from matrix_client.client import MatrixClient
except ImportError:
    matrix_found = False
else:
    matrix_found = True


def run_module():
    module_args = dict(
        msg_plain=dict(type='str', required=True),
        msg_html=dict(type='str', required=True),
        room_id=dict(type='str', required=True),
        hs_url=dict(type='str', required=True),
        token=dict(type='str', required=False),
        user_id=dict(type='str', required=False),
        password=dict(type='str', required=False),
    )

    result = dict(
        changed=False,
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if not matrix_found:
        module.fail_json(msg="Python 'matrix-client' module is required. Install via: $ pip install matrix-client")

    if module.check_mode:
        return result

    # create a client object
    client = MatrixClient(module.params['hs_url'])
    # try to log in with a password
    if module.params['password'] is not None:
        if module.params['user_id'] is None:
            module.fail_json(msg='If you specify a password, you also need to specify a user_id.', **result)
        else:
            client.login(module.params['user_id'], module.params['password'], sync=False)
    # use a token if password login isn't possible
    elif module.params['token'] is not None:
        client.api.token = module.params['token']
    else:
        module.fail_json(msg='You need to either specify a token, or a user_id and password.', **result)

    # make sure we are in a given room and return a room object for it
    room = client.join_room(module.params['room_id'])
    # send an html formatted messages
    room.send_html(module.params['msg_html'], module.params['msg_plain'])

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
