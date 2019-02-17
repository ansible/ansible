#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2014, Michael J. Schultz <mjschultz@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
module: sns
short_description: Send Amazon Simple Notification Service messages
description:
  - Sends a notification to a topic on your Amazon SNS account.
version_added: 1.6
author:
  - Michael J. Schultz (@mjschultz)
  - Paul Arthur (@flowerysong)
options:
  msg:
    description:
      - Default message for subscriptions without a more specific message.
    required: true
    aliases: [ "default" ]
  subject:
    description:
      - Message subject
  topic:
    description:
      - The name or ARN of the topic to publish to.
    required: true
  email:
    description:
      - Message to send to email subscriptions.
  email_json:
    description:
      - Message to send to email-json subscriptions
    version_added: '2.8'
  sqs:
    description:
      - Message to send to SQS subscriptions
  sms:
    description:
      - Message to send to SMS subscriptions
  http:
    description:
      - Message to send to HTTP subscriptions
  https:
    description:
      - Message to send to HTTPS subscriptions
  application:
    description:
      - Message to send to application subscriptions
    version_added: '2.8'
  lambda:
    description:
      - Message to send to Lambda subscriptions
    version_added: '2.8'
  message_attributes:
    description:
      - Dictionary of message attributes. These are optional structured data entries to be sent along to the endpoint.
      - This is in AWS's distinct Name/Type/Value format; see example below.
  message_structure:
    description:
      - The payload format to use for the message.
      - This must be 'json' to support protocol-specific messages (`http`, `https`, `email`, `sms`, `sqs`). It must be 'string' to support message_attributes.
    default: json
    choices: ['json', 'string']
extends_documentation_fragment:
  - ec2
  - aws
requirements:
  - boto3
  - botocore
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

RETURN = """
msg:
  description: Human-readable diagnostic information
  returned: always
  type: str
  sample: OK
message_id:
  description: The message ID of the submitted message
  returned: when success
  type: str
  sample: 2f681ef0-6d76-5c94-99b2-4ae3996ce57b
"""

import json
import traceback

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass    # Handled by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule


def arn_topic_lookup(module, client, short_topic):
    lookup_topic = ':{0}'.format(short_topic)

    try:
        paginator = client.get_paginator('list_topics')
        topic_iterator = paginator.paginate()
        for response in topic_iterator:
            for topic in response['Topics']:
                if topic['TopicArn'].endswith(lookup_topic):
                    return topic['TopicArn']
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Failed to look up topic ARN')

    return None


def main():
    protocols = [
        'http',
        'https',
        'email',
        'email_json',
        'sms',
        'sqs',
        'application',
        'lambda',
    ]

    argument_spec = dict(
        msg=dict(required=True, aliases=['default']),
        subject=dict(),
        topic=dict(required=True),
        message_attributes=dict(type='dict'),
        message_structure=dict(choices=['json', 'string'], default='json'),
    )

    for p in protocols:
        argument_spec[p] = dict()

    module = AnsibleAWSModule(argument_spec=argument_spec)

    sns_kwargs = dict(
        Message=module.params['msg'],
        Subject=module.params['subject'],
        MessageStructure=module.params['message_structure'],
    )

    if module.params['message_attributes']:
        if module.params['message_structure'] != 'string':
            module.fail_json(msg='message_attributes is only supported when the message_structure is "string".')
        sns_kwargs['MessageAttributes'] = module.params['message_attributes']

    dict_msg = {
        'default': sns_kwargs['Message']
    }

    for p in protocols:
        if module.params[p]:
            if sns_kwargs['MessageStructure'] != 'json':
                module.fail_json(msg='Protocol-specific messages are only supported when message_structure is "json".')
            dict_msg[p.replace('_', '-')] = module.params[p]

    client = module.client('sns')

    topic = module.params['topic']
    if ':' in topic:
        # Short names can't contain ':' so we'll assume this is the full ARN
        sns_kwargs['TopicArn'] = topic
    else:
        sns_kwargs['TopicArn'] = arn_topic_lookup(module, client, topic)

    if not sns_kwargs['TopicArn']:
        module.fail_json(msg='Could not find topic: {0}'.format(topic))

    if sns_kwargs['MessageStructure'] == 'json':
        sns_kwargs['Message'] = json.dumps(dict_msg)

    try:
        result = client.publish(**sns_kwargs)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Failed to publish message')

    module.exit_json(msg='OK', message_id=result['MessageId'])


if __name__ == '__main__':
    main()
