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
ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'curated'}


DOCUMENTATION = """
---
module: ec2_asg
short_description: Create or delete AWS Autoscaling Groups
description:
  - Can create or delete AWS Autoscaling Groups
  - Works with the ec2_lc module to manage Launch Configurations
version_added: "1.6"
author: "Gareth Rushgrove (@garethr)"
options:
  state:
    description:
      - register or deregister the instance
    required: false
    choices: ['present', 'absent']
    default: present
  name:
    description:
      - Unique name for group to be created or deleted
    required: true
  load_balancers:
    description:
      - List of ELB names to use for the group
    required: false
  target_group_arns:
    description:
      - List of Target Group ARNs to use for the group
    required: false
    version_added: "2.4"
  availability_zones:
    description:
      - List of availability zone names in which to create the group.  Defaults to all the availability zones in the region if vpc_zone_identifier is not set.
    required: false
  launch_config_name:
    description:
      - Name of the Launch configuration to use for the group. See the ec2_lc module for managing these.
    required: true
  min_size:
    description:
      - Minimum number of instances in group, if unspecified then the current group value will be used.
    required: false
  max_size:
    description:
      - Maximum number of instances in group, if unspecified then the current group value will be used.
    required: false
  placement_group:
    description:
      - Physical location of your cluster placement group created in Amazon EC2.
    required: false
    version_added: "2.3"
    default: None
  desired_capacity:
    description:
      - Desired number of instances in group, if unspecified then the current group value will be used.
    required: false
  replace_all_instances:
    description:
      - In a rolling fashion, replace all instances with an old launch configuration with one from the current launch configuration.
    required: false
    version_added: "1.8"
    default: False
  replace_batch_size:
    description:
      - Number of instances you'd like to replace at a time.  Used with replace_all_instances.
    required: false
    version_added: "1.8"
    default: 1
  replace_instances:
    description:
      - List of instance_ids belonging to the named ASG that you would like to terminate and be replaced with instances matching the current launch
        configuration.
    required: false
    version_added: "1.8"
    default: None
  lc_check:
    description:
      - Check to make sure instances that are being replaced with replace_instances do not already have the current launch_config.
    required: false
    version_added: "1.8"
    default: True
  vpc_zone_identifier:
    description:
      - List of VPC subnets to use
    required: false
    default: None
  tags:
    description:
      - A list of tags to add to the Auto Scale Group. Optional key is 'propagate_at_launch', which defaults to true.
    required: false
    default: None
    version_added: "1.7"
  health_check_period:
    description:
      - Length of time in seconds after a new EC2 instance comes into service that Auto Scaling starts checking its health.
    required: false
    default: 500 seconds
    version_added: "1.7"
  health_check_type:
    description:
      - The service you want the health status from, Amazon EC2 or Elastic Load Balancer.
    required: false
    default: EC2
    version_added: "1.7"
    choices: ['EC2', 'ELB']
  default_cooldown:
    description:
      - The number of seconds after a scaling activity completes before another can begin.
    required: false
    default: 300 seconds
    version_added: "2.0"
  wait_timeout:
    description:
      - how long before wait instances to become viable when replaced.  Used in conjunction with instance_ids option.
    default: 300
    version_added: "1.8"
  wait_for_instances:
    description:
      - Wait for the ASG instances to be in a ready state before exiting.  If instances are behind an ELB, it will wait until the ELB determines all
        instances have a lifecycle_state of  "InService" and  a health_status of "Healthy".
    version_added: "1.9"
    default: yes
    required: False
  termination_policies:
    description:
        - An ordered list of criteria used for selecting instances to be removed from the Auto Scaling group when reducing capacity.
        - For 'Default', when used to create a new autoscaling group, the "Default"i value is used. When used to change an existent autoscaling group, the
          current termination policies are maintained.
    required: false
    default: Default
    choices: ['OldestInstance', 'NewestInstance', 'OldestLaunchConfiguration', 'ClosestToNextInstanceHour', 'Default']
    version_added: "2.0"
  notification_topic:
    description:
      - A SNS topic ARN to send auto scaling notifications to.
    default: None
    required: false
    version_added: "2.2"
  notification_types:
    description:
      - A list of auto scaling events to trigger notifications on.
    default:
        - 'autoscaling:EC2_INSTANCE_LAUNCH'
        - 'autoscaling:EC2_INSTANCE_LAUNCH_ERROR'
        - 'autoscaling:EC2_INSTANCE_TERMINATE'
        - 'autoscaling:EC2_INSTANCE_TERMINATE_ERROR'
    required: false
    version_added: "2.2"
  suspend_processes:
    description:
      - A list of scaling processes to suspend.
    required: False
    default: []
    choices: ['Launch', 'Terminate', 'HealthCheck', 'ReplaceUnhealthy', 'AZRebalance', 'AlarmNotification', 'ScheduledActions', 'AddToLoadBalancer']
    version_added: "2.3"
extends_documentation_fragment:
    - aws
    - ec2
"""

