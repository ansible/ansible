#!/usr/bin/python
# Copyright: (c) 2018, Rob White (@wimnat)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: aws_glue_job
short_description: Manage an AWS Glue job
description:
    - Manage an AWS Glue job. See U(https://aws.amazon.com/glue/) for details.
version_added: "2.6"
requirements: [ boto3 ]
author: "Rob White (@wimnat)"
options:
  allocated_capacity:
    description:
      - The number of AWS Glue data processing units (DPUs) to allocate to this Job. From 2 to 100 DPUs
        can be allocated; the default is 10. A DPU is a relative measure of processing power that consists
        of 4 vCPUs of compute capacity and 16 GB of memory.
    required: false
    type: int
  command_name:
    description:
      - The name of the job command. This must be 'glueetl'.
    required: false
    default: glueetl
    type: str
  command_script_location:
    description:
      - The S3 path to a script that executes a job.
    required: true
    type: str
  command_python_version:
    description:
      - The version of python to use in glue.
    required: false
    type: str
  connections:
    description:
      - A list of Glue connections used for this job.
    required: false
    type: list
    elements: str
  default_arguments:
    description:
      - A dict of default arguments for this job.  You can specify arguments here that your own job-execution
        script consumes, as well as arguments that AWS Glue itself consumes.
    required: false
    type: dict
  description:
    description:
      - Description of the job being defined.
    required: false
    type: str
  max_concurrent_runs:
    description:
      - The maximum number of concurrent runs allowed for the job. The default is 1. An error is returned when
        this threshold is reached. The maximum value you can specify is controlled by a service limit.
    required: false
    type: int
  max_retries:
    description:
      -  The maximum number of times to retry this job if it fails.
    required: false
    type: int
  name:
    description:
      - The name you assign to this job definition. It must be unique in your account.
    required: true
    type: str
  role:
    description:
      - The name or ARN of the IAM role associated with this job.
    required: true
    type: str
  state:
    description:
      - Create or delete the AWS Glue job.
    required: true
    choices: [ 'present', 'absent' ]
    type: str
  timeout:
    description:
      - The job timeout in minutes.
    required: false
    type: int
  worker_type:
    description:
      - The type of predefined worker that is allocated when a job runs. Accepts a value of Standard, G.1X, or G.2X.
    required: false
    choices: [ 'Standard', 'G.1X', 'G.2X' ]
    type: str
  number_of_workers:
    description:
      - The number of workers of a defined workerType that are allocated when a job runs.
        The maximum number of workers you can define are 299 for G.1X , and 149 for G.2X
    required: false
    type: int
  glue_version:
    description:
      - Glue version determines the versions of Apache Spark and Python that AWS Glue supports.
    required: false
    choices: [ '0.9', '1.0' ]
    type: str
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create an AWS Glue job
- aws_glue_job:
    command_script_location: s3bucket/script.py
    name: my-glue-job
    role: my-iam-role
    state: present

# Delete an AWS Glue job
- aws_glue_job:
    name: my-glue-job
    state: absent

'''

RETURN = '''
allocated_capacity:
    description: The number of AWS Glue data processing units (DPUs) allocated to runs of this job. From 2 to
                 100 DPUs can be allocated; the default is 10. A DPU is a relative measure of processing power
                 that consists of 4 vCPUs of compute capacity and 16 GB of memory.
    returned: when state is present
    type: int
    sample: 10
command:
    description: The JobCommand that executes this job.
    returned: when state is present
    type: complex
    contains:
        name:
            description: The name of the job command.
            returned: when state is present
            type: str
            sample: glueetl
        script_location:
            description: Specifies the S3 path to a script that executes a job.
            returned: when state is present
            type: str
            sample: mybucket/myscript.py
        python_version:
            description: Specifies the python version to use in the glue job
            returned: when state is present
            type: str
            sample: 3
connections:
    description: The connections used for this job.
    returned: when state is present
    type: dict
    sample: "{ Connections: [ 'list', 'of', 'connections' ] }"
created_on:
    description: The time and date that this job definition was created.
    returned: when state is present
    type: str
    sample: "2018-04-21T05:19:58.326000+00:00"
default_arguments:
    description: The default arguments for this job, specified as name-value pairs.
    returned: when state is present
    type: dict
    sample: "{ 'mykey1': 'myvalue1' }"
description:
    description: Description of the job being defined.
    returned: when state is present
    type: str
    sample: My first Glue job
job_name:
    description: The name of the AWS Glue job.
    returned: always
    type: str
    sample: my-glue-job
execution_property:
    description: An ExecutionProperty specifying the maximum number of concurrent runs allowed for this job.
    returned: always
    type: complex
    contains:
        max_concurrent_runs:
            description: The maximum number of concurrent runs allowed for the job. The default is 1. An error is
                         returned when this threshold is reached. The maximum value you can specify is controlled by
                         a service limit.
            returned: when state is present
            type: int
            sample: 1
last_modified_on:
    description: The last point in time when this job definition was modified.
    returned: when state is present
    type: str
    sample: "2018-04-21T05:19:58.326000+00:00"
max_retries:
    description: The maximum number of times to retry this job after a JobRun fails.
    returned: when state is present
    type: int
    sample: 5
name:
    description: The name assigned to this job definition.
    returned: when state is present
    type: str
    sample: my-glue-job
role:
    description: The name or ARN of the IAM role associated with this job.
    returned: when state is present
    type: str
    sample: my-iam-role
timeout:
    description: The job timeout in minutes.
    returned: when state is present
    type: int
    sample: 300
worker_type:
    description: The type of predefined worker that is allocated when a job runs. Accepts a value of Standard, G.1X, or G.2X.
    returned: when state is present
    type: str
    sample: Standard
number_of_workers:
    description: The number of workers of a defined workerType that are allocated when a job runs.
                 The maximum number of workers you can define are 299 for G.1X , and 149 for G.2X
    required: false
    type: int
    sample: 1
glue_version:
    description: Glue version determines the versions of Apache Spark and Python that AWS Glue supports.
    required: false
    sample: 0.9
'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict

# Non-ansible imports
import copy
try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass


def _get_glue_job(connection, module, glue_job_name):
    """
    Get an AWS Glue job based on name. If not found, return None.

    :param connection: AWS boto3 glue connection
    :param module: Ansible module
    :param glue_job_name: Name of Glue job to get
    :return: boto3 Glue job dict or None if not found
    """

    try:
        return connection.get_job(JobName=glue_job_name)['Job']
    except (BotoCoreError, ClientError) as e:
        if e.response['Error']['Code'] == 'EntityNotFoundException':
            return None
        else:
            module.fail_json_aws(e)


def _compare_glue_job_params(user_params, current_params):
    """
    Compare Glue job params. If there is a difference, return True immediately else return False

    :param user_params: the Glue job parameters passed by the user
    :param current_params: the Glue job parameters currently configured
    :return: True if any parameter is mismatched else False
    """

    # Weirdly, boto3 doesn't return some keys if the value is empty e.g. Description
    # To counter this, add the key if it's missing with a blank value

    if 'Description' not in current_params:
        current_params['Description'] = ""
    if 'DefaultArguments' not in current_params:
        current_params['DefaultArguments'] = dict()

    if 'AllocatedCapacity' in user_params and user_params['AllocatedCapacity'] != current_params['AllocatedCapacity']:
        return True
    if 'Command' in user_params and user_params['Command']['ScriptLocation'] != current_params['Command']['ScriptLocation']:
        return True
    if 'Command' in user_params and user_params['Command'].get('PythonVersion') != current_params['Command'].get('PythonVersion'):
        return True
    if 'Connections' in user_params and set(user_params['Connections']) != set(current_params['Connections']):
        return True
    if 'DefaultArguments' in user_params and set(user_params['DefaultArguments']) != set(current_params['DefaultArguments']):
        return True
    if 'Description' in user_params and user_params['Description'] != current_params['Description']:
        return True
    if 'ExecutionProperty' in user_params and user_params['ExecutionProperty']['MaxConcurrentRuns'] != current_params['ExecutionProperty']['MaxConcurrentRuns']:
        return True
    if 'MaxRetries' in user_params and user_params['MaxRetries'] != current_params['MaxRetries']:
        return True
    if 'Timeout' in user_params and user_params['Timeout'] != current_params['Timeout']:
        return True
    if 'WorkerType' in user_params and user_params['WorkerType'] != current_params['WorkerType']:
        return True
    if 'NumberOfWorkers' in user_params and user_params['NumberOfWorkers'] != current_params['NumberOfWorkers']:
        return True
    if 'GlueVersion' in user_params and user_params['GlueVersion'] != current_params['GlueVersion']:
        return True

    return False


def create_or_update_glue_job(connection, module, glue_job):
    """
    Create or update an AWS Glue job

    :param connection: AWS boto3 glue connection
    :param module: Ansible module
    :param glue_job: a dict of AWS Glue job parameters or None
    :return:
    """

    changed = False
    params = dict()
    params['Name'] = module.params.get("name")
    params['Role'] = module.params.get("role")
    if module.params.get("allocated_capacity") is not None:
        params['AllocatedCapacity'] = module.params.get("allocated_capacity")
    if module.params.get("command_script_location") is not None:
        params['Command'] = {'Name': module.params.get("command_name"), 'ScriptLocation': module.params.get("command_script_location")}
        if module.params.get("command_python_version") is not None:
            params['Command']['PythonVersion'] = module.params.get("command_python_version")
    if module.params.get("connections") is not None:
        params['Connections'] = {'Connections': module.params.get("connections")}
    if module.params.get("default_arguments") is not None:
        params['DefaultArguments'] = module.params.get("default_arguments")
    if module.params.get("description") is not None:
        params['Description'] = module.params.get("description")
    if module.params.get("max_concurrent_runs") is not None:
        params['ExecutionProperty'] = {'MaxConcurrentRuns': module.params.get("max_concurrent_runs")}
    if module.params.get("max_retries") is not None:
        params['MaxRetries'] = module.params.get("max_retries")
    if module.params.get("timeout") is not None:
        params['Timeout'] = module.params.get("timeout")
    if module.params.get("worker_type") is not None:
        params['WorkerType'] = module.params.get("worker_type")
    if module.params.get("number_of_workers") is not None:
        params['NumberOfWorkers'] = module.params.get("number_of_workers")
    if module.params.get("glue_version") is not None:
        params['GlueVersion'] = module.params.get("glue_version")

    # If glue_job is not None then check if it needs to be modified, else create it
    if glue_job:
        if _compare_glue_job_params(params, glue_job):
            try:
                # Update job needs slightly modified params
                update_params = {'JobName': params['Name'], 'JobUpdate': copy.deepcopy(params)}
                del update_params['JobUpdate']['Name']
                connection.update_job(**update_params)
                changed = True
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e)
    else:
        try:
            connection.create_job(**params)
            changed = True
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e)

    # If changed, get the Glue job again
    if changed:
        glue_job = _get_glue_job(connection, module, params['Name'])

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(glue_job))


