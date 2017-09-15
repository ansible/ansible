#!/usr/bin/python
# (c) 2017, Jon Meran <jonathan.meran@sonos.com>
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
module: aws_batch_job_queue
short_description: Manage AWS Batch Job Queues
description:
    - This module allows the management of AWS Batch Job Queues.
      It is idempotent and supports "Check" mode.  Use module M(batch_compute_environment) to manage the compute
      environment, M(batch_job_queue) to manage job queues, M(batch_job_definition) to manage job definitions.

version_added: "2.5"

author: Jon Meran (@jonmer85)
options:
  job_queue_name:
    description:
      - The name for the job queue
    required: true

  state:
    description:
      - Describes the desired state.
    required: true
    default: "present"
    choices: ["present", "absent"]

  job_queue_state:
    description:
      - The state of the job queue. If the job queue state is ENABLED , it is able to accept jobs.
    default: "ENABLED"
    choices: ["ENABLED", "DISABLED"]

  priority:
    description:
      - The priority of the job queue. Job queues with a higher priority (or a lower integer value for the priority
        parameter) are evaluated first when associated with same compute environment. Priority is determined in
        ascending order, for example, a job queue with a priority value of 1 is given scheduling preference over a job
        queue with a priority value of 10.
    required: true

  compute_environment_order:
    description:
      - The set of compute environments mapped to a job queue and their order relative to each other. The job
        scheduler uses this parameter to determine which compute environment should execute a given job. Compute
        environments must be in the VALID state before you can associate them with a job queue. You can associate up to
        3 compute environments with a job queue.
    required: true

requirements:
    - boto3
extends_documentation_fragment:
    - aws
'''

EXAMPLES = '''
---
- hosts: localhost
  gather_facts: no
  vars:
    state: present
  tasks:
  - name: My Batch Job Queue
    batch_job_queue:
      job_queue_name: jobQueueName
      state: present
      region: us-east-1
      job_queue_state: ENABLED
      priority: 1
      compute_environment_order:
        - order: 1
          compute_environment: my_compute_env1
        - order: 2
          compute_environment: my_compute_env2

  - name: show results
    debug: var=batch_job_queue_action
'''

RETURN = '''
---
output:
  description: "returns what action was taken, whether something was changed, invocation and response"
  returned: always
  sample:
    batch_job_queue_action: updated
    changed: false
    response:
      job_queue_arn: "arn:aws:batch:...."
      job_queue_name: <name>
      priority: 1
      state: DISABLED
      status: UPDATING
      status_reason: "JobQueue Healthy"
  type: dict
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, get_aws_connection_info, boto3_conn, HAS_BOTO3
from ansible.module_utils.ec2 import snake_dict_to_camel_dict
from ansible.module_utils.ec2 import camel_dict_to_snake_dict

try:
    from botocore.exceptions import ClientError, ParamValidationError, MissingParametersError
    import re

    HAS_BOTOCORE = True
except ImportError:
    HAS_BOTOCORE = False


# ---------------------------------------------------------------------------------------------------
#
#   Helper Functions & classes
#
# ---------------------------------------------------------------------------------------------------


class AWSConnection:
    """
    Create the connection object and client objects as required.
    """

    def __init__(self, ansible_obj, resources, boto3=True):

        try:
            self.region, self.endpoint, aws_connect_kwargs = get_aws_connection_info(ansible_obj, boto3=boto3)

            self.resource_client = dict()
            if not resources:
                resources = ['batch']

            resources.append('iam')

            for resource in resources:
                aws_connect_kwargs.update(dict(region=self.region,
                                               endpoint=self.endpoint,
                                               conn_type='client',
                                               resource=resource
                                               ))
                self.resource_client[resource] = boto3_conn(ansible_obj, **aws_connect_kwargs)

            # if region is not provided, then get default profile/session region
            if not self.region:
                self.region = self.resource_client['batch'].meta.region_name

        except (ClientError, ParamValidationError, MissingParametersError) as e:
            ansible_obj.fail_json(msg="Unable to connect, authorize or access resource: {0}".format(e))

        # set account ID
        try:
            self.account_id = self.resource_client['iam'].get_user()['User']['Arn'].split(':')[4]
        except (ClientError, ValueError, KeyError, IndexError):
            self.account_id = ''

    def client(self, resource='batch'):
        return self.resource_client[resource]


def cc(key):
    """
    Changes python key into Camel case equivalent. For example, 'compute_environment_name' becomes 'computeEnvironmentName'.

    :param key:
    :return:
    """
    components = key.split('_')
    return components[0] + "".join([token.capitalize() for token in components[1:]])


def set_api_params(module, module_params):
    """
    Sets module parameters to those expected by the boto3 API.

    :param module:
    :param module_params:
    :return:
    """
    api_params = dict((k, v) for k, v in dict(module.params).items() if k in module_params and v is not None)
    return snake_dict_to_camel_dict(api_params)


