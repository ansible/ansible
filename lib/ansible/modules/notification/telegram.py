#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Artem Feofanov <artem.feofanov@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """

module: telegram
version_added: "2.2"
author: "Artem Feofanov (@tyouxa)"

short_description: module for sending notifications via telegram

description:
    - Send notifications via telegram bot, to a verified group or user
notes:
    - You will require a telegram account and create telegram bot to use this module.
options:
  msg:
    description:
      - What message you wish to send.
    required: true
  msg_format:
    description:
      - Message format. Formatting options `markdown` and `html` described in
        Telegram API docs (https://core.telegram.org/bots/api#formatting-options).
        If option `plain` set, message will not be formatted.
    default: plain
    choices: [ "plain", "markdown", "html" ]
    version_added: "2.4"
  token:
    description:
      - Token identifying your telegram bot.
    required: true
  chat_id:
    description:
      - Telegram group or user chat_id
    required: true

"""

EXAMPLES = """

- name: send a message to chat in playbook
  telegram:
    token: '9999999:XXXXXXXXXXXXXXXXXXXXXXX'
    chat_id: 000000
    msg: Ansible task finished
"""

RETURN = """

msg:
  description: The message you attempted to send
  returned: success
  type: string
  sample: "Ansible task finished"
telegram_error:
  description: Error message gotten from Telegram API
  returned: failure
  type: string
  sample: "Bad Request: message text is empty"
"""

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.parse import quote
from ansible.module_utils.urls import fetch_url


def main():

    module = AnsibleModule(
        argument_spec=dict(
            token=dict(type='str', required=True, no_log=True),
            chat_id=dict(type='str', required=True, no_log=True),
            msg_format=dict(type='str', required=False, default='plain',
                            choices=['plain', 'markdown', 'html']),
            msg=dict(type='str', required=True)),
        supports_check_mode=True
    )

    token = quote(module.params.get('token'))
    chat_id = quote(module.params.get('chat_id'))
    msg_format = quote(module.params.get('msg_format'))
    msg = quote(module.params.get('msg'))

    url = 'https://api.telegram.org/bot' + token + \
        '/sendMessage?text=' + msg + '&chat_id=' + chat_id
    if msg_format in ('markdown', 'html'):
        url += '&parse_mode=' + msg_format

    if module.check_mode:
        module.exit_json(changed=False)

    response, info = fetch_url(module, url)
    if info['status'] == 200:
        module.exit_json(changed=True)
    else:
        body = json.loads(info['body'])
        module.fail_json(msg="failed to send message, return status=%s" % str(info['status']),
                         telegram_error=body['description'])


if __name__ == '__main__':
    main()
