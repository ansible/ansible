#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: aws_codedeploy_application
short_description: Creates/modifies a CodeDeploy application and deployment group
description:
  - Creates/modifies a CodeDeploy application and deployment group.
version_added: 2.6
author: Kurt Knudsen
options:
  application_name:
    description:
      - The name of the application.
    required: true
  new_application_name:
    description:
      - The new name of the application (when updating).
    required: false
  state:
    description:
      - register or de-register the application
    required: false
    choices: ['present', 'absent']
    default: present
  deployment_group:
    description:
      - The name of the deployment group.
    required: true
  new_deployment_group:
    description:
      - The new name of the deployment group (when updating).
    required: false
  deployment_style:
    description:
      - The type of deployment to use as a dict.
    required: false
  ec2_tag_filters:
    description:
      - A key/value list of EC2 tags to associate with.
    required: false
  auto_scaling_groups:
    description:
      - The name(s) of the ASG(s) to attach to.
    required: false
  deployment_config:
    description:
      - The name of the deployment configuration to use. Defaults to CodeDeployDefault.OneAtATime
    default: CodeDeployDefault.OneAtATime
  service_role_arn:
    description:
      - The ARN of the service role for CodeDeploy.
    required: true
  on_premise_filters:
    description:
      - The on-premise instance tags to filter for.
    required: false
  trigger_configs:
    description:
      - Information about the triggers to create when the deployment group is created.
    required: false
  alarm_configuration:
    description:
      - Information to add about Amazon CloudWatch alarms when the deployment group is created.
    required: false
  auto_rollback_config:
    description:
      - Configuration information for an automatic rollback that is added when a deployment group is created.
    required: false
  bg_deployment_config:
    description:
      - Information about blue/green deployment options for a deployment group.
    required: false
  load_balance_info:
    description:
      - Information about the load balancer used in a deployment.
    required: false
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create a CodeDeploy application with a deployment group and an IN_PLACE deployment style.
- aws_codedeploy_application:
  application_name: TestApplication
  deployment_group: test_application_group
  deployment_style:
    deploymentType: "IN_PLACE"
    deploymentOption: "WITHOUT_TRAFFIC_CONTROL"
  service_role_arn: "arn:aws:iam::aws:policy/service-role/AWSCodeDeployRole"

- aws_codedeploy_application:
  application_name: TestApplication
  deployment_group: test_application_group
  deployment_style:
    deploymentType: "IN_PLACE"
    deploymentOption: "WITHOUT_TRAFFIC_CONTROL"
  service_role_arn: "arn:aws:iam::aws:policy/service-role/AWSCodeDeployRole"
  auto_scaling_groups: Test-Application-ASG
  deployment_config: CodeDeployDefault.AllAtOnce

- aws_codedeploy_application:
  application_name: TestApplication
  new_application_name: TestApplicationV1
  deployment_group: test_application_group
  new_deployment_group: test_application_v1
  deployment_style:
    deploymentType: "IN_PLACE"
    deploymentOption: "WITH_TRAFFIC_CONTROL"
  service_role_arn: "arn:aws:iam::aws:policy/service-role/AWSCodeDeployRole"
  deployment_config: CodeDeployDefault.OneAtATime
  load_balance_info:
    elbInfoList:
      - MyClassicLoadBalancer
'''

RETURN = '''
application:
  description: Information regarding the CodeDeploy application.
  type: complex
  returned: success
  contains:
    application_id:
      description: The application ID.
      type: string
      sample: "81293494"
    application_name:
      description: The application name.
      type: string
      sample: "TestApplication"
    create_time:
      description: The time at which the application was created.
      type: datetime
      sample: 2017-05-30 010:00:00-05:00
    linked_to_github:
      description: True if the user has authenticated with GitHub for the specified application; otherwise, false.
      type: boolean
      sample: false
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, ec2_argument_spec, camel_dict_to_snake_dict
from ansible.module_utils.aws.core import AnsibleAWSModule
import traceback

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def get_codedeploy_application(client, name, module):
    """Get the details of the CodeDeploy application."""
    try:
        return client.get_application(applicationName=name)
    except (ClientError, NoCredentialsError) as e:
        if e.response['Error']['Code'] == 'ApplicationDoesNotExistException':
            return None
        else:
            module.fail_json_aws(e, "Could not get CodeDeploy application.")
    return None


def get_codedeploy_application_deployment_group(client, name, deployment_group, module):
    """Get the details of the CodeDeploy deployment group."""
    try:
        return client.get_deployment_group(applicationName=name, deploymentGroupName=deployment_group)
    except (ClientError, BotoCoreError) as e:
        if e.response['Error']['Code'] == 'ApplicationDoesNotExistException':
            return None
        if e.response['Error']['Code'] == 'DeploymentGroupDoesNotExistException':
            return None
        else:
            module.fail_json_aws(e, "Could not get CodeDeploy application deployment group.")
    return None


