#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Mateusz Kozieł <noname@localhost>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: smsapipl

short_description: Send SMS via smsapi.pl

version_added: "2.9"

description:
  - "Module to send SMS via smsapi.pl; it allow replace Polish diacritic chars to Latin alpha."

requirements:
  - "smsapi-client >= 2.3.0"

options:
  api_key:
    description:
      - API token generated for account on smsapi.pl
    required: true
    type: str
  state:
    description:
      - Action to do; check point on account or send SMS
    choices:
      - check
      - send
    type: str
  to:
    description:
      - Mobile of destination
    type: str
  from:
    description:
      - Information about sender, that same like in smsapi.pl
    type: str
  message:
    description:
      - Message to send
    type: str
  latin:
    description:
      - If True, Polish diacritic chars are replace by Latin chars
    default: true
    type: bool

author:
  - Mateusz Kozieł (@mateusz-koziel)
'''

EXAMPLES = '''
# check points
- name: Check available points on user's account
  smsapipl:
    api_key: <here-provide-your-api-token>
    state: check
# send sms
- name: Send SMS
  smsapipl:
    api_key: <here-provide-your-api-token>
    state: send
    to: <provide-consumer-number>
    from: <provide-sender-name-that-same-like-in-smsapi-or-leave-empty>
    message: <provide-message-content>
# fail send sms
- name: Send SMS
  smsapipl:
    api_key: <here-provide-your-api-token>
    state: send
'''

RETURN = ''' # '''


import unicodedata

from ansible.module_utils.basic import AnsibleModule

try:
    from smsapi.client import SmsApiPlClient
    from smsapi.exception import SendException
except ImportError:
    pass


def check_points(data):
    api_key = data['api_key']

    client = SmsApiPlClient(access_token=api_key)

    try:
        result = client.account.balance()
        return False, False, result.points
    except SendException:
        result = 'Something went wrong'
        return True, False, result


def send_sms(data):
    api_key = data['api_key']
    to_number = data['to']
    from_sender = data['from']
    message_ctx = data['message']
    latin_alpha = data['latin']

    if to_number == '':
        return True, False, 'Please provide number in TO field.'

    client = SmsApiPlClient(access_token=api_key)

    if latin_alpha:
        message_ctx = unicodedata.normalize('NFKD', message_ctx.decode('utf8')).replace(u'ł', 'l').replace(u'Ł', 'L').encode('ascii', 'ignore')

    if from_sender != '':
        client.sms.send(to=to_number, message=message_ctx, from_=from_sender)
    else:
        client.sms.send(to=to_number, message=message_ctx)

    return False, True, 'SMS has been sent.'


def main():

    fields = {
        'api_key': {'required': True, 'type': 'str'},
        'to': {'required': False, 'type': 'str'},
        'from': {'required': False, 'type': 'str', 'default': ''},
        'message': {'required': False, 'type': 'str'},
        'latin': {'required': False, 'type': 'bool', 'default': True},
        'state': {
            'default': None,
            'choices': ['check', 'send'],
            'type': 'str'
        },
    }

    choice_map = {
        None: check_points,
        'check': check_points,
        'send': send_sms
    }

    module = AnsibleModule(argument_spec=fields)
    is_error, has_changed, result = choice_map.get(
        module.params['state'])(module.params)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg='Exit code 1', meta=result)


if __name__ == '__main__':
    main()
