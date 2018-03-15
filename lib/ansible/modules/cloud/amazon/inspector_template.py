#!/usr/bin/python
# Copyright (c) 2018 Dennis Conrad for Sainsbury's
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: inspector_template
short_description: Create and Delete Amazon Inspector Assessment Templates
description: Creates and deletes Amazon Inspector assessment templates.
version_added: "2.6"
author: "Dennis Conrad (@dennisconrad)"
options:
  attributes:
    description:
      - The user-defined attributes to be assigned to every generated finding
        from the assessment run that uses this assessment template.
    default: {}
  duration:
    description:
      - The duration in minutes for this assessment template.
    choices:
      - 15
      - 60
      - 480
      - 720
      - 1440
    default: 60
  name:
    description:
      - The name of assessment template.
    required: true
  rules:
    description:
      - The rules packages to be used by this assessment template.  Choices are
        C(best_practices) (Security Best Practices),
        C(cis) (CIS Operating System Security Configuration Benchmarks),
        C(cve) (Common Vulnerabilities and Exposures),
        C(runtime) (Runtime Behavior Analysis).
      - At least one of the above is required if C(state=present).
    default: []
  state:
    description:
      - The state of the assessment template.
    choices:
      - absent
      - present
    default: present
  subscriptions:
    description:
      - List of SNS subscriptions for events the assessment run that uses this
        assessment template triggers. Supported events are
        C(ASSESSMENT_RUN_STARTED),
        C(ASSESSMENT_RUN_COMPLETED),
        C(ASSESSMENT_RUN_STATE_CHANGED),
        C(FINDING_REPORTED).
    default: []
  tags:
    description:
      - Tags to be added to the assessment template
    default: {}
  target:
    description:
      - The name of the assessment target to be used by this assessment
        template.
      - Required if C(state=present)
notes:
  - Attributes to be added to findings cannot be changed (tags and
    subscriptions can be).
requirements:
  - boto3
  - botocore
'''

EXAMPLES = '''
- name: Create my_template Assessment Template with Tags and SNS Notifications
  inspector_template:
    attributes:
      run_no: 12345
      env: dev
    duration: 15
    name: my_template
    rules:
      - cve
      - best_practices
    subscriptions:
      - event: ASSESSMENT_RUN_STARTED
        topic_arn: arn:aws:sns:eu-west-1:123456789012:my_topic
      - event: FINDING_REPORTED
        topic_arn: arn:aws:sns:eu-west-1:123456789012:my_topic
      - event: ASSESSMENT_RUN_COMPLETED
        topic_arn: arn:aws:sns:eu-west-1:123456789012:my_topic
    tags:
      technical_contact: johndoe
    target: my_target

- name: Delete my_template Assessment Template
  inspector_template:
    name: my_template
    state: absent
'''

RETURN = '''
arn:
  description: The ARN of the assessment template.
  returned: success
  type: string
  sample: "arn:aws:inspector:eu-west-1:123456789012:target/0-3whHbHu3/template/0-fZh4XoX4"
assessment_run_count:
  description: The number of existing assessment runs associated with this
               assessment template.  This value can be zero or a positive
               integer.
  returned: success
  type: int
  sample: 2
assessment_target_arn:
  description: The ARN of the assessment target that corresponds to this
               assessment template.
  returned: success
  type: string
  sample: "arn:aws:inspector:eu-west-1:123456789012:target/0-O4LnL7n1"
created_at:
  description: The time at which the assessment template was created.
  returned: success
  type: string
  sample: "2018-01-26T14:08:02.290000+00:00"
duration_in_seconds:
  description: The duration in seconds specified for this assessment template.
  returned: success
  type: int
  sample: 3600
last_assessment_run_arn:
  description: The Amazon Resource Name (ARN) of the most recent assessment run
               associated with this assessment template.  This value exists
               only when the value of I(assessment_run_count) is greater than
               zero.
  returned: when supported
  type: string
  sample: "arn:aws:inspector:eu-west-1:123456789012:target/0-LR3nQYNG/template/0-8f57UI3g/run/0-ElLt5zlP"
name:
  description: The name of the assessment template.
  returned: success
  type: string
  sample: "my_template"
rules_package_arns:
  description: The rules packages that are specified for this assessment
               template.
  returned: success
  type: list
  sample: ["arn:aws:inspector:eu-west-1:357557129151:rulespackage/0-ubA5XvBh",
           "arn:aws:inspector:eu-west-1:357557129151:rulespackage/0-SnojL3Z6"]
subscriptions:
  description: List of event subscriptions for this assessment template.
  returned: success
  type: list
  sample: [{"event": "ASSESSMENT_RUN_STARTED",
            "topic_arn": "arn:aws:sns:eu-west-1:123456789012:my_topic"},
           {"event": "FINDING_REPORTED",
            "topic_arn": "arn:aws:sns:eu-west-1:123456789012:my_topic"}]
