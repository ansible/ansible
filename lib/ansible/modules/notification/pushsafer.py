#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017, Kevin Siml > Pushsafer.com
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: pushsafer
version_added: "2.3"
short_description: Send notifications via U(https://www.pushsafer.com)
description:
   - Send notifications via pushsafer, to subscriber list of devices, and email
     addresses. Requires pushsafer app on devices.
notes:
   - You will require a pushsafer.com account to use this module.
options:
  msg:
    description:
      - What message you wish to send.
    required: true
  private_key:
    description:
      - Pushsafer private or alias key to identifying your pushsafer account.
    required: true
  device:
    description:
      - Device or Device group ID, if empty send to all registered devices (see U(https://www.pushsafer.com/en/pushapi) for details.)
    required: false
  icon:
    description:
      - Message icon (number 1-98, see U(https://www.pushsafer.com/en/pushapi) for details.)
    required: false
  sound:
    description:
      - Message sound (number 1-28, see U(https://www.pushsafer.com/en/pushapi) for details.)
    required: false
  vibration:
    description:
      - Message vibration (number 0-3, see U(https://www.pushsafer.com/en/pushapi) for details.)
    required: false
  url:
    description:
      - Message url (see U(https://www.pushsafer.com/en/pushapi) for details.)
    required: false
  urltitle:
    description:
      - Message url title (see U(https://www.pushsafer.com/en/pushapi) for details.)
    required: false
  time2live:
    description:
      - Time in minutes, after which message automatically gets purged (see U(https://www.pushsafer.com/en/pushapi) for details.)
    required: false

author: "Kevin Siml, Pushsafer.com"
'''

EXAMPLES = '''
- pushsafer:
    msg: '{{ inventory_hostname }} has exploded in flames, It is now time to panic'
    private_key: XXXXXXXXXXXXXXXXXXXX
  delegate_to: localhost
'''

import urllib


class Pushsafer(object):
    ''' Instantiates a pushsafer object, use it to send notifications '''
    base_uri = 'https://www.pushsafer.com'

    def __init__(self, module, privatekey):
        self.module = module
        self.privatekey = privatekey

    def run(self, device, icon, sound, vibration, url, urltitle, time2live, msg, title):
        ''' Do, whatever it is, we do. '''

        url = '%s/api' % (self.base_uri)

        # parse config
        options = dict(k=self.privatekey, d=device,i=icon, s=sound, v=vibration, u=url, ut=urltitle, l=time2live, m=msg, t=title)
        data = urllib.urlencode(options)

        headers = {"Content-type": "application/x-www-form-urlencoded"}
        r, info = fetch_url(self.module, url, method='POST', data=data, headers=headers)
        if info['status'] != 200:
            raise Exception(info)

        return r.read()


def main():

    module = AnsibleModule(
        argument_spec=dict(
            msg=dict(required=True),
            title=dict(required=False),
            private_key=dict(required=True, no_log=True),
            device=dict(required=False, default=''),
            icon=dict(required=False, default='1'),
            sound=dict(required=False, default=''),
            vibration=dict(required=False, default='0', choices=['0', '1', '2', '3']),
            url=dict(required=False, default=''),
            urltitle=dict(required=False, default=''),
            time2live=dict(required=False, default=''),
        ),
    )

    msg_object = Pushsafer(module, module.params['private_key'])
    try:
        response = msg_object.run(module.params['device'], module.params['icon'], module.params['sound'], module.params['vibration'],
                                  module.params['url'], module.params['urltitle'], module.params['msg'], module.params['title'])
    except:
        module.fail_json(msg='Unable to send msg via pushsafer')

    module.exit_json(msg='message sent successfully: %s' % response, changed=False)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
if __name__ == '__main__':
    main()
