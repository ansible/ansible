#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = """
module: sns_topic
short_description: Manages AWS SNS topics and subscriptions
description:
    - The C(sns_topic) module allows you to create, delete, and manage subscriptions for AWS SNS topics. As of 2.6,
      this module can be use to subscribe and unsubscribe to topics outside of your AWS account.
version_added: 2.0
author:
  - "Joel Thompson (@joelthompson)"
  - "Fernando Jose Pando (@nand0p)"
  - "Will Thames (@willthames)"
options:
  name:
    description:
      - The name or ARN of the SNS topic to manage
    required: True
  state:
    description:
      - Whether to create or destroy an SNS topic
    default: present
    choices: ["absent", "present"]
  display_name:
    description:
      - Display name of the topic
  policy:
    description:
      - Policy to apply to the SNS topic
  delivery_policy:
    description:
      - Delivery policy to apply to the SNS topic
  subscriptions:
    description:
      - List of subscriptions to apply to the topic. Note that AWS requires
        subscriptions to be confirmed, so you will need to confirm any new
        subscriptions.
    suboptions:
      endpoint:
        description: Endpoint of subscription
        required: yes
      protocol:
        description: Protocol of subscription
        required: yes
    default: []
  purge_subscriptions:
    description:
      - "Whether to purge any subscriptions not listed here. NOTE: AWS does not
        allow you to purge any PendingConfirmation subscriptions, so if any
        exist and would be purged, they are silently skipped. This means that
        somebody could come back later and confirm the subscription. Sorry.
        Blame Amazon."
    default: 'yes'
    type: bool
extends_documentation_fragment:
  - aws
  - ec2
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
sns_arn:
    description: The ARN of the topic you are modifying
    type: str
    returned: always
    sample: "arn:aws:sns:us-east-2:111111111111:my_topic_name"
sns_topic:
  description: Dict of sns topic details
  type: complex
  returned: always
  contains:
    attributes_set:
      description: list of attributes set during this run
      returned: always
      type: list
      sample: []
    check_mode:
      description: whether check mode was on
      returned: always
      type: bool
      sample: false
    delivery_policy:
      description: Delivery policy for the SNS topic
      returned: when topic is owned by this AWS account
      type: str
      sample: >
        {"http":{"defaultHealthyRetryPolicy":{"minDelayTarget":20,"maxDelayTarget":20,"numRetries":3,"numMaxDelayRetries":0,
        "numNoDelayRetries":0,"numMinDelayRetries":0,"backoffFunction":"linear"},"disableSubscriptionOverrides":false}}
    display_name:
      description: Display name for SNS topic
      returned: when topic is owned by this AWS account
      type: str
      sample: My topic name
    name:
      description: Topic name
      returned: always
      type: str
      sample: ansible-test-dummy-topic
    owner:
      description: AWS account that owns the topic
      returned: when topic is owned by this AWS account
      type: str
      sample: '111111111111'
    policy:
      description: Policy for the SNS topic
      returned: when topic is owned by this AWS account
      type: str
      sample: >
        {"Version":"2012-10-17","Id":"SomePolicyId","Statement":[{"Sid":"ANewSid","Effect":"Allow","Principal":{"AWS":"arn:aws:iam::111111111111:root"},
        "Action":"sns:Subscribe","Resource":"arn:aws:sns:us-east-2:111111111111:ansible-test-dummy-topic","Condition":{"StringEquals":{"sns:Protocol":"email"}}}]}
    state:
      description: whether the topic is present or absent
      returned: always
      type: str
      sample: present
    subscriptions:
      description: List of subscribers to the topic in this AWS account
      returned: always
      type: list
      sample: []
    subscriptions_added:
      description: List of subscribers added in this run
      returned: always
      type: list
      sample: []
    subscriptions_confirmed:
      description: Count of confirmed subscriptions
      returned: when topic is owned by this AWS account
      type: str
      sample: '0'
    subscriptions_deleted:
      description: Count of deleted subscriptions
      returned: when topic is owned by this AWS account
      type: str
      sample: '0'
    subscriptions_existing:
      description: List of existing subscriptions
      returned: always
      type: list
      sample: []
    subscriptions_new:
      description: List of new subscriptions
      returned: always
      type: list
      sample: []
    subscriptions_pending:
      description: Count of pending subscriptions
      returned: when topic is owned by this AWS account
      type: str
      sample: '0'
    subscriptions_purge:
      description: Whether or not purge_subscriptions was set
      returned: always
      type: bool
      sample: true
    topic_arn:
      description: ARN of the SNS topic (equivalent to sns_arn)
      returned: when topic is owned by this AWS account
      type: str
      sample: arn:aws:sns:us-east-2:111111111111:ansible-test-dummy-topic
    topic_created:
      description: Whether the topic was created
      returned: always
      type: bool
      sample: false
    topic_deleted:
      description: Whether the topic was deleted
      returned: always
      type: bool
      sample: false
