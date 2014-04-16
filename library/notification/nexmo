#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Matt Martz <matt@sivel.net>
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

DOCUMENTATION = """
module: nexmo
short_description: Send a SMS via nexmo
description:
    - Send a SMS message via nexmo
version_added: 1.6
author: Matt Martz
options:
  api_key:
    description:
      - Nexmo API Key
    required: true
  api_secret:
    description:
      - Nexmo API Secret
    required: true
  src:
    description:
       - Nexmo Number to send from
    required: true
  dest:
    description:
      - Phone number(s) to send SMS message to
    required: true
  msg:
    description:
      - Message to text to send. Messages longer than 160 characters will be
        split into multiple messages
    required: true
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used
        on personally controlled sites using self-signed certificates.
    required: false
    default: 'yes'
    choices:
      - 'yes'
      - 'no'
"""

EXAMPLES = """
- name: Send notification message via Nexmo
  local_action:
    module: nexmo
    api_key: 640c8a53
    api_secret: 0ce239a6
    src: 12345678901
    dest:
      - 10987654321
      - 16789012345
    msg: "{{ inventory_hostname }} completed"
"""


NEXMO_API = 'https://rest.nexmo.com/sms/json'


def send_msg(module):
    failed = list()
    responses = dict()
    msg = {
        'api_key': module.params.get('api_key'),
        'api_secret': module.params.get('api_secret'),
        'from': module.params.get('src'),
        'text': module.params.get('msg')
    }
    for number in module.params.get('dest'):
        msg['to'] = number
        url = "%s?%s" % (NEXMO_API, urllib.urlencode(msg))

        headers = dict(Accept='application/json')
        response, info = fetch_url(module, url, headers=headers)
        if info['status'] != 200:
            failed.append(number)
            responses[number] = dict(failed=True)

        try:
            responses[number] = json.load(response)
        except:
            failed.append(number)
            responses[number] = dict(failed=True)
        else:
            for message in responses[number]['messages']:
                if int(message['status']) != 0:
                    failed.append(number)
                    responses[number] = dict(failed=True, **responses[number])

        if failed:
            msg = 'One or messages failed to send'
        else:
            msg = ''

        module.exit_json(failed=bool(failed), msg=msg, changed=False,
                         responses=responses)


def main():
    argument_spec = url_argument_spec()
    argument_spec.update(
        dict(
            api_key=dict(required=True, no_log=True),
            api_secret=dict(required=True, no_log=True),
            src=dict(required=True, type='int'),
            dest=dict(required=True, type='list'),
            msg=dict(required=True),
        ),
    )

    module = AnsibleModule(
        argument_spec=argument_spec
    )

    send_msg(module)


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

main()
