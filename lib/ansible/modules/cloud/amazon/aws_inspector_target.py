#!/usr/bin/python
# Copyright (c) 2018 Dennis Conrad for Sainsbury's
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: aws_inspector_target
short_description: Create, Update and Delete Amazon Inspector Assessment
                   Targets
description: Creates, updates, or deletes Amazon Inspector Assessment Targets
             and manages the required Resource Groups.
version_added: "2.6"
author: "Dennis Conrad (@dennisconrad)"
options:
  name:
    description:
      - The user-defined name that identifies the assessment target.  The name
        must be unique within the AWS account.
    required: true
  state:
    description:
      - The state of the assessment target.
    choices:
      - absent
      - present
    default: present
  tags:
    description:
      - Tags of the EC2 instances to be added to the assessment target.
      - Required if C(state=present).
extends_documentation_fragment:
  - aws
  - ec2
requirements:
  - boto3
  - botocore
'''

EXAMPLES = '''
- name: Create my_target Assessment Target
  aws_inspector_target:
    name: my_target
    tags:
      role: scan_target

- name: Update Existing my_target Assessment Target with Additional Tags
  aws_inspector_target:
    name: my_target
    tags:
      env: dev
      role: scan_target

- name: Delete my_target Assessment Target
  aws_inspector_target:
    name: my_target
    state: absent
'''

RETURN = '''
arn:
  description: The ARN that specifies the Amazon Inspector assessment target.
  returned: success
  type: str
  sample: "arn:aws:inspector:eu-west-1:123456789012:target/0-O4LnL7n1"
created_at:
  description: The time at which the assessment target was created.
  returned: success
  type: str
  sample: "2018-01-29T13:48:51.958000+00:00"
name:
  description: The name of the Amazon Inspector assessment target.
  returned: success
  type: str
  sample: "my_target"
resource_group_arn:
  description: The ARN that specifies the resource group that is associated
               with the assessment target.
  returned: success
  type: str
  sample: "arn:aws:inspector:eu-west-1:123456789012:resourcegroup/0-qY4gDel8"
tags:
  description: The tags of the resource group that is associated with the
               assessment target.
  returned: success
  type: list
  sample: {"role": "scan_target", "env": "dev"}
updated_at:
  description: The time at which the assessment target was last updated.
  returned: success
  type: str
  sample: "2018-01-29T13:48:51.958000+00:00"
'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import AWSRetry
from ansible.module_utils.ec2 import (
    HAS_BOTO3,
    ansible_dict_to_boto3_tag_list,
    boto3_tag_list_to_ansible_dict,
    camel_dict_to_snake_dict,
    compare_aws_tags,
)

try:
    import botocore
except ImportError:
    pass  # caught by imported HAS_BOTO3


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def main():
    argument_spec = dict(
        name=dict(required=True),
        state=dict(choices=['absent', 'present'], default='present'),
        tags=dict(type='dict'),
    )

    required_if = [['state', 'present', ['tags']]]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
        required_if=required_if,
    )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 and botocore are required for this module')

    name = module.params.get('name')
    state = module.params.get('state').lower()
    tags = module.params.get('tags')
    if tags:
        tags = ansible_dict_to_boto3_tag_list(tags, 'key', 'value')

    client = module.client('inspector')

    try:
        existing_target_arn = client.list_assessment_targets(
            filter={'assessmentTargetNamePattern': name},
        ).get('assessmentTargetArns')[0]

        existing_target = camel_dict_to_snake_dict(
            client.describe_assessment_targets(
                assessmentTargetArns=[existing_target_arn],
            ).get('assessmentTargets')[0]
        )

        existing_resource_group_arn = existing_target.get('resource_group_arn')
        existing_resource_group_tags = client.describe_resource_groups(
            resourceGroupArns=[existing_resource_group_arn],
        ).get('resourceGroups')[0].get('tags')

        target_exists = True
    except (
        botocore.exceptions.BotoCoreError,
        botocore.exceptions.ClientError,
    ) as e:
        module.fail_json_aws(e, msg="trying to retrieve targets")
    except IndexError:
        target_exists = False

    if state == 'present' and target_exists:
        ansible_dict_tags = boto3_tag_list_to_ansible_dict(tags)
        ansible_dict_existing_tags = boto3_tag_list_to_ansible_dict(
            existing_resource_group_tags
        )
        tags_to_add, tags_to_remove = compare_aws_tags(
            ansible_dict_tags,
            ansible_dict_existing_tags
        )
        if not (tags_to_add or tags_to_remove):
            existing_target.update({'tags': ansible_dict_existing_tags})
            module.exit_json(changed=False, **existing_target)
        else:
            try:
                updated_resource_group_arn = client.create_resource_group(
                    resourceGroupTags=tags,
                ).get('resourceGroupArn')

                client.update_assessment_target(
                    assessmentTargetArn=existing_target_arn,
                    assessmentTargetName=name,
                    resourceGroupArn=updated_resource_group_arn,
                )

                updated_target = camel_dict_to_snake_dict(
                    client.describe_assessment_targets(
                        assessmentTargetArns=[existing_target_arn],
                    ).get('assessmentTargets')[0]
                )

                updated_target.update({'tags': ansible_dict_tags})
                module.exit_json(changed=True, **updated_target),
            except (
                botocore.exceptions.BotoCoreError,
                botocore.exceptions.ClientError,
            ) as e:
                module.fail_json_aws(e, msg="trying to update target")

    elif state == 'present' and not target_exists:
        try:
            new_resource_group_arn = client.create_resource_group(
                resourceGroupTags=tags,
            ).get('resourceGroupArn')

            new_target_arn = client.create_assessment_target(
                assessmentTargetName=name,
                resourceGroupArn=new_resource_group_arn,
            ).get('assessmentTargetArn')

            new_target = camel_dict_to_snake_dict(
                client.describe_assessment_targets(
                    assessmentTargetArns=[new_target_arn],
                ).get('assessmentTargets')[0]
            )

            new_target.update({'tags': boto3_tag_list_to_ansible_dict(tags)})
            module.exit_json(changed=True, **new_target)
        except (
            botocore.exceptions.BotoCoreError,
            botocore.exceptions.ClientError,
        ) as e:
            module.fail_json_aws(e, msg="trying to create target")

    elif state == 'absent' and target_exists:
        try:
            client.delete_assessment_target(
                assessmentTargetArn=existing_target_arn,
            )
            module.exit_json(changed=True)
        except (
            botocore.exceptions.BotoCoreError,
            botocore.exceptions.ClientError,
        ) as e:
            module.fail_json_aws(e, msg="trying to delete target")

    elif state == 'absent' and not target_exists:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()
