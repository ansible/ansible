#!/usr/bin/python
# -*- coding: utf-8 -*-

# Benjamin Jolivot <bjolivot@gmail.com>
# Inspired by slack module :
#    # (c) 2017, Steve Pletcher <steve@steve-pletcher.com>
#    # (c) 2016, René Moser <mail@renemoser.net>
#    # (c) 2015, Stefan Berggren <nsg@nsg.cc>
#    # (c) 2014, Ramon de la Fuente <ramon@delafuente.nl>)

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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = """
module: mattermost
short_description: Send Mattermost notifications
description:
    - The C(mattermost) module sends notifications to U(http://your.mattermost.url) via the Incoming WebHook integration
version_added: "2.3"
author: "Benjamin Jolivot (@bjolivot)"
options:
  url:
    description:
      - Mattermost url (i.e. http://mattermost.yourcompany.com)
    required: true
  api_key:
    description:
      - Mattermost webhook api key. Log into your mattermost site, go to
        Menu -> Integration -> Incomming Webhook -> Add Incomming Webhook
        This will give you full URL. api_key is the last part.
        http://mattermost.example.com/hooks/C(API_KEY)
    required: true
  text:
    description:
      - Text to send. Note that the module does not handle escaping characters.
    required: true
  channel:
    description:
      - Channel to send the message to. If absent, the message goes to the channel selected for the I(api_key).
    default: None
  username:
    description:
      - This is the sender of the message (Username Override need to be enabled by mattermost admin, see mattermost doc, default C(Ansible)).
    required: false
    default: "Ansible"
  icon_url:
    description:
      - Url for the message sender's icon (default C(https://www.ansible.com/favicon.ico))
    required: false
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
- name: Send notification message via Mattermost
  mattermost:
    url: http://mattermost.example.com
    api_key: my_api_key
    text: '{{ inventory_hostname }} completed'

- name: Send notification message via Slack all options
  mattermost:
    url: http://mattermost.example.com
    api_key: my_api_key
    text: '{{ inventory_hostname }} completed'
    channel: notifications
    username: 'Ansible on {{ inventory_hostname }}'
    icon_url: http://www.example.com/some-image-file.png
"""

RETURN = '''
payload:
    description: Mattermost payload
    returned: success
    type: string
webhook_url:
    description: URL the webhook is sent to
    returned: success
    type: string
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url

def main():
    module = AnsibleModule(
        supports_check_mode=True,
        argument_spec = dict(
            url         = dict(type='str', required=True),
            api_key     = dict(type='str', required=True,  no_log=True),
            text        = dict(type='str', required=True),
            channel     = dict(type='str', default=None),
            username    = dict(type='str', default='Ansible'),
            icon_url    = dict(type='str', default='https://www.ansible.com/favicon.ico'),
            validate_certs = dict(default='yes', type='bool'),
        )
    )
    #init return dict
    result = dict(changed=False, msg="OK")

    #define webhook
    webhook_url = "{0}/hooks/{1}".format(module.params['url'],module.params['api_key'])
    result['webhook_url'] = webhook_url

    #define payload
    payload = { }
    for param in ['text', 'channel', 'username', 'icon_url']:
        if module.params[param] is not None:
            payload[param] = module.params[param]

    payload=module.jsonify(payload)
    result['payload'] = payload

    #http headers
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    #send request if not in test mode
    if module.check_mode is False:
        response, info = fetch_url(module=module, url=webhook_url, headers=headers, method='POST', data=payload)

        #somthing's wrong
        if info['status'] != 200:
            #some problem
            result['msg'] = "Failed to send mattermost message, the error was: {0}".format(info['msg'])
            module.fail_json(**result)

    #Looks good
    module.exit_json(**result)


if __name__ == '__main__':
    main()