EXAMPLES = '''
# Basic configuration

- ec2_asg:
    name: special
    load_balancers: [ 'lb1', 'lb2' ]
    availability_zones: [ 'eu-west-1a', 'eu-west-1b' ]
    launch_config_name: 'lc-1'
    min_size: 1
    max_size: 10
    desired_capacity: 5
    vpc_zone_identifier: [ 'subnet-abcd1234', 'subnet-1a2b3c4d' ]
    tags:
      - environment: production
        propagate_at_launch: no

# Rolling ASG Updates

# Below is an example of how to assign a new launch config to an ASG and terminate old instances.
#
# All instances in "myasg" that do not have the launch configuration named "my_new_lc" will be terminated in
# a rolling fashion with instances using the current launch configuration, "my_new_lc".
#
# This could also be considered a rolling deploy of a pre-baked AMI.
#
# If this is a newly created group, the instances will not be replaced since all instances
# will have the current launch configuration.

- name: create launch config
  ec2_lc:
    name: my_new_lc
    image_id: ami-lkajsf
    key_name: mykey
    region: us-east-1
    security_groups: sg-23423
    instance_type: m1.small
    assign_public_ip: yes

- ec2_asg:
    name: myasg
    launch_config_name: my_new_lc
    health_check_period: 60
    health_check_type: ELB
    replace_all_instances: yes
    min_size: 5
    max_size: 5
    desired_capacity: 5
    region: us-east-1

# To only replace a couple of instances instead of all of them, supply a list
# to "replace_instances":

- ec2_asg:
    name: myasg
    launch_config_name: my_new_lc
    health_check_period: 60
    health_check_type: ELB
    replace_instances:
    - i-b345231
    - i-24c2931
    min_size: 5
    max_size: 5
    desired_capacity: 5
    region: us-east-1
'''

import time
import logging as log
import traceback

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import (get_aws_connection_info,
                                      ec2_argument_spec,
                                      boto3_inventory_conn)
log.getLogger('boto').setLevel(log.CRITICAL)
log.basicConfig(
    filename='/tmp/ansible_ec2_asg.log',
    level=log.DEBUG,
    format='%(asctime)s: %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p',
)

try:
    import boto3
    import botocore
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

ASG_ATTRIBUTES = (
    'availability_zones', 'default_cooldown', 'desired_capacity',
    'health_check_period', 'health_check_type', 'launch_config_name',
    'load_balancers', 'max_size', 'min_size', 'name', 'placement_group',
    'termination_policies', 'vpc_zone_identifier',
)

ASG_MAPPING = {
    'availability_zones': 'AvailabilityZones',
    'default_cooldown': 'DefaultCooldown',
    'desired_capacity': 'DesiredCapacity',
    'health_check_period': 'HealthCheckGracePeriod',
    'health_check_type': 'HealthCheckType',
    'launch_config_name': 'LaunchConfigurationName',
    'load_balancers': 'LoadBalancerNames',
    'max_size': 'MaxSize',
    'min_size': 'MinSize',
    'name': 'AutoScalingGroupName',
    'placement_group': 'PlacementGroup',
    'termination_policies': 'TerminationPolicies',
    'vpc_zone_identifier': 'VPCZoneIdentifier',
    'tags': 'Tags',
    'instances': 'Instances',
}

INSTANCE_ATTRIBUTES = ('instance_id', 'health_status',
                       'lifecycle_state', 'launch_config_name')


def enforce_required_arguments(module):
    ''' As many arguments are not required for autoscale group deletion
        they cannot be mandatory arguments for the module, so we enforce
        them here '''
    missing_args = []
    for arg in ('min_size', 'max_size', 'launch_config_name'):
        if module.params[arg] is None:
            missing_args.append(arg)
    if missing_args:
        module.fail_json(
            msg="Missing required arguments for autoscaling "
            "group create/update: %s" % ",".join(missing_args)
        )


def get_client(client_type, module):
    try:
        region, _, aws_connect_params = get_aws_connection_info(module,
                                                                boto3=True)
        client = boto3_inventory_conn('client', client_type,
                                      region, **aws_connect_params)
    except botocore.exceptions.NoCredentialsError as e:
        module.fail_json(msg=str(e))
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))

    if not client:
        module.fail_json(
            msg="failed to connect to AWS for the given region: %s for %s" %
            (str(region), str(client_type)),
        )

    return client


def get_asg(group_name, module):
    asg = get_client('autoscaling', module).describe_auto_scaling_groups(
        AutoScalingGroupNames=[group_name],
    )['AutoScalingGroups']
    if len(asg):
        return asg[0]
    else:
        return {}


