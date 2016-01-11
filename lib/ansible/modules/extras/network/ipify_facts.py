#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2015, René Moser <mail@renemoser.net>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

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
notes:
  - "Visit https://www.ipify.org to get more information."
'''

EXAMPLES = '''
# Gather IP facts from ipify.org
- name: get my public IP
  ipify_facts:

# Gather IP facts from your own ipify service endpoint
- name: get my public IP
  ipify_facts: api_url=http://api.example.com/ipify
'''

RETURN = '''
---
ipify_public_ip:
  description: Public IP of the internet gateway.
  returned: success
  type: string
  sample: 1.2.3.4
'''

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        # Let snippet from module_utils/basic.py return a proper error in this case
        pass


class IpifyFacts(object):

    def __init__(self):
        self.api_url = module.params.get('api_url')

    def run(self):
        result = {
            'ipify_public_ip': None
        }
        (response, info) = fetch_url(module, self.api_url + "?format=json" , force=True)
        if response:
            data = json.loads(response.read())
            result['ipify_public_ip'] = data.get('ip')
        return result

def main():
    global module
    module = AnsibleModule(
        argument_spec = dict(
            api_url = dict(default='https://api.ipify.org'),
        ),
        supports_check_mode=True,
    )

    ipify_facts = IpifyFacts().run()
    ipify_facts_result = dict(changed=False, ansible_facts=ipify_facts)
    module.exit_json(**ipify_facts_result)

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
if __name__ == '__main__':
    main()
