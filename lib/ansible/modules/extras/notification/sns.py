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

DOCUMENTATION = """
module: sns
short_description: Send Amazon Simple Notification Service (SNS) messages
description:
    - The M(sns) module sends notifications to a topic on your Amazon SNS account
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

requirements: [ "boto" ]
"""

EXAMPLES = """
- name: Send default notification message via SNS
  local_action:
    module: sns
    msg: "{{ inventory_hostname }} has completed the play."
    subject: "Deploy complete!"
    topic: "deploy"

- name: Send notification messages via SNS with short message for SMS
  local_action:
    module: sns
    msg: "{{ inventory_hostname }} has completed the play."
    sms: "deployed!"
    subject: "Deploy complete!"
    topic: "deploy"
"""

import sys

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

try:
    import boto
    import boto.ec2
    import boto.sns
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False


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

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)
    if not region:
        module.fail_json(msg="region must be specified")
    try:
        connection = connect_to_aws(boto.sns, region, **aws_connect_params)
    except boto.exception.NoAuthHandlerFound, e:
        module.fail_json(msg=str(e))

    # .publish() takes full ARN topic id, but I'm lazy and type shortnames
    # so do a lookup (topics cannot contain ':', so thats the decider)
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

    json_msg = json.dumps(dict_msg)
    try:
        connection.publish(topic=arn_topic, subject=subject,
                           message_structure='json', message=json_msg)
    except boto.exception.BotoServerError, e:
        module.fail_json(msg=str(e))

    module.exit_json(msg="OK")

main()
