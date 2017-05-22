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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: batch_compute_environment
short_description: Manage AWS Batch Compute Environments
description:
    - This module allows the management of AWS Batch Compute Environments.
      It is idempotent and supports "Check" mode.  Use module M(batch_compute_environment) to manage the compute
      environment, M(batch_job_queue) to manage job queues, M(batch_job_definition) to manage job definitions.

version_added: "2.4"

author: Jon Meran (@jonmer85)
options:
  compute_environment_name:
    description:
      - The name for your compute environment. Up to 128 letters (uppercase and lowercase), numbers, and underscores
        are allowed.
    required: true

  type:
    description:
      - The type of the compute environment.
    required: true
    choices: ["MANAGED", "UNMANAGED"]

  state:
    description:
      - Describes the desired state.
    required: true
    default: "present"
    choices: ["present", "absent"]

  compute_environment_state:
    description:
      - The state of the compute environment. If the state is ENABLED, then the compute environment accepts jobs
        from a queue and can scale out automatically based on queues.
    default: "ENABLED"
    choices: ["ENABLED", "DISABLED"]

  service_role:
    description:
      - The full Amazon Resource Name (ARN) of the IAM role that allows AWS Batch to make calls to other AWS
        services on your behalf.
    required: true

  compute_resource_type:
    description:
      - The type of compute resource.
    required: true
    choices: ["EC2", "SPOT"]

  minv_cpus:
    description:
      - The minimum number of EC2 vCPUs that an environment should maintain.
    required: true

  maxv_cpus:
    description:
      - The maximum number of EC2 vCPUs that an environment can reach.
    required: true

  desiredv_cpus:
    description:
      - The desired number of EC2 vCPUS in the compute environment.

  instance_types:
    description:
      - The instance types that may be launched.
    required: true

  image_id:
    description:
      - The Amazon Machine Image (AMI) ID used for instances launched in the compute environment.

  subnets:
    description:
      - The VPC subnets into which the compute resources are launched.
    required: true

  security_group_ids:
    description:
      - The EC2 security groups that are associated with instances launched in the compute environment.
    required: true

  ec2_key_pair:
    description:
      - The EC2 key pair that is used for instances launched in the compute environment.

  instance_role:
    description:
      - The Amazon ECS instance role applied to Amazon EC2 instances in a compute environment.
    required: true

  tags:
    description:
      - Key-value pair tags to be applied to resources that are launched in the compute environment.

  bid_percentage:
    description:
      - The minimum percentage that a Spot Instance price must be when compared with the On-Demand price for that
        instance type before instances are launched. For example, if your bid percentage is 20%, then the Spot price
        must be below 20% of the current On-Demand price for that EC2 instance.

  spot_iam_fleet_role:
    description:
      - The Amazon Resource Name (ARN) of the Amazon EC2 Spot Fleet IAM role applied to a SPOT compute environment.


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
  - name: My Batch Compute Environment
    batch_compute_environment:
      compute_environment_name: computeEnvironmentName
      state: present
      region: us-east-1
      compute_environment_state: ENABLED
      type: MANAGED
      compute_resource_type: EC2
      minv_cpus: 0
      maxv_cpus: 2
      desiredv_cpus: 1
      instance_types:
        - optimal
      subnets:
        - my-subnet1
        - my-subnet2
      security_group_ids:
        - my-sg1
        - my-sg2
      instance_role: arn:aws:iam::<account>:instance-profile/<role>
      tags:
        tag1: value1
        tag2: value2
      service_role: arn:aws:iam::<account>:role/service-role/<role>

  - name: show results
    debug: var=batch_compute_environment_action
'''

RETURN = '''
---
batch_compute_environment_action:
    description: describes what action was taken
    returned: success
    type: string
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, get_aws_connection_info, boto3_conn, HAS_BOTO3
from botocore.exceptions import ClientError, ParamValidationError, MissingParametersError
import re


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
    Changes python key into Camel case equivalent. For example, 'compute_environment_name' becomes
    'computeEnvironmentName'.

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

    api_params = dict()

    for param in module_params:
        module_param = module.params.get(param, None)
        if module_param is not None:
            api_params[cc(param)] = module_param
    return api_params


def validate_params(module, aws):
    """
    Performs basic parameter validation.

    :param module:
    :param aws:
    :return:
    """

    compute_environment_name = module.params['compute_environment_name']

    # validate compute environment name
    if not re.search('^[\w\_:]+$', compute_environment_name):
        module.fail_json(
            msg="Function compute_environment_name {0} is invalid. Names must contain only alphanumeric characters "
                "and underscores.".format(compute_environment_name)
        )
    if not compute_environment_name.startswith('arn:aws:batch:'):
        if len(compute_environment_name) > 128:
            module.fail_json(msg='compute_environment_name "{0}" exceeds 128 character limit'
                             .format(compute_environment_name))

    return


# ---------------------------------------------------------------------------------------------------
#
#   Batch Compute Environment functions
#
# ---------------------------------------------------------------------------------------------------

def get_current_compute_environment(module, connection):
    try:
        environments = connection.client().describe_compute_environments(
            computeEnvironments=[module.params['compute_environment_name']]
        )
        return environments['computeEnvironments'][0] if len(environments['computeEnvironments']) > 0 else None
    except ClientError:
        return None


