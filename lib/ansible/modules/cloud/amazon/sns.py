#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Michael J. Schultz <mjschultz@gmail.com>
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
module: sns
short_description: Send Amazon Simple Notification Service (SNS) messages
description:
    - The C(sns) module sends notifications to a topic on your Amazon SNS account
version_added: 1.6
author: "Michael J. Schultz (@mjschultz)"
options:
  msg:
    description:
      - Default message to send.
    required: true
    aliases: [ "default" ]
  subject:
    description:
      - Subject line for email delivery.
    required: false
  topic:
    description:
      - The topic you want to publish to.
    required: true
  email:
    description:
      - Message to send to email-only subscription
    required: false
  sqs:
    description:
      - Message to send to SQS-only subscription
    required: false
  sms:
    description:
      - Message to send to SMS-only subscription
    required: false
  http:
    description:
      - Message to send to HTTP-only subscription
    required: false
  https:
    description:
      - Message to send to HTTPS-only subscription
    required: false
  aws_secret_key:
    description:
      - AWS secret key. If not set then the value of the AWS_SECRET_KEY environment variable is used.
    required: false
    default: None
    aliases: ['ec2_secret_key', 'secret_key']
  aws_access_key:
    description:
      - AWS access key. If not set then the value of the AWS_ACCESS_KEY environment variable is used.
    required: false
    default: None
    aliases: ['ec2_access_key', 'access_key']
  region:
    description:
      - The AWS region to use. If not specified then the value of the EC2_REGION environment variable, if any, is used.
    required: false
    aliases: ['aws_region', 'ec2_region']
  message_attributes:
    description:
      - Dictionary of message attributes. These are optional structured data entries to be sent along to the endpoint.
      - This is in AWS's distinct Name/Type/Value format; see example below.
    required: false
    default: None
  message_structure:
    description:
      - The payload format to use for the message.
      - This must be 'json' to support non-default messages (`http`, `https`, `email`, `sms`, `sqs`). It must be 'string' to support message_attributes.
    required: true
    default: json
    choices: ['json', 'string']

requirements:
    - "boto"
"""

EXAMPLES = """
- name: Send default notification message via SNS
  sns:
    msg: '{{ inventory_hostname }} has completed the play.'
    subject: Deploy complete!
    topic: deploy
  delegate_to: localhost

- name: Send notification messages via SNS with short message for SMS
  sns:
    msg: '{{ inventory_hostname }} has completed the play.'
    sms: deployed!
    subject: Deploy complete!
    topic: deploy
  delegate_to: localhost

- name: Send message with message_attributes
  sns:
    topic: "deploy"
    msg: "message with extra details!"
    message_attributes:
      channel:
        data_type: String
        string_value: "mychannel"
      color:
        data_type: String
        string_value: "green"
  delegate_to: localhost
"""

import json
import traceback

try:
    import boto
    import boto.ec2
    import boto.sns
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, connect_to_aws, get_aws_connection_info
from ansible.module_utils._text import to_native


def arn_topic_lookup(connection, short_topic):
    response = connection.get_all_topics()
    result = response[u'ListTopicsResponse'][u'ListTopicsResult']
    # topic names cannot have colons, so this captures the full topic name
    lookup_topic = ':{}'.format(short_topic)
    for topic in result[u'Topics']:
        if topic[u'TopicArn'].endswith(lookup_topic):
            return topic[u'TopicArn']
    return None


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            msg=dict(type='str', required=True, aliases=['default']),
            subject=dict(type='str', default=None),
            topic=dict(type='str', required=True),
            email=dict(type='str', default=None),
            sqs=dict(type='str', default=None),
            sms=dict(type='str', default=None),
            http=dict(type='str', default=None),
            https=dict(type='str', default=None),
            message_attributes=dict(type='dict', default=None),
            message_structure=dict(type='str', choices=['json', 'string'], default='json'),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    msg = module.params['msg']
    subject = module.params['subject']
    topic = module.params['topic']
    email = module.params['email']
    sqs = module.params['sqs']
    sms = module.params['sms']
    http = module.params['http']
    https = module.params['https']
    message_attributes = module.params['message_attributes']
    message_structure = module.params['message_structure']

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)
    if not region:
        module.fail_json(msg="region must be specified")
    try:
        connection = connect_to_aws(boto.sns, region, **aws_connect_params)
    except boto.exception.NoAuthHandlerFound as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    if not message_structure == 'string' and message_attributes:
        module.fail_json(msg="when specifying message_attributes, the message_structure must be set to 'string'; otherwise the attributes will not be sent.")
    elif message_structure == 'string' and (email or sqs or sms or http or https):
        module.fail_json(msg="do not specify non-default message formats when using the 'string' message_structure. they can only be used with "
                             "the 'json' message_structure.")

    # .publish() takes full ARN topic id, but I'm lazy and type shortnames
    # so do a lookup (topics cannot contain ':', so that's the decider)
    if ':' in topic:
        arn_topic = topic
    else:
        arn_topic = arn_topic_lookup(connection, topic)

    if not arn_topic:
        module.fail_json(msg='Could not find topic: {}'.format(topic))

    dict_msg = {'default': msg}
    if email:
        dict_msg.update(email=email)
    if sqs:
        dict_msg.update(sqs=sqs)
    if sms:
        dict_msg.update(sms=sms)
    if http:
        dict_msg.update(http=http)
    if https:
        dict_msg.update(https=https)

    if not message_structure == 'json':
        json_msg = msg
    else:
        json_msg = json.dumps(dict_msg)

    try:
        connection.publish(topic=arn_topic, subject=subject,
                           message_structure=message_structure, message=json_msg,
                           message_attributes=message_attributes)
    except boto.exception.BotoServerError as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    module.exit_json(msg="OK")


if __name__ == '__main__':
    main()