def validate_params(module, aws):
    """
    Performs basic parameter validation.

    :param module:
    :param aws:
    :return:
    """
    return


# ---------------------------------------------------------------------------------------------------
#
#   Batch Job Queue functions
#
# ---------------------------------------------------------------------------------------------------

def get_current_job_queue(module, connection):
    try:
        environments = connection.client().describe_job_queues(
            jobQueues=[module.params['job_queue_name']]
        )
        return environments['jobQueues'][0] if len(environments['jobQueues']) > 0 else None
    except ClientError:
        return None


def create_job_queue(module, aws):
    """
        Adds a Batch job queue

        :param module:
        :param aws:
        :return:
        """

    client = aws.client('batch')
    changed = False

    # set API parameters
    params = ('job_queue_name', 'priority')
    api_params = set_api_params(module, params)

    if module.params['job_queue_state'] is not None:
        api_params['state'] = module.params['job_queue_state']

    api_params['computeEnvironmentOrder'] = get_compute_environment_order_list(module)

    try:
        if not module.check_mode:
            client.create_job_queue(**api_params)
        changed = True
    except (ClientError, ParamValidationError, MissingParametersError) as e:
        module.fail_json(msg='Error creating compute environment: {0}'.format(e))

    return changed


def get_compute_environment_order_list(module):
    compute_environment_order_list = []
    for ceo in module.params['compute_environment_order']:
        compute_environment_order_list.append(dict(order=ceo['order'], computeEnvironment=ceo['compute_environment']))
    return compute_environment_order_list


def remove_job_queue(module, aws):
    """
    Remove a Batch job queue

    :param module:
    :param aws:
    :return:
    """

    client = aws.client('batch')
    changed = False

    # set API parameters
    api_params = {'jobQueue': module.params['job_queue_name']}

    try:
        if not module.check_mode:
            client.delete_job_queue(**api_params)
        changed = True
    except (ClientError, ParamValidationError, MissingParametersError) as e:
        module.fail_json(msg='Error removing job queue: {0}'.format(e))
    return changed


def manage_state(module, aws):
    changed = False
    current_state = 'absent'
    state = module.params['state']
    job_queue_state = module.params['job_queue_state']
    job_queue_name = module.params['job_queue_name']
    priority = module.params['priority']
    action_taken = 'none'
    response = None

    check_mode = module.check_mode

    # check if the job queue exists
    current_job_queue = get_current_job_queue(module, aws)
    if current_job_queue:
        current_state = 'present'

    if state == 'present':
        if current_state == 'present':
            updates = False
            # Update Batch Job Queuet configuration
            job_kwargs = {'jobQueue': job_queue_name}

            # Update configuration if needed
            if job_queue_state and current_job_queue['state'] != job_queue_state:
                job_kwargs.update({'state': job_queue_state})
                updates = True
            if priority is not None and current_job_queue['priority'] != priority:
                job_kwargs.update({'priority': priority})
                updates = True

            new_compute_environment_order_list = get_compute_environment_order_list(module)
            if new_compute_environment_order_list != current_job_queue['computeEnvironmentOrder']:
                job_kwargs['computeEnvironmentOrder'] = new_compute_environment_order_list
                updates = True

            if updates:
                try:
                    if not check_mode:
                        aws.client().update_job_queue(**job_kwargs)
                    changed = True
                    action_taken = "updated"
                except (ParamValidationError, ClientError) as e:
                    module.fail_json(msg=str(e))

        else:
            # Create Job Queue
            changed = create_job_queue(module, aws)
            action_taken = 'added'

        # Describe job queue
        response = get_current_job_queue(module, aws)
        if not response:
            module.fail_json(msg='Unable to get job queue information after creating/updating')
    else:
        if current_state == 'present':
            # remove the Job Queue
            changed = remove_job_queue(module, aws)
            action_taken = 'deleted'
    return dict(changed=changed, batch_job_queue_action=action_taken, response=response)


# ---------------------------------------------------------------------------------------------------
#
#   MAIN
#
# ---------------------------------------------------------------------------------------------------

def main():
    """
    Main entry point.

    :return dict: changed, batch_job_queue_action, response
    """

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            state=dict(required=False, default='present', choices=['present', 'absent']),
            job_queue_name=dict(required=True),
            job_queue_state=dict(required=False, default='ENABLED', choices=['ENABLED', 'DISABLED']),
            priority=dict(type='int', required=True),
            compute_environment_order=dict(type='list', required=True),
            region=dict(required=True)
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec
    )

    # validate dependencies
    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required for this module.')

    if not HAS_BOTOCORE:
        module.fail_json(msg='botocore and re is required for this module.')

    aws = AWSConnection(module, ['batch'])

    validate_params(module, aws)

    results = manage_state(module, aws)

    module.exit_json(**camel_dict_to_snake_dict(results))


if __name__ == '__main__':
    main()