def get_properties(autoscaling_group, instance_details=True):
    # log.debug("Extracting properties from {0}".format(autoscaling_group))
    properties = dict(
        (attr, autoscaling_group[ASG_MAPPING[attr]])
        for attr in ASG_ATTRIBUTES
        if ASG_MAPPING[attr] in autoscaling_group
    )

    # Sort Items for easy comparison
    if 'availability_zones' in properties:
        properties['availability_zones'].sort()
    if 'load_balancers' in properties:
        properties['load_balancers'].sort()
    if 'termination_policies' in properties:
        properties['termination_policies'].sort()
    if 'vpc_zone_identifier' in properties:
        properties['vpc_zone_identifier'] = ",".join(
            sorted(properties['vpc_zone_identifier'].split(','))
        )

    if 'Tags' in autoscaling_group:
        properties['tags'] = dict(
            (x['Key'], [x['Value'], x['PropagateAtLaunch']])
            for x in autoscaling_group['Tags']
        )

    if 'SuspendedProcesses' in autoscaling_group:
        try:
            # When received from AWS it's a list of dicts
            properties['suspended_processes'] = [
                x['ProcessName']
                for x in autoscaling_group['SuspendedProcesses']
            ]
        except AttributeError:
            # When sent to AWS it's a list of strings
            properties['suspended_processes'] = \
                autoscaling_group['SuspendedProcesses']

    if instance_details and 'Instances' in autoscaling_group:
        properties['viable_instances'] = sum(
            i['HealthStatus'] == "Healthy" and
            i['LifecycleState'] == 'InService'
            for i in autoscaling_group['Instances']
        )
        properties['healthy_instances'] = sum(
            i['HealthStatus'] == "Healthy"
            for i in autoscaling_group['Instances']
        )
        properties['unhealthy_instances'] = sum(
            i['HealthStatus'] != "Healthy"
            for i in autoscaling_group['Instances']
        )
        properties['in_service_instances'] = sum(
            i['LifecycleState'] == "InService"
            for i in autoscaling_group['Instances']
        )
        properties['terminating_instances'] = sum(
            i['LifecycleState'] == "Terminating"
            for i in autoscaling_group['Instances']
        )
        properties['pending_instances'] = sum(
            i['LifecycleState'] == "Pending"
            for i in autoscaling_group['Instances']
        )

        properties['instances'] = sorted([
            i['InstanceId'] for i in autoscaling_group['Instances']
        ])

        properties['instance_facts'] = dict(
            (i['InstanceId'], {
                'health_status': i.get('HealthStatus',
                                       'Unknown'),
                'lifecycle_state': i.get('LifecycleState',
                                         'Unknown'),
                'launch_config_name': i.get(
                    'LaunchConfigurationName', ''
                ),
            }) for i in autoscaling_group['Instances']
        )

    return properties


def asg_diff(asg_1, asg_2):
    props_1 = get_properties(asg_1, False)
    props_2 = get_properties(asg_2, False)

    return props_1 != props_2


def elb_dreg(module, group_name, instance_id):
    as_group = get_asg(group_name, module)

    if as_group['LoadBalancerNames'] and as_group['HealthCheckType'] == 'ELB':
        client = get_client('elb', module)
    else:
        return

    for lb_name in as_group['LoadBalancerNames']:
        log.debug("De-registering {0} from ELB {1}".format(instance_id,
                                                           lb_name))
        client.deregister_instances_from_load_balancer(
            LoadBalancerName=lb_name,
            Instances=[{'InstanceId': instance_id}],
        )

    instances_in_service = 1
    wait_timeout = time.time() + module.params.get('wait_timeout')

    while wait_timeout > time.time() and instances_in_service > 0:
        instances_in_service = 0
        for lb_name in as_group['LoadBalancerNames']:
            for i in client.describe_instance_health(
                LoadBalancerName=lb_name,
                Instances=[{'InstanceId': instance_id}],
            ):
                if i['State'] == "InService":
                    instances_in_service += 1
                    log.debug("Waiting on {0}: {1}, {2}".format(
                        i['InstanceId'],
                        i['State'],
                        i['Description'],
                    ))
        if instances_in_service > 0:
            time.sleep(10)

    if wait_timeout <= time.time():
        # waiting took too long
        module.fail_json(
            msg="Waited too long for instance to deregister. {0}".format(
                time.asctime(),
            ),
        )


def elbv2_dreg(module, group_name, instance_id):
    as_group = get_asg(group_name, module)

    if as_group['TargetGroupARNs'] and as_group['HealthCheckType'] == 'ELB':
        client = get_client('elbv2', module)
    else:
        return

    for target_arn in as_group['TargetGroupARNs']:
        client.deregister_targets(
            TargetGroupArn=target_arn,
            Targets=[{'Id': instance_id}],
        )
        log.debug("De-registering {0} from target arn {1}".format(
            instance_id, target_arn,
        ))

    instances_in_service = 1
    wait_timeout = time.time() + module.params.get('wait_timeout')

    while wait_timeout > time.time() and instances_in_service > 0:
        instances_in_service = 0
        for target_arn in as_group['TargetGroupARNs']:
            for i in client.describe_target_health(
                TargetGroupArn=target_arn,
                Targets=[{'InstanceId': instance_id}],
            ):
                if i['State'] == "InService":
                    instances_in_service += 1
                    log.debug("Waiting on {0}: {1}, {2}".format(
                        i['InstanceId'],
                        i['State'],
                        i['Description'],
                    ))
        if instances_in_service > 0:
            time.sleep(10)

    if wait_timeout <= time.time():
        # waiting took too long
        module.fail_json(
            msg="Waited too long for instance to deregister. {0}".format(
                time.asctime(),
            )
        )


