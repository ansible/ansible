#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: grove
version_added: 1.4
short_description: Sends a notification to a grove.io channel
description:
     - The C(grove) module sends a message for a service to a Grove.io
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
    default: 'yes'
    type: bool
    version_added: 1.5.1
author: "Jonas Pfenniger (@zimbatm)"
'''

EXAMPLES = '''
- grove: >
    channel_token=6Ph62VBBJOccmtTPZbubiPzdrhipZXtg
    service=my-app
    message=deployed {{ target }}
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils.urls import fetch_url


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

    data = urlencode(my_data)
    response, info = fetch_url(module, my_url, data=data)
    if info['status'] != 200:
        module.fail_json(msg="failed to send notification: %s" % info['msg'])

# ==============================================================
# main


def main():
    module = AnsibleModule(
        argument_spec=dict(
            channel_token=dict(type='str', required=True, no_log=True),
            message=dict(type='str', required=True),
            service=dict(type='str', default='ansible'),
            url=dict(type='str', default=None),
            icon_url=dict(type='str', default=None),
            validate_certs=dict(default='yes', type='bool'),
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


if __name__ == '__main__':
    main()
