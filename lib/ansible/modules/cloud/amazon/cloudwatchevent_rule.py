#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: cloudwatchevent_rule
short_description: Manage CloudWatch Event rules and targets
description:
  - This module creates and manages CloudWatch event rules and targets.
version_added: "2.2"
extends_documentation_fragment:
  - aws
  - ec2
author: "Jim Dalton (@jsdalton) <jim.dalton@gmail.com>"
requirements:
  - python >= 2.6
  - boto3
notes:
  - A rule must contain at least an I(event_pattern) or I(schedule_expression). A
    rule can have both an I(event_pattern) and a I(schedule_expression), in which
    case the rule will trigger on matching events as well as on a schedule.
  - When specifying targets, I(input) and I(input_path) are mutually-exclusive
    and optional parameters.
options:
  name:
    description:
      - The name of the rule you are creating, updating or deleting. No spaces
        or special characters allowed (i.e. must match C([\.\-_A-Za-z0-9]+))
    required: true
  schedule_expression:
    description:
      - A cron or rate expression that defines the schedule the rule will
        trigger on. For example, C(cron(0 20 * * ? *)), C(rate(5 minutes))
    required: false
  event_pattern:
    description:
      - A string pattern (in valid JSON format) that is used to match against
        incoming events to determine if the rule should be triggered
    required: false
  state:
    description:
      - Whether the rule is present (and enabled), disabled, or absent
    choices: ["present", "disabled", "absent"]
    default: present
    required: false
  description:
    description:
      - A description of the rule
    required: false
  role_arn:
    description:
      - The Amazon Resource Name (ARN) of the IAM role associated with the rule
    required: false
  targets:
    description:
      - "A dictionary array of targets to add to or update for the rule, in the
        form C({ id: [string], arn: [string], role_arn: [string], input: [valid JSON string],
        input_path: [valid JSONPath string], ecs_parameters: {task_definition_arn: [string], task_count: [int]}}).
        I(id) [required] is the unique target assignment ID. I(arn) (required)
        is the Amazon Resource Name associated with the target. I(role_arn) (optional) is The Amazon Resource Name
        of the IAM role to be used for this target when the rule is triggered. I(input)
        (optional) is a JSON object that will override the event data when
        passed to the target.  I(input_path) (optional) is a JSONPath string
        (e.g. C($.detail)) that specifies the part of the event data to be
        passed to the target. If neither I(input) nor I(input_path) is
        specified, then the entire event is passed to the target in JSON form.
        I(task_definition_arn) [optional] is ecs task definition arn.
        I(task_count) [optional] is ecs task count."
    required: false
'''

EXAMPLES = '''
- cloudwatchevent_rule:
    name: MyCronTask
    schedule_expression: "cron(0 20 * * ? *)"
    description: Run my scheduled task
    targets:
      - id: MyTargetId
        arn: arn:aws:lambda:us-east-1:123456789012:function:MyFunction

- cloudwatchevent_rule:
    name: MyDisabledCronTask
    schedule_expression: "cron(5 minutes)"
    description: Run my disabled scheduled task
    state: disabled
    targets:
      - id: MyOtherTargetId
        arn: arn:aws:lambda:us-east-1:123456789012:function:MyFunction
        input: '{"foo": "bar"}'

- cloudwatchevent_rule:
    name: MyCronTask
    state: absent
'''

RETURN = '''
rule:
    description: CloudWatch Event rule data
    returned: success
    type: dict
    sample:
      arn: 'arn:aws:events:us-east-1:123456789012:rule/MyCronTask'
      description: 'Run my scheduled task'
      name: 'MyCronTask'
      schedule_expression: 'cron(0 20 * * ? *)'
      state: 'ENABLED'
targets:
    description: CloudWatch Event target(s) assigned to the rule
    returned: success
    type: list
    sample: "[{ 'arn': 'arn:aws:lambda:us-east-1:123456789012:function:MyFunction', 'id': 'MyTargetId' }]"
