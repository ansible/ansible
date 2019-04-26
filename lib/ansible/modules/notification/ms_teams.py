#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019, Christian Kaiser <c.kaiser () also.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ms_teams
version_added: 1.0
short_description: Send messages to a Microsoft Teams channel
author: Christian Kaiser (@ckaiser79)
description:
  - Setup a webhook in Microsoft Teams. Using this webhook you can send html
    notifications.
  - The module enabley you to write longer text in plain text or html,
    instead of sending direct json to the endpoint.
options:
  body:
    required: true
    description:
      - The content of the message to be published.
  subject:
    required: true
    description:
      - The title of the message.
  webhook:
    required: true
    description:
      - The ms teams configured webhook
  color:
    description:
      - Which color should be shown on the card. HTML code without a leading '#'
    default: ffffcc
notes:
  - "See: https://docs.microsoft.com/de-de/outlook/actionable-messages/message-card-reference"
'''

EXAMPLES = '''
- set_fact:
    body: "{{ lookup('template', 'teams-sample.html.j2') }}"
- ms_teams:
    body: "{{ body }}"
    webhook: https://outlook.office.com/webhook/...
    subject: Test
    color: dd1111
  register: result
- debug:
    var=result
    verbosity=1
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
import json
import os


def create_payload(body, subject, color):
    payload = {
        'text': body,
        'title': subject,
        'themeColor': color
    }
    return json.dumps(payload)


def post_to_msteams(module):

    payload = create_payload(module.params['body'],
                             module.params['subject'],
                             module.params['color'])

    if module.check_mode:
        changed = False
        failed = False
        meta = payload
    else:

        headers = {'Content-Type': 'application/json'}
        response, info = fetch_url(module=modulea,
                                   url=module.params['webhook'],
                                   headers=headers,
                                   method='POST',
                                   data=payload)

        if info['status'] != 200:
            changed = False
            failed = True
            meta = "failed to send %s: %s" % (payload, info['msg'])
        else:
            changed = True
            failed = False
            meta = "Message send."

    return (changed, failed, meta)


def main():

    fields = {
        "body": {"required": True, "type": "str"},
        "webhook": {"required": True, "type": "str"},
        "subject": {"required": True, "type": "str"},
        "color": {"default": "ffffcc", "type": "str"}
    }

    module = AnsibleModule(argument_spec=fields)

    changed, failed, meta = post_to_msteams(module)
    module.exit_json(changed=changed, meta=meta, failed=failed)


if __name__ == '__main__':
    main()