def create_compute_environment(module, aws):
    """
        Adds a Batch compute environment

        :param module:
        :param aws:
        :return:
        """

    client = aws.client('batch')
    changed = False

    # set API parameters
    params = (
        'compute_environment_name', 'type', 'service_role')
    api_params = set_api_params(module, params)

    if module.params['compute_environment_state'] is not None:
        api_params['state'] = module.params['compute_environment_state']

    compute_resources_param_list = ('minv_cpus', 'maxv_cpus', 'desiredv_cpus', 'instance_types', 'image_id', 'subnets',
                                    'security_group_ids', 'ec2_key_pair', 'instance_role', 'tags', 'bid_percentage',
                                    'spot_iam_fleet_role')
    compute_resources_params = set_api_params(module, compute_resources_param_list)

    if module.params['compute_resource_type'] is not None:
        compute_resources_params['type'] = module.params['compute_resource_type']

    # if module.params['minv_cpus'] is not None:
    #     compute_resources_params['minvCpus'] = module.params['minv_cpus']

    api_params['computeResources'] = compute_resources_params

    try:
        if not module.check_mode:
            client.create_compute_environment(**api_params)
        changed = True
    except (ClientError, ParamValidationError, MissingParametersError) as e:
        module.fail_json(msg='Error creating compute environment: {0}'.format(e))

    return changed


def remove_compute_environment(module, aws):
    """
    Remove a Batch compute environment

    :param module:
    :param aws:
    :return:
    """

    client = aws.client('batch')
    changed = False

    # set API parameters
    api_params = {'computeEnvironment': module.params['compute_environment_name']}

    try:
        if not module.check_mode:
            client.delete_compute_environment(**api_params)
        changed = True
    except (ClientError, ParamValidationError, MissingParametersError) as e:
        module.fail_json(msg='Error removing compute environment: {0}'.format(e))
    return changed


def manage_state(module, aws):
    changed = False
    current_state = 'absent'
    state = module.params['state']
    compute_environment_state = module.params['compute_environment_state']
    compute_environment_name = module.params['compute_environment_name']
    service_role = module.params['service_role']
    minv_cpus = module.params['minv_cpus']
    maxv_cpus = module.params['maxv_cpus']
    desiredv_cpus = module.params['desiredv_cpus']
    action_taken = 'none'

    check_mode = module.check_mode

    # check if the compute environment exists
    current_compute_environment = get_current_compute_environment(module, aws)
    response = current_compute_environment
    if current_compute_environment:
        current_state = 'present'

    if state == 'present':
        if current_state == 'present':
            updates = False
            # Update Batch Compute Environment configuration
            compute_kwargs = {'computeEnvironment': compute_environment_name}

            # Update configuration if needed
            compute_resources = {}
            if compute_environment_state and current_compute_environment['state'] != compute_environment_state:
                compute_kwargs.update({'state': compute_environment_state})
                updates = True
            if service_role and current_compute_environment['serviceRole'] != service_role:
                compute_kwargs.update({'serviceRole': service_role})
                updates = True
            if minv_cpus is not None and current_compute_environment['computeResources']['minvCpus'] != minv_cpus:
                compute_resources['minvCpus'] = minv_cpus
            if maxv_cpus is not None and current_compute_environment['computeResources']['maxvCpus'] != maxv_cpus:
                compute_resources['maxvCpus'] = maxv_cpus
            if desiredv_cpus is not None and current_compute_environment['computeResources'][
                    'desiredvCpus'] != desiredv_cpus:
                compute_resources['desiredvCpus'] = desiredv_cpus
            if len(compute_resources) > 0:
                compute_kwargs['computeResources'] = compute_resources
                updates = True
            if updates:
                try:
                    if not check_mode:
                        response = aws.client().update_compute_environment(**compute_kwargs)
                    changed = True
                    action_taken = "updated"
                except (ParamValidationError, ClientError) as e:
                    module.fail_json(msg=str(e))

        else:
            # Create Batch Compute Environment
            changed = create_compute_environment(module, aws)
            # Describe compute environment
            response = get_current_compute_environment(module, aws)
            if not response:
                module.fail_json(msg='Unable to get compute environment information after creating')
            action_taken = 'added'
    else:
        if current_state == 'present':
            # remove the compute environment
            changed = remove_compute_environment(module, aws)
            action_taken = 'deleted'
    return dict(changed=changed, ansible_facts=dict(batch_compute_environment_action=action_taken), response=response)


# ---------------------------------------------------------------------------------------------------
#
#   MAIN
#
# ---------------------------------------------------------------------------------------------------

def main():
    """
    Main entry point.

    :return dict: ansible facts
    """

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            state=dict(required=False, default='present', choices=['present', 'absent']),
            compute_environment_name=dict(required=True, default=None),
            type=dict(required=True, default=None, choices=['MANAGED', 'UNMANAGED']),
            compute_environment_state=dict(required=False, default='ENABLED', choices=['ENABLED', 'DISABLED']),
            service_role=dict(required=True, default=None),
            compute_resource_type=dict(required=True, default=None, choices=['EC2', 'SPOT']),
            minv_cpus=dict(type='int', required=True, default=None),
            maxv_cpus=dict(type='int', required=True, default=None),
            desiredv_cpus=dict(type='int', required=True, default=None),
            instance_types=dict(type='list', required=True, default=None),
            image_id=dict(default=None),
            subnets=dict(type='list', required=True, default=None),
            security_group_ids=dict(type='list', required=True, default=None),
            ec2_key_pair=dict(default=None),
            instance_role=dict(required=True, default=None),
            tags=dict(type='dict', default=None),
            bid_percentage=dict(type='int', default=None),
            spot_iam_fleet_role=dict(default=None)
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_together=[]
    )

    # validate dependencies
    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required for this module.')

    aws = AWSConnection(module, ['batch'])

    validate_params(module, aws)

    results = manage_state(module, aws)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
