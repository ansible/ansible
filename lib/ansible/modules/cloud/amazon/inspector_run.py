#!/usr/bin/python
# Copyright (c) 2018 Dennis Conrad for Sainsbury's
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: inspector_run
short_description: Start, Stop, and Delete Amazon Inspector Assessment Runs
description: Starts, stops, and deletes Amazon Inspector Assessment Runs.
version_added: "2.6"
author: "Dennis Conrad (@dennisconrad)"
options:
  name:
    description:
      - The name of the assessment run.  Required unless C(state=started), in
        which case it is optional.
      - If not specified and C(state=started), a name based on the assessment
        template name, time, and a random string will be generated.
  state:
    description:
      - The state of the assessment run.
    choices:
      - started
      - stopped
      - query
      - absent
    default: started
  template:
    description:
      - The name of the assessment template.
      - Required if C(state=started).
requirements:
  - boto3
  - botocore
notes:
  - An assessment run is considered `started` when a run with the same
    assessment template that is not in state
    C(CANCELED),
    C(COMPLETED),
    C(COMPLETED_WITH_ERRORS),
    C(ERROR),
    C(FAILED)
    exists.  Assessment run names are ignored in this case.
'''

EXAMPLES = '''
- name: Start Assessment Run with name my_run using Template my_template
  inspector_run:
    name: my_run
    template: my_template

- name: Stop Assessment Run
  inspector_run:
    name: my_run
    state: stopped

- name: Query Assessment Run
  inspector_run:
    name: my_run
    state: query

- name: Delete Assessment Run
  inspector_run:
    name: my_run
    state: absent
'''

RETURN = '''
arn:
  description: The ARN of the assessment run.
  returned: success
  type: string
  sample: "arn:aws:inspector:eu-west-1:123456789012:target/0-LlRntYN4/template/0-8D42UIN2/run/0-El4tbzlN"
assessment_template_arn:
  description: The ARN of the assessment template that is associated with the
               assessment run.
  returned: success
  type: string
  sample: "arn:aws:inspector:eu-west-1:123456789012:target/0-L5RdQNNG/template/0-8317U59N"
completed_at:
  description: The assessment run completion time that corresponds to the rules
               packages evaluation completion time or failure.
  returned: when supported
  type: string
  sample: "2018-01-26T13:27:37.665000+00:00"
created_at:
  description: The time when the assessment run was was started.
  returned: success
  type: string
  sample: "2018-01-26T13:27:37.665000+00:00"
data_collected:
  description: A Boolean value that specifies whether the process of collecting
               data from the agents is completed.
  returned: success
  type: boolean
  sample: true
duration_in_seconds:
  description: The duration of the assessment run in seconds.
  returned: success
  type: int
  sample: 3600
finding_counts:
  description: Provides a total count of generated findings per severity.
  returned: when supported
  type: dict
  sample: {"high": 22, "informational": 0, "low": 0, "medium": 8}
name:
  description: The name of the assessment run.
  returned: success
  type: string
  sample: "my_run"
notifications:
  description: A list of notifications for the event subscriptions.
               A notification about a particular generated finding is added to
               this list only once.
  returned: success
  type: list
rules_package_arns:
  description: The rules packages selected for the assessment run.
  returned: success
  type: list
  sample: ["arn:aws:inspector:eu-west-1:357557129151:rulespackage/0-ubA5XvBh"]
started_at:
  description: The time when the assessment run was was started.
  returned: when supported
  type: string
  sample: "2018-01-26T12:25:29.275000+00:00"
state:
  description: The state of the assessment run.
  returned: success
  type: string
  sample: "COMPLETED"
state_changed_at:
  description: The last time when the assessment run's state changed.
  returned: success
  type: string
  sample: "2018-01-26T12:25:29.158000+00:00"
state_changes:
  description: A list of the assessment run state changes.
  returned: success
  type: list
  sample: [{"state": "CREATED",
            "state_changed_at": "2018-01-26T12:25:29.158000+00:00"}]
user_attributes_for_findings:
  description: The user-defined attributes that are assigned to every generated
               finding.
  returned: success
  type: list
  sample: [{"key": "run_no", "value": 12345}, {"key": "env", "value": "dev"}]
