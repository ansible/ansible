#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2013 Matt Coddington <coddington@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: flowdock
version_added: "1.2"
author: "Matt Coddington (@mcodd)"
short_description: Send a message to a flowdock
description:
   - Send a message to a flowdock team inbox or chat using the push API (see https://www.flowdock.com/api/team-inbox and https://www.flowdock.com/api/chat)
options:
  token:
    description:
      - API token.
    required: true
  type:
    description:
      - Whether to post to 'inbox' or 'chat'
    required: true
    choices: [ "inbox", "chat" ]
  msg:
    description:
      - Content of the message
    required: true
  tags:
    description:
      - tags of the message, separated by commas
    required: false
  external_user_name:
    description:
      - (chat only - required) Name of the "user" sending the message
    required: false
  from_address:
    description:
      - (inbox only - required) Email address of the message sender
    required: false
  source:
    description:
      - (inbox only - required) Human readable identifier of the application that uses the Flowdock API
    required: false
  subject:
    description:
      - (inbox only - required) Subject line of the message
    required: false
  from_name:
    description:
      - (inbox only) Name of the message sender
    required: false
  reply_to:
    description:
      - (inbox only) Email address for replies
    required: false
  project:
    description:
      - (inbox only) Human readable identifier for more detailed message categorization
    required: false
  link:
    description:
      - (inbox only) Link associated with the message. This will be used to link the message subject in Team Inbox.
    required: false
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used
        on personally controlled sites using self-signed certificates.
    required: false
    default: 'yes'
    choices: ['yes', 'no']
    version_added: 1.5.1

requirements: [ ]
'''

EXAMPLES = '''
- flowdock:
    type: inbox
    token: AAAAAA
    from_address: user@example.com
    source: my cool app
    msg: test from ansible
    subject: test subject

- flowdock:
    type: chat
    token: AAAAAA
    external_user_name: testuser
    msg: test from ansible
    tags: tag1,tag2,tag3
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils.urls import fetch_url


# ===========================================
# Module execution.
#

def main():

    module = AnsibleModule(
        argument_spec=dict(
            token=dict(required=True, no_log=True),
            msg=dict(required=True),
            type=dict(required=True, choices=["inbox","chat"]),
            external_user_name=dict(required=False),
            from_address=dict(required=False),
            source=dict(required=False),
            subject=dict(required=False),
            from_name=dict(required=False),
            reply_to=dict(required=False),
            project=dict(required=False),
            tags=dict(required=False),
            link=dict(required=False),
            validate_certs = dict(default='yes', type='bool'),
        ),
        supports_check_mode=True
    )

    type = module.params["type"]
    token = module.params["token"]
    if type == 'inbox':
        url = "https://api.flowdock.com/v1/messages/team_inbox/%s" % (token)
    else:
        url = "https://api.flowdock.com/v1/messages/chat/%s" % (token)

    params = {}

    # required params
    params['content'] = module.params["msg"]

    # required params for the 'chat' type
    if module.params['external_user_name']:
        if type == 'inbox':
            module.fail_json(msg="external_user_name is not valid for the 'inbox' type")
        else:
            params['external_user_name'] = module.params["external_user_name"]
    elif type == 'chat':
        module.fail_json(msg="external_user_name is required for the 'chat' type")

    # required params for the 'inbox' type
    for item in [ 'from_address', 'source', 'subject' ]:
        if module.params[item]:
            if type == 'chat':
                module.fail_json(msg="%s is not valid for the 'chat' type" % item)
            else:
                params[item] = module.params[item]
        elif type == 'inbox':
            module.fail_json(msg="%s is required for the 'inbox' type" % item)

    # optional params
    if module.params["tags"]:
        params['tags'] = module.params["tags"]

    # optional params for the 'inbox' type
    for item in [ 'from_name', 'reply_to', 'project', 'link' ]:
        if module.params[item]:
            if type == 'chat':
                module.fail_json(msg="%s is not valid for the 'chat' type" % item)
            else:
                params[item] = module.params[item]

    # If we're in check mode, just exit pretending like we succeeded
    if module.check_mode:
        module.exit_json(changed=False)

    # Send the data to Flowdock
    data = urlencode(params)
    response, info = fetch_url(module, url, data=data)
    if info['status'] != 200:
        module.fail_json(msg="unable to send msg: %s" % info['msg'])

    module.exit_json(changed=True, msg=module.params["msg"])


if __name__ == '__main__':
    main()