'''

import json
import re

try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule, is_boto3_error_code
from ansible.module_utils.ec2 import compare_policies, AWSRetry, camel_dict_to_snake_dict


class SnsTopicManager(object):
    """ Handles SNS Topic creation and destruction """

    def __init__(self,
                 module,
                 name,
                 state,
                 display_name,
                 policy,
                 delivery_policy,
                 subscriptions,
                 purge_subscriptions,
                 check_mode):

        self.connection = module.client('sns')
        self.module = module
        self.name = name
        self.state = state
        self.display_name = display_name
        self.policy = policy
        self.delivery_policy = delivery_policy
        self.subscriptions = subscriptions
        self.subscriptions_existing = []
        self.subscriptions_deleted = []
        self.subscriptions_added = []
        self.purge_subscriptions = purge_subscriptions
        self.check_mode = check_mode
        self.topic_created = False
        self.topic_deleted = False
        self.topic_arn = None
        self.attributes_set = []

    @AWSRetry.jittered_backoff()
    def _list_topics_with_backoff(self):
        paginator = self.connection.get_paginator('list_topics')
        return paginator.paginate().build_full_result()['Topics']

    @AWSRetry.jittered_backoff()
    def _list_topic_subscriptions_with_backoff(self):
        paginator = self.connection.get_paginator('list_subscriptions_by_topic')
        return paginator.paginate(TopicArn=self.topic_arn).build_full_result()['Subscriptions']

    @AWSRetry.jittered_backoff()
    def _list_subscriptions_with_backoff(self):
        paginator = self.connection.get_paginator('list_subscriptions')
        return paginator.paginate().build_full_result()['Subscriptions']

    def _list_topics(self):
        try:
            topics = self._list_topics_with_backoff()
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Couldn't get topic list")
        return [t['TopicArn'] for t in topics]

    def _topic_arn_lookup(self):
        # topic names cannot have colons, so this captures the full topic name
        all_topics = self._list_topics()
        lookup_topic = ':%s' % self.name
        for topic in all_topics:
            if topic.endswith(lookup_topic):
                return topic

    def _create_topic(self):
        if not self.check_mode:
            try:
                response = self.connection.create_topic(Name=self.name)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                self.module.fail_json_aws(e, msg="Couldn't create topic %s" % self.name)
            self.topic_arn = response['TopicArn']
        return True

    def _set_topic_attrs(self):
        changed = False
        try:
            topic_attributes = self.connection.get_topic_attributes(TopicArn=self.topic_arn)['Attributes']
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Couldn't get topic attributes for topic %s" % self.topic_arn)

        if self.display_name and self.display_name != topic_attributes['DisplayName']:
            changed = True
            self.attributes_set.append('display_name')
            if not self.check_mode:
                try:
                    self.connection.set_topic_attributes(TopicArn=self.topic_arn, AttributeName='DisplayName',
                                                         AttributeValue=self.display_name)
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    self.module.fail_json_aws(e, msg="Couldn't set display name")

        if self.policy and compare_policies(self.policy, json.loads(topic_attributes['Policy'])):
            changed = True
            self.attributes_set.append('policy')
            if not self.check_mode:
                try:
                    self.connection.set_topic_attributes(TopicArn=self.topic_arn, AttributeName='Policy',
                                                         AttributeValue=json.dumps(self.policy))
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    self.module.fail_json_aws(e, msg="Couldn't set topic policy")

        if self.delivery_policy and ('DeliveryPolicy' not in topic_attributes or
                                     compare_policies(self.delivery_policy, json.loads(topic_attributes['DeliveryPolicy']))):
            changed = True
            self.attributes_set.append('delivery_policy')
            if not self.check_mode:
                try:
                    self.connection.set_topic_attributes(TopicArn=self.topic_arn, AttributeName='DeliveryPolicy',
                                                         AttributeValue=json.dumps(self.delivery_policy))
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    self.module.fail_json_aws(e, msg="Couldn't set topic delivery policy")
        return changed

    def _canonicalize_endpoint(self, protocol, endpoint):
        if protocol == 'sms':
            return re.sub('[^0-9]*', '', endpoint)
        return endpoint

    def _set_topic_subs(self):
        changed = False
        subscriptions_existing_list = set()
        desired_subscriptions = [(sub['protocol'],
                                  self._canonicalize_endpoint(sub['protocol'], sub['endpoint'])) for sub in
                                 self.subscriptions]

        for sub in self._list_topic_subscriptions():
            sub_key = (sub['Protocol'], sub['Endpoint'])
            subscriptions_existing_list.add(sub_key)
            if (self.purge_subscriptions and sub_key not in desired_subscriptions and
                    sub['SubscriptionArn'] not in ('PendingConfirmation', 'Deleted')):
                changed = True
                self.subscriptions_deleted.append(sub_key)
                if not self.check_mode:
                    try:
                        self.connection.unsubscribe(SubscriptionArn=sub['SubscriptionArn'])
                    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                        self.module.fail_json_aws(e, msg="Couldn't unsubscribe from topic")

        for protocol, endpoint in set(desired_subscriptions).difference(subscriptions_existing_list):
            changed = True
            self.subscriptions_added.append((protocol, endpoint))
            if not self.check_mode:
                try:
                    self.connection.subscribe(TopicArn=self.topic_arn, Protocol=protocol, Endpoint=endpoint)
                except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                    self.module.fail_json_aws(e, msg="Couldn't subscribe to topic %s" % self.topic_arn)
        return changed

    def _list_topic_subscriptions(self):
        try:
            return self._list_topic_subscriptions_with_backoff()
        except is_boto3_error_code('AuthorizationError'):
            try:
                # potentially AuthorizationError when listing subscriptions for third party topic
                return [sub for sub in self._list_subscriptions_with_backoff()
                        if sub['TopicArn'] == self.topic_arn]
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                self.module.fail_json_aws(e, msg="Couldn't get subscriptions list for topic %s" % self.topic_arn)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
            self.module.fail_json_aws(e, msg="Couldn't get subscriptions list for topic %s" % self.topic_arn)

    def _delete_subscriptions(self):
        # NOTE: subscriptions in 'PendingConfirmation' timeout in 3 days
        #       https://forums.aws.amazon.com/thread.jspa?threadID=85993
        subscriptions = self._list_topic_subscriptions()
        if not subscriptions:
            return False
        for sub in subscriptions:
            if sub['SubscriptionArn'] not in ('PendingConfirmation', 'Deleted'):
                self.subscriptions_deleted.append(sub['SubscriptionArn'])
                if not self.check_mode:
                    try:
                        self.connection.unsubscribe(SubscriptionArn=sub['SubscriptionArn'])
                    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                        self.module.fail_json_aws(e, msg="Couldn't unsubscribe from topic")
        return True

    def _delete_topic(self):
        self.topic_deleted = True
        if not self.check_mode:
            try:
                self.connection.delete_topic(TopicArn=self.topic_arn)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                self.module.fail_json_aws(e, msg="Couldn't delete topic %s" % self.topic_arn)
        return True

    def _name_is_arn(self):
        return self.name.startswith('arn:')

    def ensure_ok(self):
        changed = False
        if self._name_is_arn():
            self.topic_arn = self.name
        else:
            self.topic_arn = self._topic_arn_lookup()
        if not self.topic_arn:
            changed = self._create_topic()
        if self.topic_arn in self._list_topics():
            changed |= self._set_topic_attrs()
        elif self.display_name or self.policy or self.delivery_policy:
            self.module.fail_json(msg="Cannot set display name, policy or delivery policy for SNS topics not owned by this account")
        changed |= self._set_topic_subs()
        return changed

    def ensure_gone(self):
        changed = False
        if self._name_is_arn():
            self.topic_arn = self.name
        else:
            self.topic_arn = self._topic_arn_lookup()
        if self.topic_arn:
            if self.topic_arn not in self._list_topics():
                self.module.fail_json(msg="Cannot use state=absent with third party ARN. Use subscribers=[] to unsubscribe")
            changed = self._delete_subscriptions()
            changed |= self._delete_topic()
        return changed

    def get_info(self):
        info = {
            'name': self.name,
            'state': self.state,
            'subscriptions_new': self.subscriptions,
            'subscriptions_existing': self.subscriptions_existing,
            'subscriptions_deleted': self.subscriptions_deleted,
            'subscriptions_added': self.subscriptions_added,
            'subscriptions_purge': self.purge_subscriptions,
            'check_mode': self.check_mode,
            'topic_created': self.topic_created,
            'topic_deleted': self.topic_deleted,
            'attributes_set': self.attributes_set,
        }
        if self.state != 'absent':
            if self.topic_arn in self._list_topics():
                info.update(camel_dict_to_snake_dict(self.connection.get_topic_attributes(TopicArn=self.topic_arn)['Attributes']))
                info['delivery_policy'] = info.pop('effective_delivery_policy')
            info['subscriptions'] = [camel_dict_to_snake_dict(sub) for sub in self._list_topic_subscriptions()]

        return info


def main():
    argument_spec = dict(
        name=dict(required=True),
        state=dict(default='present', choices=['present', 'absent']),
        display_name=dict(),
        policy=dict(type='dict'),
        delivery_policy=dict(type='dict'),
        subscriptions=dict(default=[], type='list'),
        purge_subscriptions=dict(type='bool', default=True),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              supports_check_mode=True)

    name = module.params.get('name')
    state = module.params.get('state')
    display_name = module.params.get('display_name')
    policy = module.params.get('policy')
    delivery_policy = module.params.get('delivery_policy')
    subscriptions = module.params.get('subscriptions')
    purge_subscriptions = module.params.get('purge_subscriptions')
    check_mode = module.check_mode

    sns_topic = SnsTopicManager(module,
                                name,
                                state,
                                display_name,
                                policy,
                                delivery_policy,
                                subscriptions,
                                purge_subscriptions,
                                check_mode)

    if state == 'present':
        changed = sns_topic.ensure_ok()

    elif state == 'absent':
        changed = sns_topic.ensure_gone()

    sns_facts = dict(changed=changed,
                     sns_arn=sns_topic.topic_arn,
                     sns_topic=sns_topic.get_info())

    module.exit_json(**sns_facts)


if __name__ == '__main__':
    main()
