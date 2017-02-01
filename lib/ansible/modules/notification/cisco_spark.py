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


ANSIBLE_METADATA = {
    'status': ['stableinterface'],
    'supported_by': 'community',
    'version': '1.0'
}

DOCUMENTATION = '''
---
module: cisco_spark
short_description: Send a message to a Cisco Spark Room or Individual
description:
    - Send a message to a Cisco Spark Room or Individual, with options to control the formatting.
version_added: "1.0"
author: Drew Rusell (@drusse11)
notes:
  - The receipient_id type must be valid for the supplied recipient_type.
  - Full API documentation can be found at https://developer.ciscospark.com/endpoint-messages-post.html

options:

  recipient_type:
    description:
       - The request parametmer you would like to send the message to.
       - Messages can be sent to either a room or individual (by ID or E-Mail).
    required: True
    choices: ['roomId', 'toPersonEmail', 'toPersonId']

  recipient_id:
    description:
      - The unique identifier associated with the supplied recipient_type
    required: true

  message_type:
    description:
       - Specifies how you would like the message formatted.
    required: False
    default: text
    choices: ['text', 'markdown']

  personal_token:
    description:
      - Your personal access token required to validate the Spark API
    require: true
    aliases: ['token']

  message:
    description:
      - The message you would like to send.
    required: True
'''

EXAMPLES = """
# Note: The following examples assume a variable file has been imported
# that contains the appropriate information.

- name: Cisco Spark - Markdown Message to a Room
  cisco_spark:
    recipient_type: roomId
    recipient_id: "{{ room_id }}"
    message_type: markdown
    personal_token: "{{ token }}"
    message: "**Cisco Spark Ansible Module - Room Message in Markdown**"

- name: Cisco Spark - Text Message to a Room
  cisco_spark:
    recipient_type: roomId
    recipient_id: "{{ room_id }}"
    message_type: text
    personal_token: "{{ token }}"
    message: "Cisco Spark Ansible Module - Room Message in Text"

- name: Cisco Spark - Text Message by an Individuals ID
  cisco_spark:
    recipient_type: toPersonId
    recipient_id: "{{ person_id}}"
    message_type: text
    personal_token: "{{ token }}"
    message: "Cisco Spark Ansible Module - Text Message to Individual by ID"

- name: Cisco Spark - Text Message by an Individuals E-Mail Address
  cisco_spark:
    recipient_type: toPersonEmail
    recipient_id: "{{ person_email }}"
    message_type: text
    personal_token: "{{ token }}"
    message: "Cisco Spark Ansible Module - Text Message to Individual by E-Mail"

"""

RETURN = """
status_code:
  description:
    - The Response Code returned by the Spark API
    - Full Responsde Code explanations can be found at https://developer.ciscospark.com/endpoint-messages-post.html
  returned: always
  type: int
  sample: 200

message:
    description:
      - The Response Message returned by the Spark API
      - Full Responsde Code explanations can be found at https://developer.ciscospark.com/endpoint-messages-post.html
    returned: always
    type: string
    sample: OK (585 bytes)
"""


def authenticated_user(module):
    """ Establish a read only connection, that does not return any user specific
    data, to validate connectivity when "check mode" is specified. """

    # Ansible Specific Variables
    results = {}
    ansible = module.params

    # Cisco Spark API Variables
    url = "https://api.ciscospark.com/v1/people/me"

    headers = {
        'Authorization': 'Bearer {}'.format(ansible['personal_token']),
        'content-type': 'application/json'
    }

    response, info = fetch_url(module, url, headers=headers)

    status_code = info['status']
    message = info['msg']

    # Module will fail if the response is not 200
    if status_code != 200:
        results['failed'] = True
        results['status_code'] = status_code
        results['message'] = message

    else:
        results['failed'] = False
        results['status_code'] = status_code
        results['message'] = 'Authentication Successful'

    return results


def spark_message(module):
    """ Send a message to a Cisco Spark Room or Individual """

    # Ansible Specific Variables
    results = {}
    ansible = module.params

    # Cisco Spark API Variables
    url = "https://api.ciscospark.com/v1/messages"

    headers = {
        'Authorization': 'Bearer {}'.format(ansible['personal_token']),
        'content-type': 'application/json'
    }

    # By Room ID
    payload = {
        ansible['recipient_type']: ansible['recipient_id'],
        ansible['message_type']: ansible['message']
    }

    payload = module.jsonify(payload)

    response, info = fetch_url(module, url, data=payload, headers=headers)

    status_code = info['status']
    message = info['msg']

    # Module will fail if the response is not 200
    if status_code != 200:
        results['failed'] = True
        results['status_code'] = status_code
        results['message'] = message

    else:
        results['failed'] = False
        results['status_code'] = status_code
        results['message'] = message

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
            message=dict(required=True)

        ),

        supports_check_mode=True
    )

    # Add Check Mode Support
    if module.check_mode:
        results = authenticated_user(module)
    else:
        results = spark_message(module)

    module.exit_json(**results)


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
main()