def elb_healthy(module, group_name):
    healthy_instances = set()

    as_group = get_asg(group_name, module)

    elb_client = get_client('elb', module)
    props = get_properties(as_group)
    # get healthy, inservice instances from ASG
    instances = []
    for instance, settings in props['instance_facts'].items():
        if settings['lifecycle_state'] == 'InService' and \
                settings['health_status'] == 'Healthy':
            instances.append({'InstanceId': instance})

    log.debug(
        "ASG considers the following instances InService and "
        "Healthy: {0}".format(instances),
    )
    log.debug("ELB instance status:")
    for lb_name in as_group['LoadBalancerNames']:
        # we catch a race condition that sometimes happens if the instance
        # exists in the ASG but has not yet show up in the ELB
        try:
            lb_instances = elb_client.describe_instance_health(
                LoadBalancerName=lb_name,
                Instances=instances,
            )
        except botocore.exceptions.ClientError as e:
            if e.error_code == 'InvalidInstance':
                return None

            module.fail_json(msg=str(e))

        for i in lb_instances:
            if i['State'] == "InService":
                healthy_instances.add(i['InstanceId'])
            log.debug("{0}: {1}".format(i['InstanceId'], i['State']))
    return len(healthy_instances)


def elbv2_healthy(module, group_name):
    healthy_instances = set()
    as_group = get_asg(group_name, module)
    props = get_properties(as_group)
    # get healthy, inservice targets from ASG
    targets = []
    for instance, settings in props['instance_facts'].items():
        if settings['lifecycle_state'] == 'InService' and \
                settings['health_status'] == 'Healthy':
            targets.append({'Id': instance})
    log.debug(
        "ASG considers the following targets InService and "
        "Healthy: {0}".format(targets),
    )
    log.debug("ELB instance status:")
    client = get_client('elbv2', module)
    for target in as_group['TargetGroupARNs']:
        # we catch a race condition that sometimes happens if the instance
        # exists in the ASG but has not yet show up in the ELB
        try:
            target_instances = client.describe_target_health(
                TargetGroupArn=target,
                Targets=targets,
            ).get('TargetHealthDescriptions', [])
        except botocore.exceptions.ClientError as e:
            if e.error_code == 'InvalidInstance':
                return None

            module.fail_json(msg=str(e))

        log.debug("target_instances = {0}".format(
            target_instances,
        ))
        for i in target_instances:
            log.debug("{0}: {1}".format(
                i['Target']['Id'],
                i['TargetHealth']['State'],
            ))
            if i['TargetHealth']['State'] == "InService":
                healthy_instances.add(i['Target']['Id'])

    return len(healthy_instances)


def wait_for_elb(module, group_name):
    wait_timeout = module.params.get('wait_timeout')

    # if the health_check_type is ELB, we want to query the ELBs directly for
    # instance status as to avoid health_check_grace period that is awarded to
    # ASG instances
    as_group = get_asg(group_name, module)

    log.debug("wait_for_elb with {0}".format(as_group))
    if as_group['LoadBalancerNames'] and as_group['HealthCheckType'] == 'ELB':
        log.debug("Waiting for ELB to consider instances healthy.")
        wait_timeout = time.time() + wait_timeout
        healthy_instances = elb_healthy(module, group_name)

        while healthy_instances < as_group['MinSize'] and \
                wait_timeout > time.time():
            healthy_instances = elb_healthy(module, group_name)
            log.debug("ELB thinks {0} instances are healthy.".format(
                healthy_instances,
            ))
            if healthy_instances < as_group['MinSize']:
                time.sleep(10)

        if wait_timeout <= time.time():
            # waiting took too long
            module.fail_json(
                msg="Waited too long for ELB instances to be healthy. %s" %
                time.asctime(),
            )
        log.debug(
            "Waiting complete. ELB thinks {0} instances are healthy.".format(
                healthy_instances,
            ),
        )


def wait_for_elbv2(module, group_name):
    wait_timeout = module.params.get('wait_timeout')

    as_group = get_asg(group_name, module)

    if as_group['TargetGroupARNs'] and as_group['HealthCheckType'] == 'ELB':
        log.debug("Waiting for ELB target to consider instances healthy.")

        wait_timeout = time.time() + wait_timeout
        healthy_instances = elbv2_healthy(module, group_name)

        while healthy_instances < as_group['MinSize'] and \
                wait_timeout > time.time():
            healthy_instances = elbv2_healthy(module, group_name)
            log.debug("ELB target thinks {0} instances are healthy.".format(
                healthy_instances,
            ))
            if healthy_instances < as_group['MinSize']:
                time.sleep(10)

        if wait_timeout <= time.time():
            # waiting took too long
            module.fail_json(
                msg="Waited too long for ELB instances to be healthy. %s" %
                time.asctime(),
            )
        log.debug(
            "Waiting complete. ELB thinks {0} instances are healthy.".format(
                healthy_instances,
            ),
        )