def delete_glue_job(connection, module, glue_job):
    """
    Delete an AWS Glue job

    :param connection: AWS boto3 glue connection
    :param module: Ansible module
    :param glue_job: a dict of AWS Glue job parameters or None
    :return:
    """

    changed = False

    if glue_job:
        try:
            connection.delete_job(JobName=glue_job['Name'])
            changed = True
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e)

    module.exit_json(changed=changed)


def main():

    argument_spec = (
        dict(
            allocated_capacity=dict(type='int'),
            command_name=dict(type='str', default='glueetl'),
            command_script_location=dict(type='str'),
            command_python_version=dict(type='str'),
            connections=dict(type='list'),
            default_arguments=dict(type='dict'),
            description=dict(type='str'),
            max_concurrent_runs=dict(type='int'),
            max_retries=dict(type='int'),
            name=dict(required=True, type='str'),
            role=dict(type='str'),
            state=dict(required=True, choices=['present', 'absent'], type='str'),
            timeout=dict(type='int'),
            worker_type=dict(choices=['Standard', 'G.1X', 'G.2X'], type='str'),
            number_of_workers=dict(type='int'),
            glue_version=dict(choices=['0.9', '1.0'], type='str'),
        )
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              required_if=[
                                  ('state', 'present', ['role', 'command_script_location'])
                              ]
                              )

    connection = module.client('glue')

    state = module.params.get("state")

    glue_job = _get_glue_job(connection, module, module.params.get("name"))

    if state == 'present':
        create_or_update_glue_job(connection, module, glue_job)
    else:
        delete_glue_job(connection, module, glue_job)


if __name__ == '__main__':
    main()