def create_codedeploy_deployment_group(client, name, deployment_group, deployment_config_name, ec2_tag_filters, on_premises_filters, auto_scaling_groups,
                                       service_role_arn, trigger_configs, alarm_config, auto_rollback_config, deployment_style, bluegreen_deployment_config,
                                       load_balancer_info, module):
    """Create a CodeDeploy deployment group for the application."""
    changed = False
    try:
        dg_params = dict()
        if deployment_config_name is not None:
            dg_params['deploymentConfigName'] = deployment_config_name
        if ec2_tag_filters is not None:
            dg_params['ec2TagFilters'] = ec2_tag_filters
        if on_premises_filters is not None:
            dg_params['onPremisesInstanceTagFilters'] = on_premises_filters
        if auto_scaling_groups is not None:
            dg_params['autoScalingGroups'] = auto_scaling_groups
        if trigger_configs is not None:
            dg_params['triggerConfigurations'] = trigger_configs
        if alarm_config is not None:
            dg_params['alarmConfiguration'] = alarm_config
        if auto_rollback_config is not None:
            dg_params['autoRollbackConfiguration'] = auto_rollback_config
        if deployment_style is not None:
            dg_params['deploymentStyle'] = deployment_style
        if bluegreen_deployment_config is not None:
            dg_params['blueGreenDeploymentConfiguration'] = bluegreen_deployment_config
        if load_balancer_info is not None:
            dg_params['loadBalancerInfo'] = load_balancer_info
        response = client.create_deployment_group(
            applicationName=name,
            deploymentGroupName=deployment_group,
            serviceRoleArn=service_role_arn,
            **dg_params)
        changed = True
    except (ClientError, NoCredentialsError) as e:
        if e.response['Error']['Code'] == 'ApplicationDoesNotExistException':
            return None
        if e.response['Error']['Code'] == 'DeploymentGroupDoesNotExistException':
            return None
        else:
            module.fail_json_aws(e, "Could not create CodeDeploy deployment group.")
    return changed


def create_codedeploy_application(client, name, deployment_group, new_deployment_group_name, deployment_config, ec2_tag_filters, on_premises_filters,
                                  auto_scaling_groups, service_role_arn, trigger_configs, alarm_configuration, auto_rollback_config, deployment_style,
                                  bluegreen_deployment_config, load_balancer_info, module):
    """Create a CodeDeploy application. Return true if changed, else false"""
    changed = False
    try:
        response = client.create_application(applicationName=name)
        # Check if the deployment group already exists, if it does, update it.
        has_deployment_group = get_codedeploy_application_deployment_group(client, name, deployment_group, module)
        if not has_deployment_group:
            create_codedeploy_deployment_group(client, name, deployment_group, deployment_config, ec2_tag_filters, on_premises_filters, auto_scaling_groups,
                                               service_role_arn, trigger_configs, alarm_configuration, auto_rollback_config, deployment_style,
                                               bluegreen_deployment_config, load_balancer_info, module)
            changed = True
        else:
            changed = update_codedeploy_deployment_group(client, name, deployment_group, new_deployment_group_name, deployment_config, ec2_tag_filters,
                                                         on_premises_filters, auto_scaling_groups, service_role_arn, trigger_configs, alarm_configuration,
                                                         auto_rollback_config, deployment_style, bluegreen_deployment_config, load_balancer_info, module)
    except ClientError as e:
        module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))

    cda = get_codedeploy_application(client, name, module)
    module.exit_json(changed=changed, **camel_dict_to_snake_dict(cda))


def update_codedeploy_deployment_group(client, name, current_deployment_group_name, new_deployment_group_name, deployment_config, ec2_tag_filters,
                                       on_premises_filters, auto_scaling_groups, service_role_arn, trigger_configs, alarm_configuration, auto_rollback_config,
                                       deployment_style, bluegreen_deployment_config, load_balancer_info, module):
    """Update a CodeDeploy deployment group. Return true if changed, else false."""
    changed = False
    try:
        dg_params = dict()
        if deployment_config is not None:
            dg_params['deploymentConfigName'] = deployment_config
        if new_deployment_group_name is not None:
            dg_params['newDeploymentGroupName'] = new_deployment_group_name
        if ec2_tag_filters is not None:
            dg_params['ec2TagFilters'] = ec2_tag_filters
        if on_premises_filters is not None:
            dg_params['onPremisesInstanceTagFilters'] = on_premises_filters
        if auto_scaling_groups is not None:
            dg_params['autoScalingGroups'] = auto_scaling_groups
        if trigger_configs is not None:
            dg_params['triggerConfigurations'] = trigger_configs
        if alarm_configuration is not None:
            dg_params['alarmConfiguration'] = alarm_configuration
        if auto_rollback_config is not None:
            dg_params['autoRollbackConfiguration'] = auto_rollback_config
        if deployment_style is not None:
            dg_params['deploymentStyle'] = deployment_style
        if bluegreen_deployment_config is not None:
            dg_params['blueGreenDeploymentConfiguration'] = bluegreen_deployment_config
        if load_balancer_info is not None:
            dg_params['loadBalancerInfo'] = load_balancer_info

        response = client.update_deployment_group(
            applicationName=name,
            currentDeploymentGroupName=current_deployment_group_name,
            serviceRoleArn=service_role_arn,
            **dg_params)
        changed = True
    except ClientError as e:
        changed = False
        module.fail_json_aws(e, "Could not update CodeDeploy deployment group.")
    return changed