def perform_asg_change(asg_def, module):
    log.debug("Performing Autoscaling Change {0}".format(asg_def))
    client = get_client('autoscaling', module)
    changed = False

    # Create has all params, update does not have following keys
    filter_out = [
        'AutoScalingGroupARN',
        'CreatedTime',
        'EnabledMetrics',
        'Instances',
        'LoadBalancerNames',
        'SuspendedProcesses',
        'Tags',
        'TargetGroupARNs',
    ]

    # Get curent autoscaling group details
    existing_group_details = get_asg(
        asg_def['AutoScalingGroupName'],
        module,
    )

    if not existing_group_details:
        changed = True
        log.debug("zxc: Creating autoscaling group {0}".format(
            asg_def,
        ))
        try:
            create_asg_def = asg_def.copy()
            suspended_processes = create_asg_def.pop('SuspendedProcesses', [])
            if create_asg_def.get('PlacementGroup') is None:
                create_asg_def.pop('PlacementGroup', None)
            client.create_auto_scaling_group(**create_asg_def)
            suspend_processes(suspended_processes, module)

            # Give time for AWS to complete the request before checking back
            time.sleep(10)
        except Exception as e:
            module.fail_json(
                msg="Failed to create Autoscaling Group: %s" %
                str(e),
                exception=traceback.format_exc(e),
            )

        existing_group_details = get_asg(
            asg_def['AutoScalingGroupName'],
            module,
        )

    existing_group = dict(
        (x, y) for x, y in existing_group_details.items()
        if x not in filter_out
    )
    existing_tags = existing_group_details.get('Tags', [])
    existing_lb_names = existing_group_details.get(
        'LoadBalancerNames',
        []
    )
    existing_target_arns = existing_group_details.get(
        'TargetGroupARNs',
        []
    )
    existing_suspended_processes = existing_group_details.get(
        'SuspendedProcesses',
        []
    )

    requested_update_group = dict(
        (x, y) for x, y in asg_def.items() if x not in filter_out
    )

    if requested_update_group.get('PlacementGroup') is None:
        requested_update_group.pop('PlacementGroup', None)

    requested_update_tags = asg_def.get('Tags', [])
    requested_update_lb_names = asg_def.get('LoadBalancerNames', [])
    requested_update_target_arns = asg_def.get('TargetGroupARNs', [])
    requested_suspended_processes = asg_def.get('SuspendedProcesses', [])

    if asg_diff(existing_group, requested_update_group):
        changed = True
        log.debug("zxc: Updating autoscaling {0}".format(
            requested_update_group
        ))
        try:
            client.update_auto_scaling_group(**requested_update_group)
        except botocore.exceptions.ClientError as e:
            module.fail_json(
                msg="Failed to update Autoscaling Group: %s" % str(e),
                exception=traceback.format_exc(e),
            )

    else:
        log.debug("zxc: Autoscaling already configured")

    if asg_diff(existing_tags, requested_update_tags):
        log.debug("zxc: Updating tags {0}".format(
            requested_update_tags
        ))
        need_tag_names = set(
            x['Key'] for x in requested_update_tags
        )

        tags_to_delete = [
            tag for tag in existing_tags
            if tag['Key'] not in need_tag_names
        ]

        if len(tags_to_delete):
            changed = True
            try:
                client.delete_tags(Tags=tags_to_delete)
            except botocore.exceptions.ClientError as e:
                module.fail_json(
                    msg="Failed to delete tags: %s" % str(e),
                    exception=traceback.format_exc(e),
                )

        if len(requested_update_tags):
            changed = True
            try:
                client.create_or_update_tags(Tags=requested_update_tags)
            except botocore.exceptions.ClientError as e:
                module.fail_json(
                    msg="Failed to create or update tags: %s" % str(e),
                    exception=traceback.format_exc(e),
                )
    else:
        log.debug("zxc: Autoscaling tags already configured")

    if asg_diff(existing_lb_names, requested_update_lb_names):
        log.debug("zxc: Updating load balancers {0}".format(
            requested_update_lb_names
        ))

        detach_lb_names = set(
            lb for lb in existing_lb_names
            if lb not in requested_update_lb_names
        )

        if len(detach_lb_names):
            changed = True
            try:
                client.detach_load_balancers(
                    AutoScalingGroupName=asg_def['AutoScalingGroupName'],
                    LoadBalancerNames=detach_lb_names,
                )
            except botocore.exceptions.ClientError as e:
                module.fail_json(
                    msg="Failed to detach load balancers: %s" % str(e),
                    exception=traceback.format_exc(e),
                )

        if len(requested_update_lb_names):
            changed = True
            try:
                client.attach_load_balancers(
                    AutoScalingGroupName=asg_def['AutoScalingGroupName'],
                    LoadBalancerNames=detach_lb_names,
                )
            except botocore.exceptions.ClientError as e:
                module.fail_json(
                    msg="Failed to attach load balancers: %s" % str(e),
                    exception=traceback.format_exc(e),
                )
    else:
        log.debug("zxc: Autoscaling load balancers already attached")

    if asg_diff(existing_target_arns, requested_update_target_arns):
        log.debug("zxc: Updating target groups {0}".format(
            requested_update_target_arns
        ))

        detach_target_arns = set(
            lb for lb in existing_target_arns
            if lb not in requested_update_target_arns
        )

        if len(detach_target_arns):
            changed = True
            try:
                client.detach_load_balancer_target_groups(
                    AutoScalingGroupName=asg_def['AutoScalingGroupName'],
                    TargetGroupARNs=detach_target_arns,
                )
            except botocore.exceptions.ClientError as e:
                module.fail_json(
                    msg="Failed to detach target groups: %s" % str(e),
                    exception=traceback.format_exc(e),
                )

        if len(requested_update_target_arns):
            changed = True
            try:
                client.attach_load_balancer_target_groups(
                    AutoScalingGroupName=asg_def['AutoScalingGroupName'],
                    TargetGroupARNs=detach_target_arns,
                )
            except botocore.exceptions.ClientError as e:
                module.fail_json(
                    msg="Failed to attach target groups: %s" % str(e),
                    exception=traceback.format_exc(e),
                )
    else:
        log.debug("zxc: Autoscaling target groups already in requested state")

    if asg_diff(existing_suspended_processes, requested_suspended_processes):
        log.debug("zxc: Updating suspend processes {0}".format(
            requested_suspended_processes
        ))

        changed |= suspend_processes(requested_suspended_processes, module)
    else:
        log.debug("zxc: Suspend processes already in requested state")

    if changed:
        # Give time for AWS to complete the request before checking state
        time.sleep(10)

    return changed


