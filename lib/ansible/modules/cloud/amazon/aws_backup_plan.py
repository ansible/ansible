#!/usr/bin/python
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: aws_backup_plan
short_description: manage aws backup plans
description:
    - manage backup plans for aws backup, needs additional modules for backup selection and vault
notes:
     - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/backup.html
     - https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/backup.html#Backup.Client.create_backup_plan
version_added: "2.8"
author:
    - "tad merchant (@ezmac)"

requirements: [ json, botocore, boto3 ]
options:
    state:
        description:
          - The desired state of the plan
        required: false
        default: present
        choices: ["present", "absent"]
    name:
        description:
          - The name of backup plan
        required: false
    plan_id:
        description:
             - id of an existing backup plan
        required: false
    rules:
        description: list of rules
        required: true
    tags:
        description:
             - list of tags to set on the backup plan
        required: false

extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.
    - name: Try creating a weekly backup plan
      aws_backup_plan:
        state: present
        name: "test weekly backup plan"
        tags:
          note: "Backup tagged resources weekly"
        rules:
          - rule_name: Weekly
            target_backup_vault_name: Default
            schedule_expression: "cron(15 22 ? * 7 *)"
            start_window_minutes: 60
            completion_window_minutes: 120
            lifecycle:
              delete_after_days: 7
            recovery_point_tags:
              key: "weekly"
      register: weekly_backup_plan
'''

RETURN = '''
backup_plan:
    description: Copy of the backup plan
    returned: when creating a backup plan
    type: complex
    contains:
        backup_plan_name:
            type: str
        rules:
            type: list of complex
            contains:
                rule_name:
                    type: str
                target_backup_vault_name:
                    type: str
                schedule_expression:
                    type: str
                start_window_minutes:
                    type: int
                completion_window_minutes:
                    type: int
                lifecycle:
                    type: complex
                    contains:
                        move_to_cold_storage_after_days:
                            type: int
                        delete_after_days:
                            type: int
                recovery_point_tags:
                    type: list
                rule_id:
                    type: str
backup_plan_id:
    description: Id of the backup plan
    returned: when creating a backup plan
    type: str
backup_plan_arn:
    description:
        An Amazon Resource Name (ARN) that uniquely identifies a backup plan; for example,
        arn:aws:backup:us-east-1:123456789012:plan:8F81F553-3A74-4A3F-B93D-B3360DC80C50 .
    returned: when creating a backup plan
    type: str
version_id:
    description: Unique, randomly generated, Unicode, UTF-8 encoded strings that are at most 1,024 bytes long. Version IDs cannot be edited.
    returned: when creating a backup plan
    type: str
creator_request_id:
    description: A unique string that identifies the request and allows failed requests to be retried without the risk of executing the operation twice.
    returned: when creating a backup plan
    type: str
deletion_date:
    description:
        The date and time that a backup plan is deleted, in Unix format and Coordinated Universal Time (UTC). The value of CreationDate is accurate to
        milliseconds. For example, the value 1516925490.087 represents Friday, January 26, 2018 12:11:30.087 AM.
    returned: when creating a backup plan
    type: str
last_execition_date:
    description:
        The last time a job to back up resources was executed with this backup plan. A date and time, in Unix format and Coordinated Universal Time
        (UTC). The value of LastExecutionDate is accurate to milliseconds. For example, the value 1516925490.087 represents Friday,
        January 26, 2018 12:11:30.087 AM.
    returned: when creating a backup plan
    type: str

'''


from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import ansible_dict_to_boto3_filter_list
from ansible.module_utils.ec2 import ec2_argument_spec, map_complex_type
from ansible.module_utils.ec2 import snake_dict_to_camel_dict, camel_dict_to_snake_dict
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info

try:
    from botocore import waiter as core_waiter
except ImportError:
    pass



RULES_TYPE_MAP = {
    'completion_window_minutes': 'int',
    'start_window_minutes': 'int'
}


# TODO; might need better handling of pagination
def get_backup_plans_by_name(client, name, next_token=None):
    if next_token:
        response = client.list_backup_plans(NextToken=next_token)
    else:
        response = client.list_backup_plans()

    plans = response['BackupPlansList']
    existing_plan = list(filter(
        lambda s: s['BackupPlanName'] == name,
        plans))
    if len(existing_plan) == 0:
        if 'NextToken' in response:
            return client.list_backup_plans(client, name, response['NextToken'])
        else:
            return []
    else:
        return existing_plan


def get_matching_plan_id(client, named_plans, params):
    for named_plan in named_plans:
        plan = client.get_backup_plan(BackupPlanId=named_plan['BackupPlanId'])
        plan_id = plan['BackupPlanId']
        del plan['BackupPlanArn']
        del plan['BackupPlanId']
        del plan['CreationDate']
        del plan['ResponseMetadata']
        del plan['VersionId']
        for rule in plan['BackupPlan']['Rules']:
            del rule['RuleId']
        if plan == params:
            return plan_id


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(choices=['present', 'absent'], default='present'),
        name=dict(required=False, type='str'),
        plan_id=dict(required=False, type='str'),
        rules=dict(required=False, type='list'),
        tags=dict(required=False, type='dict')
    ))

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=False
    )

    client = module.client('backup')

    changed = False
    version_id = None

    if module.params['state'] == 'present':
        plan_id = None
        if module.params['name'] is not None:
            named_plans = get_backup_plans_by_name(client, module.params['name'])
            params = dict(
                BackupPlan=dict(
                    BackupPlanName=module.params['name'],
                    Rules=[],
                )
            )
            for rule in module.params['rules']:
                params['BackupPlan']['Rules'].append(
                    snake_dict_to_camel_dict(map_complex_type(rule, RULES_TYPE_MAP), True)
                )
                # either, there will be one plan with name or many.  for many, we bail out.

            if len(named_plans) > 1:
                module.fail_json(msg="Exception: multiple backup plans exist with this name. can't continue", plans=named_plans)
            if len(named_plans) == 1:
                plan_id = named_plans[0]['BackupPlanId']
                version_id = named_plans[0]['VersionId']
            # if one, does it match?

        if module.params['plan_id'] is not None:
            plan_id = module.params['plan_id']

        try:
            if plan_id is not None:
                params['BackupPlanId'] = plan_id
                response = client.update_backup_plan(**params)
                if version_id != response['VersionId']:
                    changed = True
            else:
                response = client.create_backup_plan(**params)
                changed = True

            backup_plan_info = camel_dict_to_snake_dict(
                client.get_backup_plan(
                    BackupPlanId=response['BackupPlanId']
                )
            )

            module.exit_json(changed=changed, named_plans=named_plans, plan_id=plan_id, **backup_plan_info)

        except Exception as e:
            module.fail_json(msg="Exception '" + module.params['name'] + "': " + str(e))

    if module.params['state'] == 'absent':
        # still need the case where you delete a plan by id.
        plans = get_backup_plans_by_name(client, module.params['name'])
        for plan in plans:
            client.delete_backup_plan(BackupPlanId=plan['BackupPlanId'])
        if len(plans) > 0:
            changed = True

        module.exit_json(changed=True)


if __name__ == '__main__':
    main()
