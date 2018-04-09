#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2015, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ipify_facts
short_description: Retrieve the public IP of your internet gateway.
description:
  - If behind NAT and need to know the public IP of your internet gateway.
version_added: '2.0'
author: "René Moser (@resmo)"
options:
  api_url:
    description:
      - URL of the ipify.org API service.
      - C(?format=json) will be appended per default.
    required: false
    default: 'https://api.ipify.org'
  timeout:
    description:
      - HTTP connection timeout in seconds.
    required: false
    default: 10
    version_added: "2.3"
  validate_certs:
    description:
      - When set to C(NO), SSL certificates will not be validated.
    required: false
    default: "yes"
    version_added: "2.4"
notes:
  - "Visit https://www.ipify.org to get more information."
'''

EXAMPLES = '''
# Gather IP facts from ipify.org
- name: get my public IP
  ipify_facts:

# Gather IP facts from your own ipify service endpoint with a custom timeout
- name: get my public IP
  ipify_facts:
    api_url: http://api.example.com/ipify
    timeout: 20
'''

RETURN = '''
---
ipify_public_ip:
  description: Public IP of the internet gateway.
  returned: success
  type: string
  sample: 1.2.3.4
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_text


class IpifyFacts(object):

    def __init__(self):
        self.api_url = module.params.get('api_url')
        self.timeout = module.params.get('timeout')

    def run(self):
        result = {
            'ipify_public_ip': None
        }
        (response, info) = fetch_url(module=module, url=self.api_url + "?format=json", force=True, timeout=self.timeout)

        if not response:
            module.fail_json(msg="No valid or no response from url %s within %s seconds (timeout)" % (self.api_url, self.timeout))

        data = json.loads(to_text(response.read()))
        result['ipify_public_ip'] = data.get('ip')
        return result


def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            api_url=dict(default='https://api.ipify.org/'),
            timeout=dict(type='int', default=10),
            validate_certs=dict(type='bool', default=True),
        ),
        supports_check_mode=True,
    )

    ipify_facts = IpifyFacts().run()
    ipify_facts_result = dict(changed=False, ansible_facts=ipify_facts)
    module.exit_json(**ipify_facts_result)


if __name__ == '__main__':
    main()