'''

try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, camel_dict_to_snake_dict
from ansible.module_utils.ec2 import ec2_argument_spec, get_aws_connection_info


class CloudWatchEventRule(object):
    def __init__(self, module, name, client, schedule_expression=None,
                 event_pattern=None, description=None, role_arn=None):
        self.name = name
        self.client = client
        self.changed = False
        self.schedule_expression = schedule_expression
        self.event_pattern = event_pattern
        self.description = description
        self.role_arn = role_arn
        self.module = module

    def describe(self):
        """Returns the existing details of the rule in AWS"""
        try:
            rule_info = self.client.describe_rule(Name=self.name)
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == 'ResourceNotFoundException':
                return {}
            self.module.fail_json_aws(e, msg="Could not describe rule %s" % self.name)
        except botocore.exceptions.BotoCoreError as e:
            self.module.fail_json_aws(e, msg="Could not describe rule %s" % self.name)
        return self._snakify(rule_info)

    def put(self, enabled=True):
        """Creates or updates the rule in AWS"""
        request = {
            'Name': self.name,
            'State': "ENABLED" if enabled else "DISABLED",
        }
        if self.schedule_expression:
            request['ScheduleExpression'] = self.schedule_expression
        if self.event_pattern:
            request['EventPattern'] = self.event_pattern
        if self.description:
            request['Description'] = self.description
        if self.role_arn:
            request['RoleArn'] = self.role_arn
        try:
            response = self.client.put_rule(**request)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Could not create/update rule %s" % self.name)
        self.changed = True
        return response

    def delete(self):
        """Deletes the rule in AWS"""
        self.remove_all_targets()

        try:
            response = self.client.delete_rule(Name=self.name)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Could not delete rule %s" % self.name)
        self.changed = True
        return response

    def enable(self):
        """Enables the rule in AWS"""
        try:
            response = self.client.enable_rule(Name=self.name)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Could not enable rule %s" % self.name)
        self.changed = True
        return response

    def disable(self):
        """Disables the rule in AWS"""
        try:
            response = self.client.disable_rule(Name=self.name)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Could not disable rule %s" % self.name)
        self.changed = True
        return response

    def list_targets(self):
        """Lists the existing targets for the rule in AWS"""
        try:
            targets = self.client.list_targets_by_rule(Rule=self.name)
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == 'ResourceNotFoundException':
                return []
            self.module.fail_json_aws(e, msg="Could not find target for rule %s" % self.name)
        except botocore.exceptions.BotoCoreError as e:
            self.module.fail_json_aws(e, msg="Could not find target for rule %s" % self.name)
        return self._snakify(targets)['targets']

    def put_targets(self, targets):
        """Creates or updates the provided targets on the rule in AWS"""
        if not targets:
            return
        request = {
            'Rule': self.name,
            'Targets': self._targets_request(targets),
        }
        try:
            response = self.client.put_targets(**request)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Could not create/update rule targets for rule %s" % self.name)
        self.changed = True
        return response

    def remove_targets(self, target_ids):
        """Removes the provided targets from the rule in AWS"""
        if not target_ids:
            return
        request = {
            'Rule': self.name,
            'Ids': target_ids
        }
        try:
            response = self.client.remove_targets(**request)
        except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
            self.module.fail_json_aws(e, msg="Could not remove rule targets from rule %s" % self.name)
        self.changed = True
        return response

    def remove_all_targets(self):
        """Removes all targets on rule"""
        targets = self.list_targets()
        return self.remove_targets([t['id'] for t in targets])

    def _targets_request(self, targets):
        """Formats each target for the request"""
        targets_request = []
        for target in targets:
            target_request = {
                'Id': target['id'],
                'Arn': target['arn']
            }
            if 'input' in target:
                target_request['Input'] = target['input']
            if 'input_path' in target:
                target_request['InputPath'] = target['input_path']
            if 'role_arn' in target:
                target_request['RoleArn'] = target['role_arn']
            if 'ecs_parameters' in target:
                target_request['EcsParameters'] = {}
                ecs_parameters = target['ecs_parameters']
                if 'task_definition_arn' in target['ecs_parameters']:
                    target_request['EcsParameters']['TaskDefinitionArn'] = ecs_parameters['task_definition_arn']
                if 'task_count' in target['ecs_parameters']:
                    target_request['EcsParameters']['TaskCount'] = ecs_parameters['task_count']
            targets_request.append(target_request)
        return targets_request

    def _snakify(self, dict):
        """Converts cammel case to snake case"""
        return camel_dict_to_snake_dict(dict)


class CloudWatchEventRuleManager(object):
    RULE_FIELDS = ['name', 'event_pattern', 'schedule_expression', 'description', 'role_arn']

    def __init__(self, rule, targets):
        self.rule = rule
        self.targets = targets

    def ensure_present(self, enabled=True):
        """Ensures the rule and targets are present and synced"""
        rule_description = self.rule.describe()
        if rule_description:
            # Rule exists so update rule, targets and state
            self._sync_rule(enabled)
            self._sync_targets()
            self._sync_state(enabled)
        else:
            # Rule does not exist, so create new rule and targets
            self._create(enabled)

    def ensure_disabled(self):
        """Ensures the rule and targets are present, but disabled, and synced"""
        self.ensure_present(enabled=False)

    def ensure_absent(self):
        """Ensures the rule and targets are absent"""
        rule_description = self.rule.describe()
        if not rule_description:
            # Rule doesn't exist so don't need to delete
            return
        self.rule.delete()

    def fetch_aws_state(self):
        """Retrieves rule and target state from AWS"""
        aws_state = {
            'rule': {},
            'targets': [],
            'changed': self.rule.changed
        }
        rule_description = self.rule.describe()
        if not rule_description:
            return aws_state

        # Don't need to include response metadata noise in response
        del rule_description['response_metadata']

        aws_state['rule'] = rule_description
        aws_state['targets'].extend(self.rule.list_targets())
        return aws_state

    def _sync_rule(self, enabled=True):
        """Syncs local rule state with AWS"""
        if not self._rule_matches_aws():
            self.rule.put(enabled)

    def _sync_targets(self):
        """Syncs local targets with AWS"""
        # Identify and remove extraneous targets on AWS
        target_ids_to_remove = self._remote_target_ids_to_remove()
        if target_ids_to_remove:
            self.rule.remove_targets(target_ids_to_remove)

        # Identify targets that need to be added or updated on AWS
        targets_to_put = self._targets_to_put()
        if targets_to_put:
            self.rule.put_targets(targets_to_put)

    def _sync_state(self, enabled=True):
        """Syncs local rule state with AWS"""
        remote_state = self._remote_state()
        if enabled and remote_state != 'ENABLED':
            self.rule.enable()
        elif not enabled and remote_state != 'DISABLED':
            self.rule.disable()

    def _create(self, enabled=True):
        """Creates rule and targets on AWS"""
        self.rule.put(enabled)
        self.rule.put_targets(self.targets)

    def _rule_matches_aws(self):
        """Checks if the local rule data matches AWS"""
        aws_rule_data = self.rule.describe()

        # The rule matches AWS only if all rule data fields are equal
        # to their corresponding local value defined in the task
        return all([
            getattr(self.rule, field) == aws_rule_data.get(field, None)
            for field in self.RULE_FIELDS
        ])

    def _targets_to_put(self):
        """Returns a list of targets that need to be updated or added remotely"""
        remote_targets = self.rule.list_targets()
        return [t for t in self.targets if t not in remote_targets]

    def _remote_target_ids_to_remove(self):
        """Returns a list of targets that need to be removed remotely"""
        target_ids = [t['id'] for t in self.targets]
        remote_targets = self.rule.list_targets()
        return [
            rt['id'] for rt in remote_targets if rt['id'] not in target_ids
        ]

    def _remote_state(self):
        """Returns the remote state from AWS"""
        description = self.rule.describe()
        if not description:
            return
        return description['state']


def get_cloudwatchevents_client(module):
    """Returns a boto3 client for accessing CloudWatch Events"""
    region, ec2_url, aws_conn_kwargs = get_aws_connection_info(module, boto3=True)
    return boto3_conn(module, conn_type='client',
                      resource='events',
                      region=region, endpoint=ec2_url,
                      **aws_conn_kwargs)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True),
            schedule_expression=dict(),
            event_pattern=dict(),
            state=dict(choices=['present', 'disabled', 'absent'],
                       default='present'),
            description=dict(),
            role_arn=dict(),
            targets=dict(type='list', default=[]),
        )
    )
    module = AnsibleAWSModule(argument_spec=argument_spec)

    rule_data = dict(
        [(rf, module.params.get(rf)) for rf in CloudWatchEventRuleManager.RULE_FIELDS]
    )
    targets = module.params.get('targets')
    state = module.params.get('state')

    cwe_rule = CloudWatchEventRule(module,
                                   client=get_cloudwatchevents_client(module),
                                   **rule_data)
    cwe_rule_manager = CloudWatchEventRuleManager(cwe_rule, targets)

    if state == 'present':
        cwe_rule_manager.ensure_present()
    elif state == 'disabled':
        cwe_rule_manager.ensure_disabled()
    elif state == 'absent':
        cwe_rule_manager.ensure_absent()
    else:
        module.fail_json(msg="Invalid state '{0}' provided".format(state))

    module.exit_json(**cwe_rule_manager.fetch_aws_state())


if __name__ == '__main__':
    main()
