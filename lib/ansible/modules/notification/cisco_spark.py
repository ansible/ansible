#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cisco_spark
short_description: Send a message to a Cisco Webex Teams (formerly known as Cisco Spark) Room or Individual.
description:
    - Send a message to a Cisco Webex Teams (formerly known as Cisco Spark) Room or Individual with options to control the formatting.
version_added: "2.3"
author: Drew Rusell (@drew-russell)
notes:
  - The C(recipient_id) type must be valid for the supplied C(recipient_id).
  - Full API documentation can be found at U(https://developer.webex.com/docs/api/v1/messages/create-a-message).

options:

  recipient_type:
    description:
       - The request parameter you would like to send the message to.
       - Messages can be sent to either a room or individual (by ID or E-Mail).
    required: True
    choices: ['roomId', 'toPersonEmail', 'toPersonId']

  recipient_id:
    description:
      - The unique identifier associated with the supplied C(recipient_type).
    required: true

  message_type:
    description:
       - Specifies how you would like the message formatted.
    required: False
    default: text
    choices: ['text', 'markdown']

  personal_token:
    description:
      - Your personal access token required to validate the Spark API.
    required: true
    aliases: ['token']

  send_message:
    description:
      - The message you would like to send.
    required: True
'''

EXAMPLES = """
# Note: The following examples assume a variable file has been imported
# that contains the appropriate information.

- name: Cisco Webex Teams - Markdown Message to a Room
  cisco_spark:
    recipient_type: roomId
    recipient_id: "{{ room_id }}"
    message_type: markdown
    personal_token: "{{ token }}"
    send_message: "**Cisco Webex Teams Ansible Module - Room Message in Markdown**"

- name: Cisco Webex Teams - Text Message to a Room
  cisco_spark:
    recipient_type: roomId
    recipient_id: "{{ room_id }}"
    message_type: text
    personal_token: "{{ token }}"
    send_message: "Cisco Webex Teams Ansible Module - Room Message in Text"

- name: Cisco Webex Teams - Text Message by an Individuals ID
  cisco_spark:
    recipient_type: toPersonId
    recipient_id: "{{ person_id}}"
    message_type: text
    personal_token: "{{ token }}"
    send_message: "Cisco Webex Teams Ansible Module - Text Message to Individual by ID"

- name: Cisco Spark - Text Message by an Individuals E-Mail Address
  cisco_spark:
    recipient_type: toPersonEmail
    recipient_id: "{{ person_email }}"
    message_type: text
    personal_token: "{{ token }}"
    send_message: "Cisco Webex Teams Ansible Module - Text Message to Individual by E-Mail"

"""

RETURN = """
status_code:
  description:
    - The Response Code returned by the Webex Teams API.
    - Full Response Code explanations can be found at U(https://https://developer.webex.com/docs/api/v1/messages/create-a-message).
  returned: always
  type: int
  sample: 200

send_message:
    description:
      - The Response Message returned by the Webex teams API.
      - Full Response Code explanations can be found at U(https://developer.webex.com/docs/api/v1/messages/create-a-message).
    returned: always
    type: str
    sample: OK (585 bytes)
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


def spark_message(module):
    """ When check mode is specified, establish a read only connection, that does not return any user specific
    data, to validate connectivity. In regular mode, send a message to a Cisco Webex teams Room or Individual"""

    # Ansible Specific Variables
    results = {}
    ansible = module.params

    headers = {
        'Authorization': 'Bearer {0}'.format(ansible['personal_token']),
        'content-type': 'application/json'
    }

    if module.check_mode:
        url = "https://api.ciscospark.com/v1/people/me"
        payload = None

    else:
        url = "https://api.ciscospark.com/v1/messages"

        payload = {
            ansible['recipient_type']: ansible['recipient_id'],
            ansible['message_type']: ansible['send_message']
        }

        payload = module.jsonify(payload)

    response, info = fetch_url(module, url, data=payload, headers=headers)

    status_code = info['status']
    send_message = info['msg']

    # Module will fail if the response is not 200
    if status_code != 200:
        results['failed'] = True
        results['status_code'] = status_code
        results['send_message'] = send_message
    else:
        results['failed'] = False
        results['status_code'] = status_code

        if module.check_mode:
            results['send_message'] = 'Authentication Successful.'
        else:
            results['send_message'] = send_message

    return results


def main():
    '''Ansible main. '''
    module = AnsibleModule(
        argument_spec=dict(
            recipient_type=dict(required=True, choices=[
                'roomId', 'toPersonEmail', 'toPersonId']),
            recipient_id=dict(required=True, no_log=True),
            message_type=dict(required=False, default=['text'], aliases=[
                              'type'], choices=['text', 'markdown']),
            personal_token=dict(required=True, no_log=True, aliases=['token']),
            send_message=dict(type='str', required=True, aliases=['message'], deprecated_aliases=[dict(name='message', version='2.14')]),

        ),

        supports_check_mode=True
    )

    results = spark_message(module)

    module.exit_json(**results)


if __name__ == "__main__":
    main()