'''

from botocore.exceptions import ClientError, ValidationError
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import AWSRetry
from ansible.module_utils.ec2 import (
    boto3_conn,
    camel_dict_to_snake_dict,
    get_aws_connection_info,
)


@AWSRetry.backoff()
def get_template_arn(client, module, name):
    try:
        return client.list_assessment_templates(
            filter={'namePattern': name},
        ).get('assessmentTemplateArns')[0]
    except (ClientError, ValidationError) as e:
        module.fail_json_aws(e, msg='trying to retrieve template arn')
    except IndexError:
        module.fail_json(msg='unknown template: %s' % name)


@AWSRetry.backoff()
def get_runs(client, module, name=None, states=None):
    filters = {}
    filters.update({'namePattern': name} if name else {})
    filters.update({'states': states} if states else {})
    try:
        runs = client.list_assessment_runs(filter=filters)
        all_runs_arns = [runs.get('assessmentRunArns')]
        next_token = runs.get('nextToken')
        while next_token:
            runs = client.list_assessment_runs(
                filter=filters,
                nextToken=next_token,
            )
            all_runs_arns.append(runs.get('assessmentRunArns'))
            next_token = runs.get('nextToken')

        all_runs = []
        for runs_arns in [arn for arn in all_runs_arns if arn]:
            all_runs += client.describe_assessment_runs(
                assessmentRunArns=runs_arns,
            ).get('assessmentRuns')
        return [camel_dict_to_snake_dict(run) for run in all_runs]
    except (ClientError, ValidationError) as e:
        module.fail_json_aws(e, msg='trying to retrieve runs')


def get_single_run(client, module, name):
    try:
        return get_runs(client, module, name)[0]
    except IndexError:
        module.fail_json(msg='unknown run: %s' % name)


@AWSRetry.backoff()
def main():
    argument_spec = dict(
        name=dict(),
        state=dict(
            choices=['absent', 'query', 'started', 'stopped'],
            default='started',
        ),
        template=dict(),
    )

    required_if = [
        ['state', 'started', ['template']],
        ['state', 'absent', ['name']],
        ['state', 'query', ['name']],
        ['state', 'stopped', ['name']],
    ]

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=required_if,
        supports_check_mode=False,
    )

    name = module.params.get('name')
    state = module.params.get('state').lower()
    template = module.params.get('template')
    started_states = [
        'COLLECTING_DATA', 'CREATED', 'DATA_COLLECTED', 'EVALUATING_RULES',
        'START_DATA_COLLECTION_IN_PROGRESS', 'START_DATA_COLLECTION_PENDING',
        'START_EVALUATING_RULES_PENDING', 'STOP_DATA_COLLECTION_PENDING',
    ]
    stopped_states = [
        'CANCELED', 'COMPLETED', 'COMPLETED_WITH_ERRORS', 'ERROR', 'FAILED',
    ]

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

    if state == 'started':
        template_arn = get_template_arn(client, module, template)
        active_runs = get_runs(client, module, states=started_states)
        try:
            active_run = [
                run for run in active_runs if
                run.get('assessment_template_arn') == template_arn
            ][0]
        except IndexError:
            active_run = None

        if not active_run:
            run_params = {'assessmentTemplateArn': template_arn}
            if name and get_runs(client, module, name):
                module.fail_json(msg='name already exists: %s' % name)
            else:
                run_params.update({'assessmentRunName': name})
            try:
                started_run_arn = client.start_assessment_run(
                    **run_params
                ).get('assessmentRunArn')

                started_run = camel_dict_to_snake_dict(
                    client.describe_assessment_runs(
                        assessmentRunArns=[started_run_arn],
                    ).get('assessmentRuns')[0]
                )

                module.exit_json(changed=True, **started_run)
            except (ClientError, ValidationError) as e:
                module.fail_json_aws(e, msg='trying to start run')
        else:
            module.exit_json(changed=False, **active_run)

    elif state == 'stopped':
        run = get_single_run(client, module, name)
        existing_state = run.get('state')
        if existing_state in stopped_states:
            module.exit_json(changed=False, msg=run)
        elif existing_state not in stopped_states:
            try:
                client.stop_assessment_run(assessmentRunArn=run.get('arn'))
                module.exit_json(
                    changed=True,
                    **get_single_run(client, module, name)
                )
            except (ClientError, ValidationError) as e:
                module.fail_json_aws(e, msg='trying to stop run')
        else:
            module.fail_json(msg='unknown state: %s' % existing_state)

    elif state == 'query':
        module.exit_json(changed=False, **get_single_run(client, module, name))

    elif state == 'absent':
        try:
            run = get_runs(client, module, name)[0]
        except IndexError:
            module.exit_json(changed=False)

        if run.get('state') in stopped_states:
            try:
                client.delete_assessment_run(assessmentRunArn=run.get('arn'))
                module.exit_json(changed=True)
            except (ClientError, ValidationError) as e:
                module.fail_json_aws(e, msg='trying to delete run')
        else:
            module.fail_json(msg='run state not in: %s' % stopped_states)


if __name__ == '__main__':
    main()
