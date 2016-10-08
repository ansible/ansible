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
module: grove
version_added: 1.4
short_description: Sends a notification to a grove.io channel
description:
     - The M(grove) module sends a message for a service to a Grove.io
       channel.
options:
  channel_token:
    description:
      - Token of the channel to post to.
    required: true
  service:
    description:
      - Name of the service (displayed as the "user" in the message)
    required: false
    default: ansible
  message:
    description:
      - Message content
    required: true
  url:
    description:
      - Service URL for the web client
    required: false
  icon_url:
    description:
      -  Icon for the service
    required: false
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used
        on personally controlled sites using self-signed certificates.
    required: false
    default: 'yes'
    choices: ['yes', 'no']
    version_added: 1.5.1
author: "Jonas Pfenniger (@zimbatm)"
'''

EXAMPLES = '''
- grove: >
    channel_token=6Ph62VBBJOccmtTPZbubiPzdrhipZXtg
    service=my-app
    message=deployed {{ target }}
'''

import urllib

BASE_URL = 'https://grove.io/api/notice/%s/'

# ==============================================================
# do_notify_grove

def do_notify_grove(module, channel_token, service, message, url=None, icon_url=None):
    my_url = BASE_URL % (channel_token,)

    my_data = dict(service=service, message=message)
    if url is not None:
        my_data['url'] = url
    if icon_url is not None:
        my_data['icon_url'] = icon_url

    data = urllib.urlencode(my_data)
    response, info = fetch_url(module, my_url, data=data)
    if info['status'] != 200:
        module.fail_json(msg="failed to send notification: %s" % info['msg'])

# ==============================================================
# main

def main():
    module = AnsibleModule(
        argument_spec = dict(
            channel_token = dict(type='str', required=True, no_log=True),
            message = dict(type='str', required=True),
            service = dict(type='str', default='ansible'),
            url = dict(type='str', default=None),
            icon_url = dict(type='str', default=None),
            validate_certs = dict(default='yes', type='bool'),
        )
    )

    channel_token = module.params['channel_token']
    service = module.params['service']
    message = module.params['message']
    url = module.params['url']
    icon_url = module.params['icon_url']

    do_notify_grove(module, channel_token, service, message, url, icon_url)

    # Mission complete
    module.exit_json(msg="OK")

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
main()