def suspend_processes(processes_to_suspend, module):
    changed = False
    client = get_client('autoscaling', module)
    group_name = module.params.get('name')

    # Get current autoscaling group details
    asg_def = get_asg(group_name, module)
    asg_props = get_properties(asg_def)
    currently_suspended = set(asg_props['suspended_processes'])

    processes_to_resume = list(currently_suspended - set(processes_to_suspend))

    if processes_to_resume:
        changed = True
        client.resume_processes(
            AutoScalingGroupName=group_name,
            ScalingProcesses=processes_to_resume,
        )

    if processes_to_suspend:
        changed = True
        client.suspend_processes(
            AutoScalingGroupName=group_name,
            ScalingProcesses=processes_to_suspend,
        )

    return changed


def create_autoscaling_group(module):
    group_name = module.params.get('name')
    load_balancers = module.params['load_balancers']
    target_group_arns = module.params['target_group_arns']
    availability_zones = module.params['availability_zones']
    launch_config_name = module.params.get('launch_config_name')
    min_size = module.params['min_size']
    max_size = module.params['max_size']
    placement_group = module.params.get('placement_group')
    desired_capacity = module.params.get('desired_capacity')
    vpc_zone_identifier = module.params.get('vpc_zone_identifier')
    set_tags = module.params.get('tags')
    health_check_period = module.params.get('health_check_period')
    health_check_type = module.params.get('health_check_type')
    default_cooldown = module.params.get('default_cooldown')
    termination_policies = module.params.get('termination_policies')
    notification_topic = module.params.get('notification_topic')
    notification_types = module.params.get('notification_types')
    suspend_processes = module.params['suspend_processes']
    changed = False

    asg_client = get_client('autoscaling', module)
    as_group = get_asg(group_name, module)
    asg_properties = get_properties(as_group)

    if vpc_zone_identifier:
        vpc_zone_identifier = ','.join(vpc_zone_identifier)

    asg_tags = []
    for tag in set_tags:
        for key, val in tag.items():
            if key != 'propagate_at_launch':
                asg_tags.append({
                    'Key': key,
                    'Value': val,
                    'ResourceId': group_name,
                    'ResourceType': 'auto-scaling-group',
                    'PropagateAtLaunch': bool(
                        tag.get('propagate_at_launch', True),
                    ),
                })

    if not vpc_zone_identifier and not availability_zones:
        ec2_client = get_client('ec2', module)
        availability_zones = module.params['availability_zones'] = [
            zone.name for zone in ec2_client.get_all_zones()
        ]
    enforce_required_arguments(module)
    requested_autoscale = {
        'AutoScalingGroupName': group_name,
        'LaunchConfigurationName': launch_config_name,
        'MinSize': min_size,
        'MaxSize': max_size,
        'DesiredCapacity': desired_capacity,
        'DefaultCooldown': default_cooldown,
        'AvailabilityZones': availability_zones,
        'LoadBalancerNames': load_balancers,
        'TargetGroupARNs': target_group_arns,
        'HealthCheckType': health_check_type,
        'HealthCheckGracePeriod': health_check_period,
        'PlacementGroup': placement_group,
        'VPCZoneIdentifier': vpc_zone_identifier,
        'TerminationPolicies': termination_policies,
        # 'NewInstancesProtectedFromScaleIn': True|False,
        'Tags': asg_tags,
        'SuspendedProcesses': suspend_processes,
    }

    log.debug("zxc: About to perform the base asg change")
    changed = perform_asg_change(requested_autoscale, module)

    if changed and notification_topic:
        log.debug("Put Notification Configuration")
        asg_client.put_notification_configuration(
            AutoScalingGroupName=group_name,
            TopicARN=notification_topic,
            NotificationTypes=notification_types,
        )

    try:
        as_group = get_asg(group_name, module)
        asg_properties = get_properties(as_group)
    except botocore.exceptions.ClientError as e:
        module.fail_json(
            msg="Failed to read existing Autoscaling Groups: %s" % str(e),
            exception=traceback.format_exc(e),
        )
    return(changed, asg_properties)


