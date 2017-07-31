#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2012, Jim Richardson <weaselkeeper@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: pushover
version_added: "2.0"
short_description: Send notifications via U(https://pushover.net)
description:
   - Send notifications via pushover, to subscriber list of devices, and email
     addresses. Requires pushover app on devices.
notes:
   - You will require a pushover.net account to use this module. But no account
     is required to receive messages.
options:
  msg:
    description:
      - What message you wish to send.
    required: true
  app_token:
    description:
      - Pushover issued token identifying your pushover app.
    required: true
  user_key:
    description:
      - Pushover issued authentication key for your user.
    required: true
  pri:
    description:
      - Message priority (see U(https://pushover.net) for details.)
    required: false

author: "Jim Richardson (@weaselkeeper)"
'''

EXAMPLES = '''
- pushover:
    msg: '{{ inventory_hostname }} has exploded in flames, It is now time to panic'
    app_token: wxfdksl
    user_key: baa5fe97f2c5ab3ca8f0bb59
  delegate_to: localhost
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils.urls import fetch_url


class Pushover(object):
    ''' Instantiates a pushover object, use it to send notifications '''
    base_uri = 'https://api.pushover.net'

    def __init__(self, module, user, token):
        self.module = module
        self.user = user
        self.token = token

    def run(self, priority, msg):
        ''' Do, whatever it is, we do. '''

        url = '%s/1/messages.json' % (self.base_uri)

        # parse config
        options = dict(user=self.user,
                token=self.token,
                priority=priority,
                message=msg)
        data = urlencode(options)

        headers = { "Content-type": "application/x-www-form-urlencoded"}
        r, info = fetch_url(self.module, url, method='POST', data=data, headers=headers)
        if info['status'] != 200:
            raise Exception(info)

        return r.read()


def main():

    module = AnsibleModule(
        argument_spec=dict(
            msg=dict(required=True),
            app_token=dict(required=True, no_log=True),
            user_key=dict(required=True, no_log=True),
            pri=dict(required=False, default='0', choices=['-2','-1','0','1','2']),
        ),
    )

    msg_object = Pushover(module, module.params['user_key'], module.params['app_token'])
    try:
        response = msg_object.run(module.params['pri'], module.params['msg'])
    except:
        module.fail_json(msg='Unable to send msg via pushover')

    module.exit_json(msg='message sent successfully: %s' % response, changed=False)


if __name__ == '__main__':
    main()
