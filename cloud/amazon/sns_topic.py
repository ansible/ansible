#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.


DOCUMENTATION = """
module: sns_topic
short_description: Manages AWS SNS topics and subscriptions
description:
    - The M(sns_topic) module allows you to create, delete, and manage subscriptions for AWS SNS topics.
version_added: 2.0
author: "Joel Thompson (@joelthompson)"
options:
  name:
    description:
      - The name or ARN of the SNS topic to converge
    required: True
  state:
    description:
      - Whether to create or destroy an SNS topic
    required: False
    default: present
    choices: ["absent", "present"]
  display_name:
    description:
      - Display name of the topic
    required: False
    default: None
  policy:
    description:
      - Policy to apply to the SNS topic
    required: False
    default: None
  delivery_policy:
    description:
      - Delivery policy to apply to the SNS topic
    required: False
    default: None
  subscriptions:
    description:
      - List of subscriptions to apply to the topic. Note that AWS requires
        subscriptions to be confirmed, so you will need to confirm any new
        subscriptions.
    required: False
    default: []
  purge_subscriptions:
    description:
      - "Whether to purge any subscriptions not listed here. NOTE: AWS does not
        allow you to purge any PendingConfirmation subscriptions, so if any
        exist and would be purged, they are silently skipped. This means that
        somebody could come back later and confirm the subscription. Sorry.
        Blame Amazon."
    required: False
    default: True
extends_documentation_fragment: aws
requirements: [ "boto" ]
"""

EXAMPLES = """

- name: Create alarm SNS topic
  sns_topic:
    name: "alarms"
    state: present
    display_name: "alarm SNS topic"
    delivery_policy: 
      http:
        defaultHealthyRetryPolicy: 
            minDelayTarget: 2
            maxDelayTarget: 4
            numRetries: 3
            numMaxDelayRetries: 5
            backoffFunction: "<linear|arithmetic|geometric|exponential>"
        disableSubscriptionOverrides: True
        defaultThrottlePolicy: 
            maxReceivesPerSecond: 10
    subscriptions:
      - endpoint: "my_email_address@example.com"
        protocol: "email"
      - endpoint: "my_mobile_number"
        protocol: "sms"

"""

RETURN = '''
topic_created:
    description: Whether the topic was newly created
    type: bool
    returned: changed and state == present
    sample: True

attributes_set:
    description: The attributes which were changed
    type: list
    returned: state == "present"
    sample: ["policy", "delivery_policy"]

subscriptions_added:
    description: The subscriptions added to the topic
    type: list
    returned: state == "present"
    sample: [["sms", "my_mobile_number"], ["sms", "my_mobile_2"]]

subscriptions_deleted:
    description: The subscriptions deleted from the topic
    type: list
    returned: state == "present"
    sample: [["sms", "my_mobile_number"], ["sms", "my_mobile_2"]]

sns_arn:
    description: The ARN of the topic you are modifying
    type: string
    returned: state == "present"
    sample: "arn:aws:sns:us-east-1:123456789012:my_topic_name"
'''

import sys
import time
import json
import re

try:
    import boto
    import boto.sns
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False


def canonicalize_endpoint(protocol, endpoint):
    if protocol == 'sms':
        import re
        return re.sub('[^0-9]*', '', endpoint)
    return endpoint



def get_all_topics(connection):
    next_token = None
    topics = []
    while True:
        response = connection.get_all_topics(next_token)
        topics.extend(response['ListTopicsResponse']['ListTopicsResult']['Topics'])
        next_token = \
                response['ListTopicsResponse']['ListTopicsResult']['NextToken']
        if not next_token:
            break
    return [t['TopicArn'] for t in topics]