def delete_autoscaling_group(module):
    group_name = module.params.get('name')
    notification_topic = module.params.get('notification_topic')

    changed = False
    current_asg = get_asg(group_name, module)

    if current_asg is None:
        client = get_client('autoscaling', module)

        if notification_topic:
            client.delete_notification_configuration(
                AutoScalingGroupName=group_name,
                TopicARN=notification_topic,
            )

        client.delete_auto_scaling_group(
            AutoScalingGroupName=group_name,
            ForceDelete=True,
        )

        while get_asg(group_name, module):
            log.debug("Waiting for autoscaling group to be removed")
            time.sleep(10)

        changed = True

    return changed


def get_chunks(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i + n], i + n >= len(l)


def update_asg_size(as_group,
                    base_min_size,
                    base_max_size,
                    base_desired_size,
                    by_size,
                    module):
    update_group = as_group.copy()
    update_group['MinSize'] = base_min_size + by_size
    update_group['MaxSize'] = base_max_size + by_size
    update_group['DesiredCapacity'] = base_desired_size + by_size

    log.debug("zxc: updating ASG size(+{0}) {1},{2} => {3}".format(
        by_size,
        update_group['MinSize'],
        update_group['MaxSize'],
        update_group['DesiredCapacity'],
    ))

    perform_asg_change(update_group, module)

    return update_group


def wait_for_asg_state(group_name, viable_size, module):
    wait_for_instances = module.params.get('wait_for_instances')

    if wait_for_instances:
        wait_for_viable_instances(group_name,
                                  viable_size,
                                  module)
        wait_for_elb(module, group_name)
        wait_for_elbv2(module, group_name)


def replace(module):
    changed = False
    batch_size = module.params.get('replace_batch_size')
    group_name = module.params.get('name')
    lc_check = module.params.get('lc_check')
    replace_instances = module.params.get('replace_instances')

    as_group = get_asg(group_name, module)

    # Use min_size/max_size/desired_capacity if specified otherwise use ASG val
    if module.params.get('min_size'):
        as_group['MinSize'] = module.params.get('min_size')
    if module.params.get('max_size'):
        as_group['MaxSize'] = module.params.get('max_size')
    if module.params.get('desired_capacity'):
        as_group['DesiredCapacity'] = module.params.get('desired_capacity')

    base_min_size = as_group['MinSize']
    base_max_size = as_group['MaxSize']
    base_desired_size = as_group['DesiredCapacity']

    as_group = update_asg_size(
        as_group,
        base_min_size,
        base_max_size,
        base_desired_size,
        0,
        module,
    )

    # Wait for instances to reach min, without testing them.
    while True:
        as_group = get_asg(group_name, module)
        if len(get_properties(as_group)['instances']) >= \
                as_group['MinSize']:
            break
        log.debug("zxc: Waiting for min_size instance to exist")
        changed = True
        time.sleep(10)

    if replace_instances:  # replace with specified list
        instances = replace_instances
    else:  # replace with asg instances
        props = get_properties(as_group)
        instances = props.get('instances', [])

    log.debug("zxc: deploy could replace {0}".format(instances))
    instances = get_replaceable_instances(as_group,
                                          lc_check,
                                          instances)

    log.debug("zxc: deploy will replace {0}".format(instances))
    if instances:
        changed = True

    # TODO: Need to break out when timeout hit
    for batch_instances, final_loop in get_chunks(instances,
                                                  batch_size):
        log.debug("zxc: batching {0}".format(batch_instances))
        as_group = get_asg(group_name, module)
        log.debug("zxc: increase size by {0}".format(len(batch_instances)))
        as_group = update_asg_size(
            as_group,
            base_min_size,
            base_max_size,
            base_desired_size,
            len(batch_instances),
            module,
        )
        wait_for_asg_state(group_name, as_group['MinSize'], module)
        if final_loop:
            log.debug("zxc: restoring size")
            as_group = update_asg_size(
                as_group,
                base_min_size,
                base_max_size,
                base_desired_size,
                0,
                module,
            )

        terminate_instances(batch_instances, module)

    log.debug("zxc: final waiting")
    wait_for_asg_state(group_name, as_group['MinSize'], module)
    log.debug("zxc: Rolling update complete.")

    as_group = get_asg(group_name, module)
    asg_properties = get_properties(as_group)
    return(changed, asg_properties)


