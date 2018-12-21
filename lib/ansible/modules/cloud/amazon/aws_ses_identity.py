#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: aws_ses_identity
short_description: Manages SES email and domain identity
description:
    - This module allows the user to manage verified email and domain identity for SES.
    - This covers verifying and removing identities as well as setting up complaint, bounce
      and delivery notification settings.
version_added: "2.5"
author: Ed Costello    (@orthanc)

options:
    identity:
        description:
            - This is the email address or domain to verify / delete.
            - If this contains an '@' then it will be considered an email. Otherwise it will be considered a domain.
        required: true
    state:
        description: Whether to create(or update) or delete the identity.
        default: present
        choices: [ 'present', 'absent' ]
    bounce_notifications:
        description:
            - Setup the SNS topic used to report bounce notifications.
            - If omitted, bounce notifications will not be delivered to a SNS topic.
            - If bounce notifications are not delivered to a SNS topic, I(feedback_forwarding) must be enabled.
        suboptions:
            topic:
                description:
                    - The ARN of the topic to send notifications to.
                    - If omitted, notifications will not be delivered to a SNS topic.
            include_headers:
                description:
                    - Whether or not to include headers when delivering to the SNS topic.
                    - If I(topic) is not specified this will have no impact, but the SES setting is updated even if there is no topic.
                type: bool
                default: No
    complaint_notifications:
        description:
            - Setup the SNS topic used to report complaint notifications.
            - If omitted, complaint notifications will not be delivered to a SNS topic.
            - If complaint notifications are not delivered to a SNS topic, I(feedback_forwarding) must be enabled.
        suboptions:
            topic:
                description:
                    - The ARN of the topic to send notifications to.
                    - If omitted, notifications will not be delivered to a SNS topic.
            include_headers:
                description:
                    - Whether or not to include headers when delivering to the SNS topic.
                    - If I(topic) is not specified this will have no impact, but the SES setting is updated even if there is no topic.
                type: bool
                default: No
    delivery_notifications:
        description:
            - Setup the SNS topic used to report delivery notifications.
            - If omitted, delivery notifications will not be delivered to a SNS topic.
        suboptions:
            topic:
                description:
                    - The ARN of the topic to send notifications to.
                    - If omitted, notifications will not be delivered to a SNS topic.
            include_headers:
                description:
                    - Whether or not to include headers when delivering to the SNS topic.
                    - If I(topic) is not specified this will have no impact, but the SES setting is updated even if there is no topic.
                type: bool
                default: No
    feedback_forwarding:
        description:
            - Whether or not to enable feedback forwarding.
            - This can only be false if both I(bounce_notifications) and I(complaint_notifications) specify SNS topics.
        type: 'bool'
        default: True
requirements: [ 'botocore', 'boto3' ]
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Ensure example@example.com email identity exists
  aws_ses_identity:
    identity: example@example.com
    state: present

- name: Delete example@example.com email identity
  aws_ses_identity:
    email: example@example.com
    state: absent

- name: Ensure example.com domain identity exists
  aws_ses_identity:
    identity: example.com
    state: present

# Create an SNS topic and send bounce and complaint notifications to it
# instead of emailing the identity owner
- name: Ensure complaints-topic exists
  sns_topic:
    name: "complaints-topic"
    state: present
    purge_subscriptions: False
  register: topic_info

- name: Deliver feedback to topic instead of owner email
  aws_ses_identity:
    identity: example@example.com
    state: present
    complaint_notifications:
      topic: "{{ topic_info.sns_arn }}"
      include_headers: True
    bounce_notifications:
      topic: "{{ topic_info.sns_arn }}"
      include_headers: False
    feedback_forwarding: False

# Create an SNS topic for delivery notifications and leave complaints
# Being forwarded to the identity owner email
- name: Ensure delivery-notifications-topic exists
  sns_topic:
    name: "delivery-notifications-topic"
    state: present
    purge_subscriptions: False
  register: topic_info

- name: Delivery notifications to topic
  aws_ses_identity:
    identity: example@example.com
    state: present
    delivery_notifications:
      topic: "{{ topic_info.sns_arn }}"
'''

RETURN = '''
identity:
    description: The identity being modified.
    returned: success
    type: str
    sample: example@example.com
identity_arn:
    description: The arn of the identity being modified.
    returned: success
    type: str
    sample: arn:aws:ses:us-east-1:12345678:identity/example@example.com
