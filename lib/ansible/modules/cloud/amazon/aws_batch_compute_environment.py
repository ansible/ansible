#!/usr/bin/python
# Copyright (c) 2017 Jon Meran <jonathan.meran@sonos.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: aws_batch_compute_environment
short_description: Manage AWS Batch Compute Environments
description:
    - This module allows the management of AWS Batch Compute Environments.
      It is idempotent and supports "Check" mode.  Use module M(aws_batch_compute_environment) to manage the compute
      environment, M(aws_batch_job_queue) to manage job queues, M(aws_batch_job_definition) to manage job definitions.

version_added: "2.5"

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
    - ec2
'''

EXAMPLES = '''
---
- hosts: localhost
  gather_facts: no
  vars:
    state: present
  tasks:
  - name: My Batch Compute Environment
    aws_batch_compute_environment:
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
    register: aws_batch_compute_environment_action

  - name: show results
    debug:
      var: aws_batch_compute_environment_action
'''

RETURN = '''
---
output:
  description: "returns what action was taken, whether something was changed, invocation and response"
  returned: always
  sample:
    batch_compute_environment_action: none
    changed: false
    invocation:
      module_args:
        aws_access_key: ~
        aws_secret_key: ~
        bid_percentage: ~
        compute_environment_name: <name>
        compute_environment_state: ENABLED
        compute_resource_type: EC2
        desiredv_cpus: 0
        ec2_key_pair: ~
        ec2_url: ~
        image_id: ~
        instance_role: "arn:aws:iam::..."
        instance_types:
          - optimal
        maxv_cpus: 8
        minv_cpus: 0
        profile: ~
        region: us-east-1
        security_group_ids:
          - "*******"
        security_token: ~
        service_role: "arn:aws:iam::...."
        spot_iam_fleet_role: ~
        state: present
        subnets:
          - "******"
        tags:
          Environment: <name>
          Name: <name>
        type: MANAGED
        validate_certs: true
    response:
      computeEnvironmentArn: "arn:aws:batch:...."
      computeEnvironmentName: <name>
      computeResources:
        desiredvCpus: 0
        instanceRole: "arn:aws:iam::..."
        instanceTypes:
          - optimal
        maxvCpus: 8
        minvCpus: 0
        securityGroupIds:
          - "******"
        subnets:
          - "*******"
        tags:
          Environment: <name>
          Name: <name>
        type: EC2
      ecsClusterArn: "arn:aws:ecs:....."
      serviceRole: "arn:aws:iam::..."
      state: ENABLED
      status: VALID
      statusReason: "ComputeEnvironment Healthy"
      type: MANAGED
  type: dict
'''

from ansible.module_utils._text import to_native
from ansible.module_utils.aws.batch import AWSConnection
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, HAS_BOTO3
from ansible.module_utils.ec2 import snake_dict_to_camel_dict, camel_dict_to_snake_dict
import re
import traceback

try:
    from botocore.exceptions import ClientError, ParamValidationError, MissingParametersError
except ImportError:
    pass  # Handled by HAS_BOTO3


# ---------------------------------------------------------------------------------------------------
#
#   Helper Functions & classes
#
# ---------------------------------------------------------------------------------------------------

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

    compute_environment_name = module.params['compute_environment_name']

    # validate compute environment name
    if not re.search(r'^[\w\_:]+$', compute_environment_name):
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
        if len(environments['computeEnvironments']) > 0:
            return environments['computeEnvironments'][0]
        else:
            return None
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
        module.fail_json(msg='Error creating compute environment: {0}'.format(to_native(e)),
                         exception=traceback.format_exc())

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
        module.fail_json(msg='Error removing compute environment: {0}'.format(to_native(e)),
                         exception=traceback.format_exc())
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
    update_env_response = ''

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
            if desiredv_cpus is not None and current_compute_environment['computeResources']['desiredvCpus'] != desiredv_cpus:
                compute_resources['desiredvCpus'] = desiredv_cpus
            if len(compute_resources) > 0:
                compute_kwargs['computeResources'] = compute_resources
                updates = True
            if updates:
                try:
                    if not check_mode:
                        update_env_response = aws.client().update_compute_environment(**compute_kwargs)
                    if not update_env_response:
                        module.fail_json(msg='Unable to get compute environment information after creating')
                    changed = True
                    action_taken = "updated"
                except (ParamValidationError, ClientError) as e:
                    module.fail_json(msg="Unable to update environment: {0}".format(to_native(e)),
                                     exception=traceback.format_exc())

        else:
            # Create Batch Compute Environment
            changed = create_compute_environment(module, aws)
            # Describe compute environment
            action_taken = 'added'
        response = get_current_compute_environment(module, aws)
        if not response:
            module.fail_json(msg='Unable to get compute environment information after creating')
    else:
        if current_state == 'present':
            # remove the compute environment
            changed = remove_compute_environment(module, aws)
            action_taken = 'deleted'
    return dict(changed=changed, batch_compute_environment_action=action_taken, response=response)


# ---------------------------------------------------------------------------------------------------
#
#   MAIN
#
# ---------------------------------------------------------------------------------------------------

def main():
    """
    Main entry point.

    :return dict: changed, batch_compute_environment_action, response
    """

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            state=dict(default='present', choices=['present', 'absent']),
            compute_environment_name=dict(required=True),
            type=dict(required=True, choices=['MANAGED', 'UNMANAGED']),
            compute_environment_state=dict(required=False, default='ENABLED', choices=['ENABLED', 'DISABLED']),
            service_role=dict(required=True),
            compute_resource_type=dict(required=True, choices=['EC2', 'SPOT']),
            minv_cpus=dict(type='int', required=True),
            maxv_cpus=dict(type='int', required=True),
            desiredv_cpus=dict(type='int'),
            instance_types=dict(type='list', required=True),
            image_id=dict(),
            subnets=dict(type='list', required=True),
            security_group_ids=dict(type='list', required=True),
            ec2_key_pair=dict(),
            instance_role=dict(required=True),
            tags=dict(type='dict'),
            bid_percentage=dict(type='int'),
            spot_iam_fleet_role=dict(),
            region=dict(aliases=['aws_region', 'ec2_region'])
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    # validate dependencies
    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required for this module.')

    aws = AWSConnection(module, ['batch'])

    validate_params(module, aws)

    results = manage_state(module, aws)

    module.exit_json(**camel_dict_to_snake_dict(results, ignore_list=['Tags']))


if __name__ == '__main__':
    main()
