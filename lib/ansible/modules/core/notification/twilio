#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Matt Makai <matthew.makai@gmail.com>
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
version_added: "1.6"
module: twilio
short_description: Sends a text message to a mobile phone through Twilio.
description:
   - Sends a text message to a phone number through an the Twilio SMS service. 
notes:
   - Like the other notification modules, this one requires an external 
     dependency to work. In this case, you'll need a Twilio account with
     a purchased or verified phone number to send the text message.
options:
  account_sid:
    description:
      user's account id for Twilio found on the account page
    required: true
  auth_token:
    description: user's authentication token for Twilio found on the account page
    required: true
  msg:
    description:
      the body of the text message
    required: true
  to_number:
    description:
      what phone number to send the text message to, format +15551112222
    required: true
  from_number:
    description:
      what phone number to send the text message from, format +15551112222
    required: true
  
requirements: [ urllib, urllib2 ]
author: Matt Makai
'''

EXAMPLES = '''
# send a text message from the local server about the build status to (555) 303 5681
# note: you have to have purchased the 'from_number' on your Twilio account
- local_action: text msg="All servers with webserver role are now configured." 
  account_sid={{ twilio_account_sid }}
  auth_token={{ twilio_auth_token }}
  from_number=+15552014545 to_number=+15553035681

# send a text message from a server to (555) 111 3232
# note: you have to have purchased the 'from_number' on your Twilio account
- text: msg="This server's configuration is now complete."
  account_sid={{ twilio_account_sid }}
  auth_token={{ twilio_auth_token }}
  from_number=+15553258899 to_number=+15551113232
  
'''

# =======================================
# text module support methods
#
try:
    import urllib, urllib2
except ImportError:
    module.fail_json(msg="urllib and urllib2 are required")

import base64


def post_text(module, account_sid, auth_token, msg, from_number, to_number):
    URI = "https://api.twilio.com/2010-04-01/Accounts/%s/Messages.json" \
        % (account_sid,)
    AGENT = "Ansible/1.5"

    data = {'From':from_number, 'To':to_number, 'Body':msg}
    encoded_data = urllib.urlencode(data)
    request = urllib2.Request(URI)
    base64string = base64.encodestring('%s:%s' % \
        (account_sid, auth_token)).replace('\n', '')
    request.add_header('User-Agent', AGENT)
    request.add_header('Content-type', 'application/x-www-form-urlencoded')
    request.add_header('Accept', 'application/ansible')
    request.add_header('Authorization', 'Basic %s' % base64string)
    return urllib2.urlopen(request, encoded_data)


# =======================================
# Main
#

def main():

    module = AnsibleModule(
        argument_spec=dict(
            account_sid=dict(required=True),
            auth_token=dict(required=True),
            msg=dict(required=True),
            from_number=dict(required=True),
            to_number=dict(required=True),
        ),
        supports_check_mode=True
    )
  
    account_sid = module.params['account_sid']
    auth_token = module.params['auth_token']
    msg = module.params['msg']
    from_number = module.params['from_number']
    to_number = module.params['to_number']

    try:
        response = post_text(module, account_sid, auth_token, msg, 
            from_number, to_number)
    except Exception, e:
        module.fail_json(msg="unable to send text message to %s" % to_number)

    module.exit_json(msg=msg, changed=False) 

# import module snippets
from ansible.module_utils.basic import *
main()