verification_attributes:
    description: The verification information for the identity.
    returned: success
    type: complex
    sample: {
        "verification_status": "Pending",
        "verification_token": "...."
    }
    contains:
        verification_status:
            description: The verification status of the identity.
            type: str
            sample: "Pending"
        verification_token:
            description: The verification token for a domain identity.
            type: str
notification_attributes:
    description: The notification setup for the identity.
    returned: success
    type: complex
    sample: {
        "bounce_topic": "arn:aws:sns:....",
        "complaint_topic": "arn:aws:sns:....",
        "delivery_topic": "arn:aws:sns:....",
        "forwarding_enabled": false,
        "headers_in_bounce_notifications_enabled": true,
        "headers_in_complaint_notifications_enabled": true,
        "headers_in_delivery_notifications_enabled": true
    }
    contains:
        bounce_topic:
            description:
              - The ARN of the topic bounce notifications are delivered to.
              - Omitted if bounce notifications are not delivered to a topic.
            type: str
        complaint_topic:
            description:
              - The ARN of the topic complaint notifications are delivered to.
              - Omitted if complaint notifications are not delivered to a topic.
            type: str
        delivery_topic:
            description:
              - The ARN of the topic delivery notifications are delivered to.
              - Omitted if delivery notifications are not delivered to a topic.
            type: str
        forwarding_enabled:
            description: Whether or not feedback forwarding is enabled.
            type: bool
        headers_in_bounce_notifications_enabled:
            description: Whether or not headers are included in messages delivered to the bounce topic.
            type: bool
        headers_in_complaint_notifications_enabled:
            description: Whether or not headers are included in messages delivered to the complaint topic.
            type: bool
        headers_in_delivery_notifications_enabled:
            description: Whether or not headers are included in messages delivered to the delivery topic.
            type: bool
'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, AWSRetry

import time

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # caught by imported HAS_BOTO3


def get_verification_attributes(connection, module, identity, retries=0, retryDelay=10):
    # Unpredictably get_identity_verification_attributes doesn't include the identity even when we've
    # just registered it. Suspect this is an eventual consistency issue on AWS side.
    # Don't want this complexity exposed users of the module as they'd have to retry to ensure
    # a consistent return from the module.
    # To avoid this we have an internal retry that we use only after registering the identity.
    for attempt in range(0, retries + 1):
        try:
            response = connection.get_identity_verification_attributes(Identities=[identity], aws_retry=True)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg='Failed to retrieve identity verification attributes for {identity}'.format(identity=identity))
        identity_verification = response['VerificationAttributes']
        if identity in identity_verification:
            break
        time.sleep(retryDelay)
    if identity not in identity_verification:
        return None
    return identity_verification[identity]


def get_identity_notifications(connection, module, identity, retries=0, retryDelay=10):
    # Unpredictably get_identity_notifications doesn't include the notifications when we've
    # just registered the identity.
    # Don't want this complexity exposed users of the module as they'd have to retry to ensure
    # a consistent return from the module.
    # To avoid this we have an internal retry that we use only when getting the current notification
    # status for return.
    for attempt in range(0, retries + 1):
        try:
            response = connection.get_identity_notification_attributes(Identities=[identity], aws_retry=True)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg='Failed to retrieve identity notification attributes for {identity}'.format(identity=identity))
        notification_attributes = response['NotificationAttributes']

        # No clear AWS docs on when this happens, but it appears sometimes identities are not included in
        # in the notification attributes when the identity is first registered. Suspect that this is caused by
        # eventual consistency within the AWS services. It's been observed in builds so we need to handle it.
        #
        # When this occurs, just return None and we'll assume no identity notification settings have been changed
        # from the default which is reasonable if this is just eventual consistency on creation.
        # See: https://github.com/ansible/ansible/issues/36065
        if identity in notification_attributes:
            break
        else:
            # Paranoia check for coding errors, we only requested one identity, so if we get a different one
            # something has gone very wrong.
            if len(notification_attributes) != 0:
                module.fail_json(
                    msg='Unexpected identity found in notification attributes, expected {0} but got {1!r}.'.format(
                        identity,
                        notification_attributes.keys(),
                    )
                )
        time.sleep(retryDelay)
    if identity not in notification_attributes:
        return None
    return notification_attributes[identity]


