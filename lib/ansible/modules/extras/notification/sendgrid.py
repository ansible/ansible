#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Matt Makai <matthew.makai@gmail.com>
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
version_added: "2.0"
module: sendgrid
short_description: Sends an email with the SendGrid API
description:
   - "Sends an email with a SendGrid account through their API, not through
     the SMTP service."
notes:
   - "This module is non-idempotent because it sends an email through the
     external API. It is idempotent only in the case that the module fails."
   - "Like the other notification modules, this one requires an external
     dependency to work. In this case, you'll need an active SendGrid
     account."
options:
  username:
    description:
      - username for logging into the SendGrid account
    required: true
  password:
    description: 
      - password that corresponds to the username
    required: true
  from_address:
    description:
      - the address in the "from" field for the email
    required: true
  to_addresses:
    description:
      - a list with one or more recipient email addresses
    required: true
  subject:
    description:
      - the desired subject for the email
    required: true

author: "Matt Makai (@makaimc)"
'''

EXAMPLES = '''
# send an email to a single recipient that the deployment was successful
- sendgrid:
    username: "{{ sendgrid_username }}"
    password: "{{ sendgrid_password }}"
    from_address: "ansible@mycompany.com"
    to_addresses:
      - "ops@mycompany.com"
    subject: "Deployment success."
    body: "The most recent Ansible deployment was successful."
  delegate_to: localhost

# send an email to more than one recipient that the build failed
- sendgrid
      username: "{{ sendgrid_username }}"
      password: "{{ sendgrid_password }}"
      from_address: "build@mycompany.com"
      to_addresses:
        - "ops@mycompany.com"
        - "devteam@mycompany.com"
      subject: "Build failure!."
      body: "Unable to pull source repository from Git server."
  delegate_to: localhost
'''

# =======================================
# sendgrid module support methods
#
import urllib

def post_sendgrid_api(module, username, password, from_address, to_addresses,
        subject, body):
    SENDGRID_URI = "https://api.sendgrid.com/api/mail.send.json"
    AGENT = "Ansible"
    data = {'api_user': username, 'api_key':password,
            'from':from_address, 'subject': subject, 'text': body}
    encoded_data = urllib.urlencode(data)
    to_addresses_api = ''
    for recipient in to_addresses:
        if isinstance(recipient, unicode):
            recipient = recipient.encode('utf-8')
        to_addresses_api += '&to[]=%s' % recipient
    encoded_data += to_addresses_api

    headers = { 'User-Agent': AGENT,
            'Content-type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'}
    return fetch_url(module, SENDGRID_URI, data=encoded_data, headers=headers, method='POST')


# =======================================
# Main
#

def main():
    module = AnsibleModule(
        argument_spec=dict(
            username=dict(required=True),
            password=dict(required=True, no_log=True),
            from_address=dict(required=True),
            to_addresses=dict(required=True, type='list'),
            subject=dict(required=True),
            body=dict(required=True),
        ),
        supports_check_mode=True
    )

    username = module.params['username']
    password = module.params['password']
    from_address = module.params['from_address']
    to_addresses = module.params['to_addresses']
    subject = module.params['subject']
    body = module.params['body']

    response, info = post_sendgrid_api(module, username, password,
        from_address, to_addresses, subject, body)
    if info['status'] != 200:
        module.fail_json(msg="unable to send email through SendGrid API: %s" % info['msg'])


    module.exit_json(msg=subject, changed=False)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *
if __name__ == '__main__':
    main()