def arn_topic_lookup(connection, short_topic):
    # topic names cannot have colons, so this captures the full topic name
    all_topics = get_all_topics(connection)
    lookup_topic = ':%s' % short_topic
    for topic in all_topics:
        if topic.endswith(lookup_topic):
            return topic
    return None

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present',
                'absent']),
            display_name=dict(type='str', required=False),
            policy=dict(type='dict', required=False),
            delivery_policy=dict(type='dict', required=False),
            subscriptions=dict(type='list', required=False),
            purge_subscriptions=dict(type='bool', default=True),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    name = module.params.get('name')
    state = module.params.get('state')
    display_name = module.params.get('display_name')
    policy = module.params.get('policy')
    delivery_policy = module.params.get('delivery_policy')
    subscriptions = module.params.get('subscriptions')
    purge_subscriptions = module.params.get('purge_subscriptions')
    check_mode = module.check_mode
    changed = False

    topic_created = False
    attributes_set = []
    subscriptions_added = []
    subscriptions_deleted = []

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)
    if not region:
        module.fail_json(msg="region must be specified")
    try:
        connection = connect_to_aws(boto.sns, region, **aws_connect_params)
    except boto.exception.NoAuthHandlerFound, e:
        module.fail_json(msg=str(e))

    # topics cannot contain ':', so thats the decider
    if ':' in name:
        all_topics = get_all_topics(connection)
        if name in all_topics:
            arn_topic = name
        elif state == 'absent':
            module.exit_json(changed=False)
        else:
            module.fail_json(msg="specified an ARN for a topic but it doesn't"
                    " exist")
    else:
        arn_topic = arn_topic_lookup(connection, name)
        if not arn_topic:
            if state == 'absent':
                module.exit_json(changed=False)
            elif check_mode:
                module.exit_json(changed=True, topic_created=True,
                        subscriptions_added=subscriptions,
                        subscriptions_deleted=[])
            
            changed=True
            topic_created = True
            connection.create_topic(name)
            arn_topic = arn_topic_lookup(connection, name)
            while not arn_topic:
                time.sleep(3)
                arn_topic = arn_topic_lookup(connection, name)
    
    if arn_topic and state == "absent":
        if not check_mode:
            connection.delete_topic(arn_topic)
        module.exit_json(changed=True)

    topic_attributes = connection.get_topic_attributes(arn_topic) \
            ['GetTopicAttributesResponse'] ['GetTopicAttributesResult'] \
            ['Attributes']
    if display_name and display_name != topic_attributes['DisplayName']:
        changed = True
        attributes_set.append('display_name')
        if not check_mode:
            connection.set_topic_attributes(arn_topic, 'DisplayName',
                    display_name)

    if policy and policy != json.loads(topic_attributes['policy']):
        changed = True
        attributes_set.append('policy')
        if not check_mode:
            connection.set_topic_attributes(arn_topic, 'Policy',
                    json.dumps(policy))
    
    if delivery_policy and ('DeliveryPolicy' not in topic_attributes or \
            delivery_policy != json.loads(topic_attributes['DeliveryPolicy'])):
        changed = True
        attributes_set.append('delivery_policy')
        if not check_mode:
            connection.set_topic_attributes(arn_topic, 'DeliveryPolicy',
                    json.dumps(delivery_policy))


    next_token = None
    aws_subscriptions = []
    while True:
        response = connection.get_all_subscriptions_by_topic(arn_topic,
                next_token)
        aws_subscriptions.extend(response['ListSubscriptionsByTopicResponse'] \
                ['ListSubscriptionsByTopicResult']['Subscriptions'])
        next_token = response['ListSubscriptionsByTopicResponse'] \
                ['ListSubscriptionsByTopicResult']['NextToken']
        if not next_token:
            break

    desired_subscriptions = [(sub['protocol'],
        canonicalize_endpoint(sub['protocol'], sub['endpoint'])) for sub in
        subscriptions]
    aws_subscriptions_list = []

    for sub in aws_subscriptions:
        sub_key = (sub['Protocol'], sub['Endpoint'])
        aws_subscriptions_list.append(sub_key)
        if purge_subscriptions and sub_key not in desired_subscriptions and \
                sub['SubscriptionArn'] != 'PendingConfirmation':
            changed = True
            subscriptions_deleted.append(sub_key)
            if not check_mode:
                connection.unsubscribe(sub['SubscriptionArn'])

    for (protocol, endpoint) in desired_subscriptions:
        if (protocol, endpoint) not in aws_subscriptions_list:
            changed = True
            subscriptions_added.append(sub)
            if not check_mode:
                connection.subscribe(arn_topic, protocol, endpoint)

    module.exit_json(changed=changed, topic_created=topic_created,
            attributes_set=attributes_set,
            subscriptions_added=subscriptions_added,
            subscriptions_deleted=subscriptions_deleted, sns_arn=arn_topic)

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