def desired_topic(module, notification_type):
    arg_dict = module.params.get(notification_type.lower() + '_notifications')
    if arg_dict:
        return arg_dict.get('topic', None)
    else:
        return None


def update_notification_topic(connection, module, identity, identity_notifications, notification_type):
    topic_key = notification_type + 'Topic'
    if identity_notifications is None:
        # If there is no configuration for notifications cannot be being sent to topics
        # hence assume None as the current state.
        current = None
    elif topic_key in identity_notifications:
        current = identity_notifications[topic_key]
    else:
        # If there is information on the notifications setup but no information on the
        # particular notification topic it's pretty safe to assume there's no topic for
        # this notification. AWS API docs suggest this information will always be
        # included but best to be defensive
        current = None

    required = desired_topic(module, notification_type)

    if current != required:
        try:
            if not module.check_mode:
                connection.set_identity_notification_topic(Identity=identity, NotificationType=notification_type, SnsTopic=required, aws_retry=True)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg='Failed to set identity notification topic for {identity} {notification_type}'.format(
                identity=identity,
                notification_type=notification_type,
            ))
        return True
    return False


def update_notification_topic_headers(connection, module, identity, identity_notifications, notification_type):
    arg_dict = module.params.get(notification_type.lower() + '_notifications')
    header_key = 'HeadersIn' + notification_type + 'NotificationsEnabled'
    if identity_notifications is None:
        # If there is no configuration for topic notifications, headers cannot be being
        # forwarded, hence assume false.
        current = False
    elif header_key in identity_notifications:
        current = identity_notifications[header_key]
    else:
        # AWS API doc indicates that the headers in fields are optional. Unfortunately
        # it's not clear on what this means. But it's a pretty safe assumption that it means
        # headers are not included since most API consumers would interpret absence as false.
        current = False

    if arg_dict is not None and 'include_headers' in arg_dict:
        required = arg_dict['include_headers']
    else:
        required = False

    if current != required:
        try:
            if not module.check_mode:
                connection.set_identity_headers_in_notifications_enabled(Identity=identity, NotificationType=notification_type, Enabled=required,
                                                                         aws_retry=True)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg='Failed to set identity headers in notification for {identity} {notification_type}'.format(
                identity=identity,
                notification_type=notification_type,
            ))
        return True
    return False


def update_feedback_forwarding(connection, module, identity, identity_notifications):
    if identity_notifications is None:
        # AWS requires feedback forwarding to be enabled unless bounces and complaints
        # are being handled by SNS topics. So in the absence of identity_notifications
        # information existing feedback forwarding must be on.
        current = True
    elif 'ForwardingEnabled' in identity_notifications:
        current = identity_notifications['ForwardingEnabled']
    else:
        # If there is information on the notifications setup but no information on the
        # forwarding state it's pretty safe to assume forwarding is off. AWS API docs
        # suggest this information will always be included but best to be defensive
        current = False

    required = module.params.get('feedback_forwarding')

    if current != required:
        try:
            if not module.check_mode:
                connection.set_identity_feedback_forwarding_enabled(Identity=identity, ForwardingEnabled=required, aws_retry=True)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg='Failed to set identity feedback forwarding for {identity}'.format(identity=identity))
        return True
    return False


def create_mock_notifications_response(module):
    resp = {
        "ForwardingEnabled": module.params.get('feedback_forwarding'),
    }
    for notification_type in ('Bounce', 'Complaint', 'Delivery'):
        arg_dict = module.params.get(notification_type.lower() + '_notifications')
        if arg_dict is not None and 'topic' in arg_dict:
            resp[notification_type + 'Topic'] = arg_dict['topic']

        header_key = 'HeadersIn' + notification_type + 'NotificationsEnabled'
        if arg_dict is not None and 'include_headers' in arg_dict:
            resp[header_key] = arg_dict['include_headers']
        else:
            resp[header_key] = False
    return resp


def update_identity_notifications(connection, module):
    identity = module.params.get('identity')
    changed = False
    identity_notifications = get_identity_notifications(connection, module, identity)

    for notification_type in ('Bounce', 'Complaint', 'Delivery'):
        changed |= update_notification_topic(connection, module, identity, identity_notifications, notification_type)
        changed |= update_notification_topic_headers(connection, module, identity, identity_notifications, notification_type)

    changed |= update_feedback_forwarding(connection, module, identity, identity_notifications)

    if changed or identity_notifications is None:
        if module.check_mode:
            identity_notifications = create_mock_notifications_response(module)
        else:
            identity_notifications = get_identity_notifications(connection, module, identity, retries=4)
    return changed, identity_notifications