def update_codedeploy_application(client, name, new_name, module):
    """Update a CodeDeploy application. Return true if changed, else false."""
    changed = False
    try:
        response = client.update_application(
            applicationName=name,
            newApplicationName=new_name)
        changed = True
    except ClientError as e:
        module.fail_json_aws(e, "Could not update CodeDeploy application name.")
    return changed


def delete_codedeploy_application(client, name, module):
    """Delete a CodeDeploy application. Return true if changed, else false"""
    try:
        response = client.delete_application(applicationName=name)
        return True
    except ClientError as e:
        module.fail_json_aws(e, "Could not delete CodeDeploy application.")


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        application_name=dict(required=True, type='str'),
        deployment_group=dict(required=True, type='str'),
        deployment_style=dict(required=True, type="dict"),
        service_role_arn=dict(required=True, type='str'),
        state=dict(required=False, default='present', choices=['present', 'absent'], type='str'),
        deployment_config=dict(required=False, default='CodeDeployDefault.OneAtATime', type='str'),
        new_application_name=dict(required=False, type='str', default=None),
        new_deployment_group=dict(required=False, type='str', default=None),
        ec2_tag_filters=dict(required=False, type='list', default=None),
        on_premise_filters=dict(required=False, type='list', default=None),
        auto_scaling_groups=dict(required=False, type='list', default=None),
        trigger_configs=dict(required=False, type='list', default=None),
        alarm_configuration=dict(required=False, type='dict', default=None),
        auto_rollback_config=dict(required=False, type='dict', default=None),
        bg_deployment_config=dict(required=False, type='dict', default=None),
        load_balance_info=dict(required=False, type='dict', default=None)
    ))
    module = AnsibleModule(argument_spec=argument_spec)

    name = module.params.get('application_name')
    deployment_group = module.params.get('deployment_group')
    deployment_style = module.params.get('deployment_style')
    service_role_arn = module.params.get('service_role_arn')
    state = module.params.get('state')
    new_application_name = module.params.get('new_application_name')
    new_deployment_group = module.params.get('new_deployment_group')
    auto_scaling_groups = module.params.get('auto_scaling_groups')
    trigger_configs = module.params.get('trigger_configs')
    deployment_config = module.params.get('deployment_config')
    ec2_tag_filters = module.params.get('ec2_tag_filters')
    on_premise_filters = module.params.get('on_premise_filters')
    alarm_configuration = module.params.get('alarm_configuration')
    auto_rollback_config = module.params.get('auto_rollback_config')
    bg_deployment_config = module.params.get('bg_deployment_config')
    load_balance_info = module.params.get('load_balance_info')

    if not HAS_BOTO3:
        module.fail_json(msg='boto required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
    connection = boto3_conn(module, conn_type='client', resource='codedeploy', region=region, endpoint=ec2_url, **aws_connect_params)

    changed = False
    if state == 'present':
        # Check if the application already exists, if it does, update it.
        has_application = get_codedeploy_application(connection, name, module)
        # Check if the deployment group already exists, if it does, update it.
        has_deployment_group = get_codedeploy_application_deployment_group(connection, name, deployment_group, module)
        if not has_application:
            cd_properties = create_codedeploy_application(
                connection,
                name,
                deployment_group,
                new_deployment_group,
                deployment_config,
                ec2_tag_filters,
                on_premise_filters,
                auto_scaling_groups,
                service_role_arn,
                trigger_configs,
                alarm_configuration,
                auto_rollback_config,
                deployment_style,
                bg_deployment_config,
                load_balance_info,
                module)
        else:
            # Update the application name if a new name was given.
            if new_application_name:
                cd_properties = update_codedeploy_application(connection, name, new_application_name, module)
        if has_deployment_group:
            cd_properties = update_codedeploy_deployment_group(
                connection,
                name,
                deployment_group,
                new_deployment_group,
                deployment_config,
                ec2_tag_filters,
                on_premise_filters,
                auto_scaling_groups,
                service_role_arn,
                trigger_configs,
                alarm_configuration,
                auto_rollback_config,
                deployment_style,
                bg_deployment_config,
                load_balance_info,
                module)
        else:
            cd_properties = create_codedeploy_deployment_group(
                connection,
                name,
                deployment_group,
                deployment_config,
                ec2_tag_filters,
                on_premise_filters,
                auto_scaling_groups,
                service_role_arn,
                trigger_configs,
                alarm_configuration,
                auto_rollback_config,
                deployment_style,
                bg_deployment_config,
                load_balance_info,
                module)
    elif state == 'absent':
        changed = delete_codedeploy_application(connection, name, module)
        module.exit_json(changed=changed)
    cda = get_codedeploy_application(connection, name, module)
    module.exit_json(changed=changed, **camel_dict_to_snake_dict(cda))

if __name__ == '__main__':
    main()