def get_replaceable_instances(as_group,
                              lc_check,
                              allowed_instances):
    """Get a list of replaceable instance ids.

    An instance is deamed replacable if it's in the autoscaling
    group, in the list of allowed instances, and the launch config
    name matches (if lc_check is set)

    """
    replacable_instances = []

    props = get_properties(as_group)

    log.debug("zxc: get_replaceable_instances start {0}".format(
        allowed_instances,
    ))
    for instance_id, instance in props['instance_facts'].items():
        if instance_id in allowed_instances:
            if not lc_check or instance['launch_config_name'] != \
                    props['launch_config_name']:
                replacable_instances.append(instance_id)

    return replacable_instances


def terminate_instances(instances, module):
    group_name = module.params.get('name')
    wait_for_instances = module.params.get('wait_for_instances')

    client = get_client('ec2', module)
    client.terminate_instances(InstanceIds=instances)

    wait_timeout = time.time() + module.params.get('wait_timeout')
    if wait_for_instances:
        log.debug(
            "zxc: waiting for instances to terminate {0}".format(
                instances,
            )
        )
        count = 1
        while wait_timeout > time.time() and count > 0:
            count = 0
            as_group = get_asg(group_name, module)
            props = get_properties(as_group)
            instance_facts = props['instance_facts']

            for i in (i for i in instance_facts if i in instances):
                lifecycle = instance_facts[i]['lifecycle_state']
                health = instance_facts[i]['health_status']
                log.debug("Instance {0} has state of {1}, {2}".format(
                    i,
                    lifecycle,
                    health,
                ))
                if lifecycle == 'Terminating' or \
                        health == 'Unhealthy':
                    count += 1
            time.sleep(10)

    if wait_timeout <= time.time():
        # waiting took too long
        module.fail_json(
            msg="Waited too long for old instances to "
            "terminate. %s" % time.asctime()
        )


def wait_for_viable_instances(group_name, desired_size, module):
    wait_timeout = module.params.get('wait_timeout')

    def get_viable_instances():
        return get_properties(get_asg(group_name,
                                      module))['viable_instances']

    viable_instances = get_viable_instances()
    log.debug("zxc: viable_instances = {0}, currently {1}".format(
        desired_size, viable_instances
    ))

    wait_timeout = time.time() + wait_timeout
    while wait_timeout > time.time() and viable_instances < desired_size:
        log.debug("Waiting for viable_instances = {0}, currently {1}".format(
            desired_size, viable_instances
        ))
        time.sleep(10)
        viable_instances = get_viable_instances()

    if wait_timeout <= time.time():
        # waiting took too long
        module.fail_json(
            msg="Waited too long for new instances to become viable. %s" %
            time.asctime()
        )
    log.debug("viable_instances >= {0}".format(desired_size))


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True, type='str'),
            load_balancers=dict(type='list'),
            target_group_arns=dict(type='list'),
            availability_zones=dict(type='list'),
            launch_config_name=dict(type='str'),
            min_size=dict(type='int'),
            max_size=dict(type='int'),
            placement_group=dict(type='str'),
            desired_capacity=dict(type='int'),
            vpc_zone_identifier=dict(type='list'),
            replace_batch_size=dict(type='int', default=1),
            replace_all_instances=dict(type='bool', default=False),
            replace_instances=dict(type='list', default=[]),
            lc_check=dict(type='bool', default=True),
            wait_timeout=dict(type='int', default=300),
            state=dict(default='present', choices=['present', 'absent']),
            tags=dict(type='list', default=[]),
            health_check_period=dict(type='int', default=300),
            health_check_type=dict(default='EC2', choices=['EC2', 'ELB']),
            default_cooldown=dict(type='int', default=300),
            wait_for_instances=dict(type='bool', default=True),
            termination_policies=dict(type='list', default='Default'),
            notification_topic=dict(type='str', default=None),
            notification_types=dict(type='list', default=[
                'autoscaling:EC2_INSTANCE_LAUNCH',
                'autoscaling:EC2_INSTANCE_LAUNCH_ERROR',
                'autoscaling:EC2_INSTANCE_TERMINATE',
                'autoscaling:EC2_INSTANCE_TERMINATE_ERROR'
            ]),
            suspend_processes=dict(type='list', default=[])
        ),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[['replace_all_instances', 'replace_instances']]
    )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    state = module.params.get('state')
    lc_check = module.params.get('lc_check')
    replace_instances = module.params.get('replace_instances')
    replace_all_instances = module.params.get(
        'replace_all_instances',
    )
    changed = replace_changed = False

    if state == 'present':
        log.debug("zxc: present path")
        changed, asg_properties = create_autoscaling_group(module)

        if replace_all_instances or replace_instances:
            log.debug("zxc: replace path")
            replace_changed, asg_properties = replace(module)
    elif state == 'absent':
        log.debug("zxc: absent path")
        changed = delete_autoscaling_group(module)
        asg_properties = {}
        module.exit_json(changed=changed)

    log.debug("Exiting with {0}, {1}".format(changed, asg_properties))
    module.exit_json(changed=changed or replace_changed, **asg_properties)

if __name__ == '__main__':
    main()