def validate_params_for_identity_present(module):
    if module.params.get('feedback_forwarding') is False:
        if not (desired_topic(module, 'Bounce') and desired_topic(module, 'Complaint')):
            module.fail_json(msg="Invalid Parameter Value 'False' for 'feedback_forwarding'. AWS requires "
                             "feedback forwarding to be enabled unless bounces and complaints are handled by SNS topics")


def create_or_update_identity(connection, module, region, account_id):
    identity = module.params.get('identity')
    changed = False
    verification_attributes = get_verification_attributes(connection, module, identity)
    if verification_attributes is None:
        try:
            if not module.check_mode:
                if '@' in identity:
                    connection.verify_email_identity(EmailAddress=identity, aws_retry=True)
                else:
                    connection.verify_domain_identity(Domain=identity, aws_retry=True)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg='Failed to verify identity {identity}'.format(identity=identity))
        if module.check_mode:
            verification_attributes = {
                "VerificationStatus": "Pending",
            }
        else:
            verification_attributes = get_verification_attributes(connection, module, identity, retries=4)
        changed = True
    elif verification_attributes['VerificationStatus'] not in ('Pending', 'Success'):
        module.fail_json(msg="Identity " + identity + " in bad status " + verification_attributes['VerificationStatus'],
                         verification_attributes=camel_dict_to_snake_dict(verification_attributes))

    if verification_attributes is None:
        module.fail_json(msg='Unable to load identity verification attributes after registering identity.')

    notifications_changed, notification_attributes = update_identity_notifications(connection, module)
    changed |= notifications_changed

    if notification_attributes is None:
        module.fail_json(msg='Unable to load identity notification attributes.')

    identity_arn = 'arn:aws:ses:' + region + ':' + account_id + ':identity/' + identity

    module.exit_json(
        changed=changed,
        identity=identity,
        identity_arn=identity_arn,
        verification_attributes=camel_dict_to_snake_dict(verification_attributes),
        notification_attributes=camel_dict_to_snake_dict(notification_attributes),
    )


def destroy_identity(connection, module):
    identity = module.params.get('identity')
    changed = False
    verification_attributes = get_verification_attributes(connection, module, identity)
    if verification_attributes is not None:
        try:
            if not module.check_mode:
                connection.delete_identity(Identity=identity, aws_retry=True)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg='Failed to delete identity {identity}'.format(identity=identity))
        changed = True

    module.exit_json(
        changed=changed,
        identity=identity,
    )


def get_account_id(module):
    sts = module.client('sts')
    try:
        caller_identity = sts.get_caller_identity()
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Failed to retrieve caller identity')
    return caller_identity['Account']


def main():
    module = AnsibleAWSModule(
        argument_spec={
            "identity": dict(required=True, type='str'),
            "state": dict(default='present', choices=['present', 'absent']),
            "bounce_notifications": dict(type='dict'),
            "complaint_notifications": dict(type='dict'),
            "delivery_notifications": dict(type='dict'),
            "feedback_forwarding": dict(default=True, type='bool'),
        },
        supports_check_mode=True,
    )

    for notification_type in ('bounce', 'complaint', 'delivery'):
        param_name = notification_type + '_notifications'
        arg_dict = module.params.get(param_name)
        if arg_dict:
            extra_keys = [x for x in arg_dict.keys() if x not in ('topic', 'include_headers')]
            if extra_keys:
                module.fail_json(msg='Unexpected keys ' + str(extra_keys) + ' in ' + param_name + ' valid keys are topic or include_headers')

    # SES APIs seem to have a much lower throttling threshold than most of the rest of the AWS APIs.
    # Docs say 1 call per second. This shouldn't actually be a big problem for normal usage, but
    # the ansible build runs multiple instances of the test in parallel that's caused throttling
    # failures so apply a jittered backoff to call SES calls.
    connection = module.client('ses', retry_decorator=AWSRetry.jittered_backoff())

    state = module.params.get("state")

    if state == 'present':
        region = module.params.get('region')
        account_id = get_account_id(module)
        validate_params_for_identity_present(module)
        create_or_update_identity(connection, module, region, account_id)
    else:
        destroy_identity(connection, module)


if __name__ == '__main__':
    main()