tags:
  description: List of tags added to this assessment template.
  returned: success
  type: list
  sample: [{"key": "technical_contact", "value": "johndoe"}]
user_attributes_for_findings:
  description: List of user-defined attributes that are assigned to every
               generated finding from the assessment run that uses this
               assessment template.
  returned: success
  type: list
  sample: [{"key": "run_no", "value": 12345}, {"key": "env", "value": "dev"}]
'''

import re
from botocore.exceptions import ClientError, ValidationError
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import AWSRetry
from ansible.module_utils.ec2 import (
    boto3_conn,
    camel_dict_to_snake_dict,
    get_aws_connection_info,
)


def _check_subs(module, subs):
    sns_arn_regexp = (
        '^'
        'arn:'
        'aws[a-z-]*:'  # allow aws-us-gov, aws-cn etc.
        'sns:'
        r'([a-z]{2}-[a-z-]+-\d|\*|):'  # allow us-gov-west-1 etc.
        r'\d{12}:'  # 12 digit account number
        r'[\w-]{1,256}'  # resource name
        '$'
    )

    supported_events = [
        'ASSESSMENT_RUN_COMPLETED', 'ASSESSMENT_RUN_STARTED',
        'ASSESSMENT_RUN_STATE_CHANGED', 'FINDING_REPORTED',
    ]

    checked_subs = []
    for sub in subs:
        event = sub.get('event').upper()
        topic_arn = sub.get('topic_arn')
        if not event or not topic_arn:
            module.fail_json(msg='expected event and topic_arn, got: %s' % sub)
        elif event not in supported_events:
            module.fail_json(msg='unsupported event: %s' % event)
        elif not re.match(sns_arn_regexp, topic_arn):
            module.fail_json(msg='malformed topic_arn: %s' % topic_arn)
        else:
            checked_subs.append({'event': event, 'topic_arn': topic_arn})

    return checked_subs


@AWSRetry.backoff()
def get_template_arn(client, module, name):
    try:
        return client.list_assessment_templates(
            filter={'namePattern': name},
        ).get('assessmentTemplateArns')[0]
    except (ClientError, ValidationError) as e:
        module.fail_json_aws(e, msg='trying to retrieve template arn')
    except IndexError:
        return None


@AWSRetry.backoff()
def get_template(client, module, arn):
    try:
        template = client.describe_assessment_templates(
            assessmentTemplateArns=[arn],
        ).get('assessmentTemplates')[0]
    except (ClientError, ValidationError) as e:
        module.fail_json_aws(e, msg='trying to retrieve template')
    except IndexError:
        module.fail_json(msg='unknown template: %s' % arn)

    template.update({'tags': _retrieve_tags(client, module, arn)})
    template.update({'subscriptions': _retrieve_subs(client, module, arn)})

    return camel_dict_to_snake_dict(template)


@AWSRetry.backoff()
def get_rules_arns(client, module, rules):
    # Add new rules to this dictionary
    rules_mapping = {
        'best_practices': 'Security Best Practices',
        'cis': 'CIS Operating System Security Configuration Benchmarks',
        'cve': 'Common Vulnerabilities and Exposures',
        'runtime': 'Runtime Behavior Analysis',
    }

    supported_rules = rules_mapping.keys()
    for rule in rules:
        if rule not in supported_rules:
            module.fail_json(msg='unsupported rule: %s' % rule)

    rules_fullnames = [rules_mapping.get(rule) for rule in rules]
    try:
        all_rules_arns = client.list_rules_packages().get('rulesPackageArns')
        all_rules = client.describe_rules_packages(
            rulesPackageArns=all_rules_arns,
        ).get('rulesPackages')
    except (ClientError, ValidationError) as e:
        module.fail_json_aws(e, msg="trying to retrieve rules")

    return [
        rule.get('arn') for rule in all_rules if
        rule.get('name') in rules_fullnames
    ]


@AWSRetry.backoff()
def _retrieve_tags(client, module, arn):
    try:
        return client.list_tags_for_resource(resourceArn=arn).get('tags')
    except (ClientError, ValidationError) as e:
        module.fail_json_aws(e, msg="trying to retrieve tags for target")


@AWSRetry.backoff()
def set_tags(client, module, arn, tags):
    try:
        return client.set_tags_for_resource(
            resourceArn=arn, tags=tags,
        ).get('changed')
    except (ClientError, ValidationError) as e:
        module.fail_json_aws(e, msg="trying to set tags on target")


def update_tags(client, module, arn, tags):
    existing_tags = _retrieve_tags(client, module, arn)
    if sorted(tags) != sorted(existing_tags):
        return set_tags(client, module, arn, tags)
    else:
        return None


@AWSRetry.backoff()
def _retrieve_subs(client, module, arn):
    try:
        event_subs = client.list_event_subscriptions(resourceArn=arn)
        subs = event_subs.get('subscriptions')
        next_token = event_subs.get('nextToken')
        while next_token:
            event_subs = client.list_event_subscriptions(
                resourceArn=arn,
                nextToken=next_token,
            )
            subs += event_subs.get('subscriptions')
            next_token = event_subs.get('nextToken')
    except (ClientError, ValidationError) as e:
        module.fail_json_aws(e, msg="trying to retrieve subs for target")

    return [
        {'topic_arn': sub.get('topicArn'), 'event': event_sub.get('event')}
        for sub in subs for event_sub in sub.get('eventSubscriptions')
    ]


@AWSRetry.backoff()
def add_subs(client, module, arn, subs):
    changed = False
    try:
        for sub in subs:
            client.subscribe_to_event(
                resourceArn=arn,
                event=sub.get('event'),
                topicArn=sub.get('topic_arn'),
            )
            changed = True
    except (ClientError, ValidationError) as e:
        module.fail_json_aws(e, msg="trying to add sub to target")

    return changed


@AWSRetry.backoff()
def delete_subs(client, module, arn, subs):
    changed = False
    try:
        for sub in subs:
            client.unsubscribe_from_event(
                resourceArn=arn,
                event=sub.get('event'),
                topicArn=sub.get('topic_arn'),
            )
            changed = True
    except (ClientError, ValidationError) as e:
        module.fail_json_aws(e, msg="trying to delete sub from target")

    return changed


def update_subs(client, module, arn, subs):
    changed = False
    existing_subs = _retrieve_subs(client, module, arn)
    if sorted(subs) != sorted(existing_subs):
        to_add = [sub for sub in subs if sub not in existing_subs]
        to_delete = [sub for sub in existing_subs if sub not in subs]
        if to_add:
            if add_subs(client, module, arn, to_add):
                changed = True
        if to_delete:
            if delete_subs(client, module, arn, to_delete):
                changed = True

    return changed


@AWSRetry.backoff()
def get_target_arn(client, module, target):
    try:
        return client.list_assessment_targets(
            filter={'assessmentTargetNamePattern': target},
        ).get('assessmentTargetArns')[0]
    except (ClientError, ValidationError) as e:
        module.fail_json_aws(e, msg="trying to retrieve target arn")
    except IndexError:
        module.fail_json(msg='unknown target: %s' % target)


@AWSRetry.backoff()
def main():
    argument_spec = dict(
        attributes=dict(type='dict', default={}),
        duration=dict(
            type='int',
            choices=[15, 60, 480, 720, 1440],
            default=60,
        ),
        name=dict(required=True),
        rules=dict(type='list', default=[]),
        subscriptions=dict(type='list', default=[]),
        state=dict(choices=['absent', 'present'], default='present'),
        tags=dict(type='dict', default={}),
        target=dict(),
    )

    required_if = [['state', 'present', ['rules', 'target']]]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=required_if,
        supports_check_mode=False,
    )

    attributes = [
        {'key': key, 'value': value} for key, value in
        module.params.get('attributes').items()
    ]
    duration = module.params.get('duration')
    name = module.params.get('name')
    rules = module.params.get('rules')
    subscriptions = _check_subs(module, module.params.get('subscriptions'))
    state = module.params.get('state').lower()
    tags = [
        {'key': key, 'value': value} for key, value in
        module.params.get('tags').items()
    ]
    target = module.params.get('target')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(
        module,
        boto3=True,
    )

    if not region:
        module.fail_json(msg='region must be specified')

    try:
        client = boto3_conn(
            module, conn_type='client',
            resource='inspector',
            region=region,
            endpoint=ec2_url,
            **aws_connect_kwargs
        )
    except (ClientError, ValidationError) as e:
        module.fail_json_aws(e, msg="trying to connect to AWS")

    arn = get_template_arn(client, module, name)
    if state == 'present' and arn:
        changed = False

        if update_tags(client, module, arn, tags):
            changed = True

        if update_subs(client, module, arn, subscriptions):
            changed = True

        module.exit_json(changed=changed, **get_template(client, module, arn))
    elif state == 'present' and not arn:
        try:
            arn = client.create_assessment_template(
                assessmentTargetArn=get_target_arn(client, module, target),
                assessmentTemplateName=name,
                durationInSeconds=duration * 60,
                rulesPackageArns=get_rules_arns(client, module, rules),
                userAttributesForFindings=attributes,
            ).get('assessmentTemplateArn')
        except (ClientError, ValidationError) as e:
            module.fail_json_aws(e, msg="trying to create template")

        set_tags(client, module, arn, tags)
        add_subs(client, module, arn, subscriptions)

        module.exit_json(changed=True, **get_template(client, module, arn))

    elif state == 'absent' and arn:
        try:
            client.delete_assessment_template(assessmentTemplateArn=arn)
            module.exit_json(changed=True)
        except (ClientError, ValidationError) as e:
            module.fail_json_aws(e, msg="trying to delete template")

    elif state == 'absent' and not arn:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()
