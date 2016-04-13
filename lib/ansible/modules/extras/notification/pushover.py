#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2012, Jim Richardson <weaselkeeper@gmail.com>
# All rights reserved.
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

###

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
- local_action: pushover msg="{{inventory_hostname}} has exploded in flames,
  It is now time to panic" app_token=wxfdksl user_key=baa5fe97f2c5ab3ca8f0bb59
'''

import urllib


class Pushover(object):
    ''' Instantiates a pushover object, use it to send notifications '''
    base_uri = 'https://api.pushover.net'
    port = 443

    def __init__(self, module, user, token):
        self.module = module
        self.user = user
        self.token = token

    def run(self, priority, msg):
        ''' Do, whatever it is, we do. '''

        url = '%s:%s/1/messages.json' % (self.base_uri, self.port)

        # parse config
        options = dict(user=self.user,
                token=self.token,
                priority=priority,
                message=msg)
        data = urllib.urlencode(options)

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

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
if __name__ == '__main__':
    main()
