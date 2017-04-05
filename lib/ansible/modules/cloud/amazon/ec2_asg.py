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
      - List of target group ARNs to use for the group
    version_added: "2.3"
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
from ansible.module_utils.ec2 import *
from ansible.module_utils.six import iteritems

try:
    import botocore
except ImportError:
    pass  # will be detected by imported HAS_BOTO3

#log.basicConfig(filename='/tmp/ansible_ec2_asg.log', level=log.DEBUG, format='%(asctime)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

ASG_ATTRIBUTES = ('AvailabilityZones', 'DefaultCooldown', 'DesiredCapacity',
                  'HealthCheckGracePeriod', 'HealthCheckType', 'LaunchConfigurationName',
                  'LoadBalancerNames', 'MaxSize', 'MinSize', 'AutoScalingGroupName', 'PlacementGroup',
                  'TerminationPolicies', 'VPCZoneIdentifier')

INSTANCE_ATTRIBUTES = ('instance_id', 'health_status', 'lifecycle_state', 'launch_config_name')

def enforce_required_arguments(module):
    ''' As many arguments are not required for autoscale group deletion
        they cannot be mandatory arguments for the module, so we enforce
        them here '''
    missing_args = []
    for arg in ('min_size', 'max_size', 'launch_config_name'):
        if module.params[arg] is None:
            missing_args.append(arg)
    if missing_args:
        module.fail_json(msg="Missing required arguments for autoscaling group create/update: %s" % ",".join(missing_args))


def get_properties(autoscaling_group):
    properties = dict()
    properties['healthy_instances'] = 0
    properties['in_service_instances'] = 0
    properties['unhealthy_instances'] = 0
    properties['pending_instances'] = 0
    properties['viable_instances'] = 0
    properties['terminating_instances'] = 0

    instance_facts = dict()
    autoscaling_group_instances = autoscaling_group.get('Instances')
    if autoscaling_group_instances:
        properties['instances'] = [i['InstanceId'] for i in autoscaling_group_instances]
        for i in autoscaling_group_instances:
            instance_facts[i['InstanceId']] = {'health_status': i['HealthStatus'],
                                               'lifecycle_state': i['LifecycleState'],
                                               'launch_config_name': i['LaunchConfigurationName']}
            if i['HealthStatus'] == 'Healthy' and i['LifecycleState'] == 'InService':
                properties['viable_instances'] += 1
            if i['HealthStatus'] == 'Healthy':
                properties['healthy_instances'] += 1
            else:
                properties['unhealthy_instances'] += 1
            if i['LifecycleState'] == 'InService':
                properties['in_service_instances'] += 1
            if i['LifecycleState'] == 'Terminating':
                properties['terminating_instances'] += 1
            if i['LifecycleState'] == 'Pending':
                properties['pending_instances'] += 1
    else:
        properties['instances'] = []
    properties['instance_facts'] = instance_facts
    properties['load_balancers'] = autoscaling_group.get('LoadBalancerNames')
    properties['launch_config_name'] = autoscaling_group.get('LaunchConfigurationName')
    properties['tags'] = autoscaling_group.get('Tags')

    return properties

def elb_dreg(asg_connection, module, group_name, instance_id):
    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
    as_group = asg_connection.describe_auto_scaling_groups(AutoScalingGroupNames=[group_name])['AutoScalingGroups'][0]
    wait_timeout = module.params.get('wait_timeout')
    count = 1
    if as_group['LoadBalancerNames'] and as_group['HealthCheckType'] == 'ELB':
        try:
            elb_connection = boto3_conn(module,
                                        conn_type='client',
                                        resource='elb',
                                        region=region,
                                        endpoint=ec2_url,
                                        **aws_connect_params)
        except boto.exception.NoAuthHandlerFound as e:
            module.fail_json(msg=str(e))
    else:
        return

    for lb in as_group['LoadBalancerNames']:
        elb_connection.deregister_instances_from_load_balancer(LoadBalancerName=lb,
                                                               Instances=[dict(InstanceId=instance_id)])
        log.debug("De-registering {0} from ELB {1}".format(instance_id, lb))

    wait_timeout = time.time() + wait_timeout
    while wait_timeout > time.time() and count > 0:
        count = 0
        for lb in as_group['LoadBalancerNames']:
            lb_instances = elb_connection.describe_instance_health(LoadBalancerName=lb)
            for i in lb_instances['InstanceStates']:
                if i['InstanceId'] == instance_id and i['State'] == "InService":
                    count += 1
                    log.debug("{0}: {1}, {2}".format(i['InstanceId'], i['State'], i['Description']))
        time.sleep(10)

    if wait_timeout <= time.time():
        # waiting took too long
        module.fail_json(msg = "Waited too long for instance to deregister. {0}".format(time.asctime()))


def elb_healthy(asg_connection, elb_connection, module, group_name):
    healthy_instances = set()
    as_group = asg_connection.describe_auto_scaling_groups(AutoScalingGroupNames=[group_name])['AutoScalingGroups'][0]
    props = get_properties(as_group)
    # get healthy, inservice instances from ASG
    instances = []
    for instance, settings in props['instance_facts'].items():
        if settings['lifecycle_state'] == 'InService' and settings['health_status'] == 'Healthy':
            instances.append(dict(InstanceId=instance))
    log.debug("ASG considers the following instances InService and Healthy: {0}".format(instances))
    log.debug("ELB instance status:")
    lb_instances = list()
    for lb in as_group.get('LoadBalancerNames'):
        # we catch a race condition that sometimes happens if the instance exists in the ASG
        # but has not yet show up in the ELB
        try:
            lb_instances = elb_connection.describe_instance_health(LoadBalancerName=lb, Instances=instances)
        except boto.exception.BotoServerError as e:
            if e.error_code == 'InvalidInstance':
                return None

            module.fail_json(msg=str(e))

        for i in lb_instances.get('InstanceStates'):
            if i['State'] == "InService":
                healthy_instances.add(i['InstanceId'])
            log.debug("ELB Health State {0}: {1}".format(i['InstanceId'], i['State']))
    return len(healthy_instances)


def tg_healthy(asg_connection, elbv2_connection, module, group_name):
    healthy_instances = set()
    as_group = asg_connection.describe_auto_scaling_groups(AutoScalingGroupNames=[group_name])['AutoScalingGroups'][0]
    props = get_properties(as_group)
    # get healthy, inservice instances from ASG
    instances = []
    for instance, settings in props['instance_facts'].items():
        if settings['lifecycle_state'] == 'InService' and settings['health_status'] == 'Healthy':
            instances.append(dict(Id=instance))
    log.debug("ASG considers the following instances InService and Healthy: {0}".format(instances))
    log.debug("Target Group instance status:")
    tg_instances = list()
    for tg in as_group.get('TargetGroupARNs'):
        # we catch a race condition that sometimes happens if the instance exists in the ASG
        # but has not yet show up in the ELB
        try:
            tg_instances = elbv2_connection.describe_target_health(TargetGroupArn=tg, Targets=instances)
        except boto.exception.BotoServerError as e:
            if e.error_code == 'InvalidInstance':
                return None
            module.fail_json(msg=str(e))

        for i in tg_instances.get('TargetHealthDescriptions'):
            if i['TargetHealth']['State'] == "healthy":
                healthy_instances.add(i['Target']['Id'])
            log.debug("Target Group Health State {0}: {1}".format(i['Target']['Id'], i['TargetHealth']['State']))
    return len(healthy_instances)


def wait_for_elb(asg_connection, module, group_name):
    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
    wait_timeout = module.params.get('wait_timeout')

    # if the health_check_type is ELB, we want to query the ELBs directly for instance
    # status as to avoid health_check_grace period that is awarded to ASG instances
    as_group = asg_connection.describe_auto_scaling_groups(AutoScalingGroupNames=[group_name])['AutoScalingGroups'][0]

    if as_group.get('LoadBalancerNames') and as_group.get('HealthCheckType') == 'ELB':
        log.debug("Waiting for ELB to consider instances healthy.")
        try:
            # elb_connection = connect_to_aws(boto.ec2.elb, region, **aws_connect_params)
            elb_connection = boto3_conn(module,
                                        conn_type='client',
                                        resource='elb',
                                        region=region,
                                        endpoint=ec2_url,
                                        **aws_connect_params)
        except boto.exception.NoAuthHandlerFound as e:
            module.fail_json(msg=str(e))

        wait_timeout = time.time() + wait_timeout
        healthy_instances = elb_healthy(asg_connection, elb_connection, module, group_name)

        while healthy_instances < as_group.get('MinSize') and wait_timeout > time.time():
            healthy_instances = elb_healthy(asg_connection, elb_connection, module, group_name)
            log.debug("ELB thinks {0} instances are healthy.".format(healthy_instances))
            time.sleep(10)
        if wait_timeout <= time.time():
            # waiting took too long
            module.fail_json(msg="Waited too long for ELB instances to be healthy. %s" % time.asctime())
        log.debug("Waiting complete.  ELB thinks {0} instances are healthy.".format(healthy_instances))


def wait_for_target_group(asg_connection, module, group_name):
    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
    wait_timeout = module.params.get('wait_timeout')

    # if the health_check_type is ELB, we want to query the ELBs directly for instance
    # status as to avoid health_check_grace period that is awarded to ASG instances
    as_group = asg_connection.describe_auto_scaling_groups(AutoScalingGroupNames=[group_name])['AutoScalingGroups'][0]

    if as_group.get('TargetGroupARNs') and as_group.get('HealthCheckType') == 'ELB':
        log.debug("Waiting for Target Group to consider instances healthy.")
        try:
            # elb_connection = connect_to_aws(boto.ec2.elb, region, **aws_connect_params)
            elbv2_connection = boto3_conn(module,
                                          conn_type='client',
                                          resource='elbv2',
                                          region=region,
                                          endpoint=ec2_url,
                                          **aws_connect_params)
        except boto.exception.NoAuthHandlerFound as e:
            module.fail_json(msg=str(e))
        wait_timeout = time.time() + wait_timeout
        healthy_instances = tg_healthy(asg_connection, elbv2_connection, module, group_name)

        while healthy_instances < as_group.get('MinSize') and wait_timeout > time.time():
            healthy_instances = tg_healthy(asg_connection, elbv2_connection, module, group_name)
            log.debug("Target Group thinks {0} instances are healthy.".format(healthy_instances))
            time.sleep(10)
        if wait_timeout <= time.time():
            # waiting took too long
            module.fail_json(msg="Waited too long for ELB instances to be healthy. %s" % time.asctime())
        log.debug("Waiting complete. Target Group thinks {0} instances are healthy.".format(healthy_instances))


def suspend_processes(ec2_connection, as_group, module):
    suspend_processes = set(module.params.get('suspend_processes'))

    try:
        suspended_processes = set([p['ProcessName'] for p in as_group['SuspendedProcesses']])
    except AttributeError:
        # New ASG being created, no suspended_processes defined yet
        suspended_processes = set()

    if suspend_processes == suspended_processes:
        return False

    resume_processes = list(suspended_processes - suspend_processes)
    if resume_processes:
        ec2_connection.resume_processes(AutoScalingGroupName=module.params.get('name'), ScalingProcesses=resume_processes)

    if suspend_processes:
        ec2_connection.suspend_processes(AutoScalingGroupName=module.params.get('name'), ScalingProcesses=list(suspend_processes))

    return True

@AWSRetry.backoff(tries=3, delay=0.1)
def create_autoscaling_group(connection, module):
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
    wait_for_instances = module.params.get('wait_for_instances')
    as_groups = connection.describe_auto_scaling_groups(AutoScalingGroupNames=[group_name])
    wait_timeout = module.params.get('wait_timeout')
    termination_policies = module.params.get('termination_policies')
    notification_topic = module.params.get('notification_topic')
    notification_types = module.params.get('notification_types')

    if not vpc_zone_identifier and not availability_zones:
        region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
        try:
            ec2_connection = boto3_conn(module,
                                        conn_type='client',
                                        resource='ec2',
                                        region=region,
                                        endpoint=ec2_url,
                                        **aws_connect_params)
        except (botocore.exceptions.NoCredentialsError, AnsibleAWSError) as e:
            module.fail_json(msg=str(e))
    elif vpc_zone_identifier:
        vpc_zone_identifier = ','.join(vpc_zone_identifier)

    asg_tags = []
    for tag in set_tags:
        for k,v in tag.items():
            if k !='propagate_at_launch':
                asg_tags.append(dict(Key=k,
                                     Value=v,
                                     PropagateAtLaunch=bool(tag.get('propagate_at_launch', True)),
                                     ResourceType='auto-scaling-group',
                                     ResourceId=group_name))
    if not as_groups.get('AutoScalingGroups'):
        if not vpc_zone_identifier and not availability_zones:
            availability_zones = module.params['availability_zones'] = [zone.name for zone in ec2_connection.get_all_zones()]
        enforce_required_arguments(module)
        launch_configs = connection.describe_launch_configurations(LaunchConfigurationNames=[launch_config_name])
        if len(launch_configs) == 0:
            module.fail_json(msg="No launch config found with name %s" % launch_config_name)
        ag = dict(
            AutoScalingGroupName=group_name,
            AvailabilityZones=availability_zones,
            LaunchConfigurationName=launch_configs['LaunchConfigurations'][0]['LaunchConfigurationName'],
            MinSize=min_size,
            MaxSize=max_size,
            DesiredCapacity=desired_capacity,
            VPCZoneIdentifier=vpc_zone_identifier,
            Tags=asg_tags,
            HealthCheckGracePeriod=health_check_period,
            HealthCheckType=health_check_type,
            DefaultCooldown=default_cooldown,
            TerminationPolicies=termination_policies)
        if placement_group:
            ag['PlacementGroup'] = placement_group
        if load_balancers:
            ag['LoadBalancerNames'] = load_balancers
        if target_group_arns:
            ag['TargetGroupARNs'] = target_group_arns

        try:
            connection.create_auto_scaling_group(**ag)

            all_ag = connection.describe_auto_scaling_groups(AutoScalingGroupNames=[group_name])['AutoScalingGroups']
            if len(all_ag) == 0:
                module.fail_json(msg="No auto scaling group found with the name %s" % group_name)
            as_group = all_ag[0]
            suspend_processes(connection, as_group, module)
            if wait_for_instances:
                wait_for_new_inst(module, connection, group_name, wait_timeout, desired_capacity, 'viable_instances')
                if load_balancers:
                    wait_for_elb(connection, module, group_name)
                # Wait for target group health if target group(s)defined
                if target_group_arns:
                    wait_for_target_group(connection, module, group_name)
            if notification_topic:
                connection.put_notification_configuration(
                    AutoScalingGroupName=group_name,
                    TopicARN=notification_topic,
                    NotificationTypes=[
                        notification_types,
                    ]
                )
            asg_properties = get_properties(as_group)
            changed = True
            return changed, asg_properties
        except botocore.exceptions.BotoCoreError as e:
            module.fail_json(msg="Failed to create Autoscaling Group: %s" % str(e), exception=traceback.format_exc())
    else:
        as_group = as_groups['AutoScalingGroups'][0]
        changed = False

        if suspend_processes(connection, as_group, module):
            changed = True

        # process tag changes
        if len(set_tags) > 0:
            have_tags = as_group.get('Tags')
            want_tags = asg_tags
            dead_tags = []
            have_tag_keyvals = [x['Key'] for x in have_tags]
            want_tag_keyvals = [x['Key'] for x in want_tags]

            for dead_tag in set(have_tag_keyvals).difference(want_tag_keyvals):
                changed = True
                dead_tags.append(dict(ResourceId=as_group['AutoScalingGroupName'],
                                      ResourceType='auto-scaling-group', Key=dead_tag))
                have_tags = [have_tag for have_tag in have_tags if have_tag['Key'] != dead_tag]
            if dead_tags:
                connection.delete_tags(Tags=dead_tags)

            zipped = zip(have_tags, want_tags)
            if len(have_tags) != len(want_tags) or not all(x == y for x, y in zipped):
                changed = True
                connection.create_or_update_tags(Tags=asg_tags)

        # Handle load balancer attachments/detachments
        # Attach load balancers if they are specified but none currently exist
        if load_balancers and not as_group['LoadBalancerNames']:
            changed = True
            try:
                connection.attach_load_balancers(
                    AutoScalingGroupName=group_name,
                    LoadBalancerNames=load_balancers
                )
            except botocore.exceptions.BotoCoreError as e:
                module.fail_json(msg="Failed to update Autoscaling Group: %s" % str(e),
                                 exception=traceback.format_exc())

        # Update load balancers if they are specified and one or more already exists
        elif as_group['LoadBalancerNames']:
            # Get differences
            if not load_balancers:
                load_balancers = list()
            wanted_elbs = set(load_balancers)

            has_elbs = set(as_group['LoadBalancerNames'])
            # check if all requested are already existing
            if has_elbs.issuperset(wanted_elbs):
                # if wanted contains less than existing, then we need to delete some
                elbs_to_detach = has_elbs.difference(wanted_elbs)
                if elbs_to_detach:
                    changed = True
                    connection.detach_load_balancers(
                        AutoScalingGroupName=group_name,
                        LoadBalancerNames=list(elbs_to_detach)
                    )
            if wanted_elbs.issuperset(has_elbs):
                # if has contains less than wanted, then we need to add some
                elbs_to_attach = wanted_elbs.difference(has_elbs)
                if elbs_to_attach:
                    changed = True
                    connection.attach_load_balancers(
                        AutoScalingGroupName=group_name,
                        LoadBalancerNames=list(elbs_to_attach)
                    )

        # Handle target group attachments/detachments
        # Attach target groups if they are specified but none currently exist
        if target_group_arns and not as_group['TargetGroupARNs']:
            changed = True
            try:
                connection.attach_load_balancer_target_groups(
                    AutoScalingGroupName=group_name,
                    TargetGroupARNs=target_group_arns
                )
            except botocore.exceptions.BotoCoreError as e:
                module.fail_json(msg="Failed to update Autoscaling Group: %s" % str(e),
                                 exception=traceback.format_exc())
        # Update target groups if they are specified and one or more already exists
        elif target_group_arns and as_group['TargetGroupARNs']:
            # Get differences
            if not target_group_arns:
                target_group_arns = list()
            wanted_tgs = set(target_group_arns)
            has_tgs = set(as_group['TargetGroupARNs'])
            # check if all requested are already existing
            if has_tgs.issuperset(wanted_tgs):
                # if wanted contains less than existing, then we need to delete some
                tgs_to_detach = has_tgs.difference(wanted_tgs)
                if tgs_to_detach:
                    changed = True
                    connection.detach_load_balancer_target_groups(
                        AutoScalingGroupName=group_name,
                        TargetGroupARNs=list(tgs_to_detach)
                    )
            if wanted_tgs.issuperset(has_tgs):
                # if has contains less than wanted, then we need to add some
                tgs_to_attach = wanted_tgs.difference(has_tgs)
                if tgs_to_attach:
                    changed = True
                    connection.attach_load_balancer_target_groups(
                        AutoScalingGroupName=group_name,
                        TargetGroupARNs=list(tgs_to_attach)
                    )

        launch_configs = connection.describe_launch_configurations(LaunchConfigurationNames=[launch_config_name])
        ag = dict(
            AutoScalingGroupName=group_name,
            AvailabilityZones=availability_zones,
            LaunchConfigurationName=launch_configs['LaunchConfigurations'][0]['LaunchConfigurationName'],
            MinSize=min_size,
            MaxSize=max_size,
            DesiredCapacity=desired_capacity,
            VPCZoneIdentifier=vpc_zone_identifier,
            HealthCheckGracePeriod=health_check_period,
            HealthCheckType=health_check_type,
            DefaultCooldown=default_cooldown,
            TerminationPolicies=termination_policies)
        connection.update_auto_scaling_group(**ag)

        if notification_topic:
            try:
                connection.put_notification_configuration(
                    AutoScalingGroupName=group_name,
                    TopicARN=notification_topic,
                    NotificationTypes=notification_types
                )
            except botocore.exceptions.BotoCoreError as e:
                module.fail_json(msg="Failed to update Autoscaling Group notifications: %s" % str(e),
                                 exception=traceback.format_exc())
        if wait_for_instances:
            wait_for_new_inst(module, connection, group_name, wait_timeout, desired_capacity, 'viable_instances')
            # Wait for ELB health if ELB(s)defined
            if load_balancers:
                log.debug('\tWAITING FOR ELB HEALTH')
                wait_for_elb(connection, module, group_name)
            # Wait for target group health if target group(s)defined

            if target_group_arns:
                log.debug('\tWAITING FOR TG HEALTH')
                wait_for_target_group(connection, module, group_name)

        try:
            as_group = connection.describe_auto_scaling_groups(
                AutoScalingGroupNames=[group_name])['AutoScalingGroups'][0]
            asg_properties = get_properties(as_group)
        except botocore.exceptions.BotoCoreError as e:
            module.fail_json(msg="Failed to read existing Autoscaling Groups: %s" % str(e),
                             exception=traceback.format_exc())
        return changed, asg_properties


def delete_autoscaling_group(connection, module):
    group_name = module.params.get('name')
    notification_topic = module.params.get('notification_topic')
    wait_for_instances = module.params.get('wait_for_instances')
    wait_timeout = module.params.get('wait_timeout')

    if notification_topic:
        connection.delete_notification_configuration(
            AutoScalingGroupName=group_name,
            TopicARN=notification_topic
        )
    describe_response = connection.describe_auto_scaling_groups(AutoScalingGroupNames=[group_name])
    groups = describe_response.get('AutoScalingGroups')
    if groups:
        if not wait_for_instances:
            connection.delete_auto_scaling_group(AutoScalingGroupName=group_name, ForceDelete=True)
            return True

        wait_timeout = time.time() + wait_timeout
        connection.update_auto_scaling_group(
            AutoScalingGroupName=group_name,
            MinSize=0, MaxSize=0,
            DesiredCapacity=0)
        instances = True
        while instances and wait_for_instances and wait_timeout >= time.time():
            tmp_groups = connection.describe_auto_scaling_groups(AutoScalingGroupNames=[group_name]).get(
                'AutoScalingGroups')
            if tmp_groups:
                tmp_group = tmp_groups[0]
                if not tmp_group.get('Instances'):
                    instances = False
            time.sleep(10)

        if wait_timeout <= time.time():
            # waiting took too long
            module.fail_json(msg = "Waited too long for old instances to terminate. %s" % time.asctime())

        connection.delete_auto_scaling_group(AutoScalingGroupName=group_name)
        while len(connection.describe_auto_scaling_groups(AutoScalingGroupNames=[group_name]).get('AutoScalingGroups')):
            time.sleep(5)
        return True

    return False

def get_chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def update_size(connection, group, max_size, min_size, dc):

    log.debug("setting ASG sizes")
    log.debug("minimum size: {0}, desired_capacity: {1}, max size: {2}".format(min_size, dc, max_size))
    updated_group = dict()
    updated_group['AutoScalingGroupName'] = group['AutoScalingGroupName']
    updated_group['MinSize'] = min_size
    updated_group['MaxSize'] = max_size
    updated_group['DesiredCapacity'] = dc
    connection.update_auto_scaling_group(**updated_group)


def replace(connection, module):
    batch_size = module.params.get('replace_batch_size')
    wait_timeout = module.params.get('wait_timeout')
    group_name = module.params.get('name')
    max_size =  module.params.get('max_size')
    min_size =  module.params.get('min_size')
    desired_capacity =  module.params.get('desired_capacity')
    lc_check = module.params.get('lc_check')
    replace_instances = module.params.get('replace_instances')

    as_group = connection.describe_auto_scaling_groups(AutoScalingGroupNames=[group_name])['AutoScalingGroups'][0]
    wait_for_new_inst(module, connection, group_name, wait_timeout, as_group['MinSize'], 'viable_instances')
    props = get_properties(as_group)
    instances = props['instances']
    if replace_instances:
        instances = replace_instances
    # check to see if instances are replaceable if checking launch configs

    new_instances, old_instances = get_instances_by_lc(props, lc_check, instances)
    num_new_inst_needed = desired_capacity - len(new_instances)

    if lc_check:
        if num_new_inst_needed == 0 and old_instances:
            log.debug("No new instances needed, but old instances are present. Removing old instances")
            terminate_batch(connection, module, old_instances, instances, True)
            as_group = connection.describe_auto_scaling_groups(AutoScalingGroupNames=[group_name])['AutoScalingGroups'][0]
            props = get_properties(as_group)
            changed = True
            return(changed, props)

        #  we don't want to spin up extra instances if not necessary
        if num_new_inst_needed < batch_size:
            log.debug("Overriding batch size to {0}".format(num_new_inst_needed))
            batch_size = num_new_inst_needed

    if not old_instances:
        changed = False
        return(changed, props)

    # check if min_size/max_size/desired capacity have been specified and if not use ASG values
    if min_size is None:
        min_size = as_group['MinSize']
    if max_size is None:
        max_size = as_group['MaxSize']
    if desired_capacity is None:
        desired_capacity = as_group['DesiredCapacity']
    # set temporary settings and wait for them to be reached
    # This should get overwritten if the number of instances left is less than the batch size.

    as_group = connection.describe_auto_scaling_groups(AutoScalingGroupNames=[group_name])['AutoScalingGroups'][0]
    update_size(connection, as_group, max_size + batch_size, min_size + batch_size, desired_capacity + batch_size)
    wait_for_new_inst(module, connection, group_name, wait_timeout, as_group['MinSize'], 'viable_instances')
    wait_for_elb(connection, module, group_name)
    wait_for_target_group(connection, module, group_name)
    as_group = connection.describe_auto_scaling_groups(AutoScalingGroupNames=[group_name])['AutoScalingGroups'][0]
    props = get_properties(as_group)
    instances = props['instances']
    if replace_instances:
        instances = replace_instances
    log.debug("beginning main loop")
    for i in get_chunks(instances, batch_size):
        # break out of this loop if we have enough new instances
        break_early, desired_size, term_instances = terminate_batch(connection, module, i, instances, False)
        wait_for_term_inst(connection, module, term_instances)
        wait_for_new_inst(module, connection, group_name, wait_timeout, desired_size, 'viable_instances')
        wait_for_elb(connection, module, group_name)
        wait_for_target_group(connection, module, group_name)
        as_group = connection.describe_auto_scaling_groups(AutoScalingGroupNames=[group_name])['AutoScalingGroups'][0]
        if break_early:
            log.debug("breaking loop")
            break
    update_size(connection, as_group, max_size, min_size, desired_capacity)
    as_group = connection.describe_auto_scaling_groups(AutoScalingGroupNames=[group_name])['AutoScalingGroups'][0]
    asg_properties = get_properties(as_group)
    log.debug("Rolling update complete.")
    changed=True
    return(changed, asg_properties)

def get_instances_by_lc(props, lc_check, initial_instances):

    new_instances = []
    old_instances = []
    # old instances are those that have the old launch config
    if lc_check:
        for i in props['instances']:
            if props['instance_facts'][i]['launch_config_name']  == props['launch_config_name']:
                new_instances.append(i)
            else:
                old_instances.append(i)

    else:
        log.debug("Comparing initial instances with current: {0}".format(initial_instances))
        for i in props['instances']:
            if i not in initial_instances:
                new_instances.append(i)
            else:
                old_instances.append(i)
    log.debug("New instances: {0}, {1}".format(len(new_instances), new_instances))
    log.debug("Old instances: {0}, {1}".format(len(old_instances), old_instances))

    return new_instances, old_instances


def list_purgeable_instances(props, lc_check, replace_instances, initial_instances):
    instances_to_terminate = []
    instances = ( inst_id for inst_id in replace_instances if inst_id in props['instances'])

    # check to make sure instances given are actually in the given ASG
    # and they have a non-current launch config
    if lc_check:
        for i in instances:
            if props['instance_facts'][i]['launch_config_name']  != props['launch_config_name']:
                instances_to_terminate.append(i)
    else:
        for i in instances:
            if i in initial_instances:
                instances_to_terminate.append(i)
    return instances_to_terminate

def terminate_batch(connection, module, replace_instances, initial_instances, leftovers=False):
    batch_size = module.params.get('replace_batch_size')
    min_size =  module.params.get('min_size')
    desired_capacity =  module.params.get('desired_capacity')
    group_name = module.params.get('name')
    wait_timeout = int(module.params.get('wait_timeout'))
    lc_check = module.params.get('lc_check')
    decrement_capacity = False
    break_loop = False

    as_group = connection.describe_auto_scaling_groups(AutoScalingGroupNames=[group_name])['AutoScalingGroups'][0]
    props = get_properties(as_group)
    desired_size = as_group['MinSize']

    new_instances, old_instances = get_instances_by_lc(props, lc_check, initial_instances)
    num_new_inst_needed = desired_capacity - len(new_instances)

    # check to make sure instances given are actually in the given ASG
    # and they have a non-current launch config
    instances_to_terminate = list_purgeable_instances(props, lc_check, replace_instances, initial_instances)

    log.debug("new instances needed: {0}".format(num_new_inst_needed))
    log.debug("new instances: {0}".format(new_instances))
    log.debug("old instances: {0}".format(old_instances))
    log.debug("batch instances: {0}".format(",".join(instances_to_terminate)))

    if num_new_inst_needed == 0:
        decrement_capacity = True
        if as_group['MinSize'] != min_size:
            connection.update_auto_scaling_group(AutoScalingGroupName=as_group['AutoScalingGroupName'],
                                                 MinSize=min_size)
            log.debug("Updating minimum size back to original of {0}".format(min_size))
        #if are some leftover old instances, but we are already at capacity with new ones
        # we don't want to decrement capacity
        if leftovers:
            decrement_capacity = False
        break_loop = True
        instances_to_terminate = old_instances
        desired_size = min_size
        log.debug("No new instances needed")

    if num_new_inst_needed < batch_size and num_new_inst_needed !=0 :
        instances_to_terminate = instances_to_terminate[:num_new_inst_needed]
        decrement_capacity = False
        break_loop = False
        log.debug("{0} new instances needed".format(num_new_inst_needed))

    log.debug("decrementing capacity: {0}".format(decrement_capacity))

    for instance_id in instances_to_terminate:
        elb_dreg(connection, module, group_name, instance_id)
        log.debug("terminating instance: {0}".format(instance_id))
        connection.terminate_instance_in_auto_scaling_group(InstanceId=instance_id,
                                                            ShouldDecrementDesiredCapacity=decrement_capacity)

    # we wait to make sure the machines we marked as Unhealthy are
    # no longer in the list

    return break_loop, desired_size, instances_to_terminate


def wait_for_term_inst(connection, module, term_instances):

    batch_size = module.params.get('replace_batch_size')
    wait_timeout = module.params.get('wait_timeout')
    group_name = module.params.get('name')
    lc_check = module.params.get('lc_check')
    as_group = connection.describe_auto_scaling_groups(AutoScalingGroupNames=[group_name])['AutoScalingGroups'][0]
    props = get_properties(as_group)
    count = 1
    wait_timeout = time.time() + wait_timeout
    while wait_timeout > time.time() and count > 0:
        log.debug("waiting for instances to terminate")
        count = 0
        as_group = connection.describe_auto_scaling_groups(AutoScalingGroupNames=[group_name])['AutoScalingGroups'][0]
        props = get_properties(as_group)
        instance_facts = props['instance_facts']
        instances = ( i for i in instance_facts if i in term_instances)
        for i in instances:
            lifecycle = instance_facts[i]['lifecycle_state']
            health = instance_facts[i]['health_status']
            log.debug("Instance {0} has state of {1},{2}".format(i,lifecycle,health ))
            if lifecycle == 'Terminating' or health == 'Unhealthy':
                count += 1
        time.sleep(10)

    if wait_timeout <= time.time():
        # waiting took too long
        module.fail_json(msg = "Waited too long for old instances to terminate. %s" % time.asctime())


def wait_for_new_inst(module, connection, group_name, wait_timeout, desired_size, prop):

    # make sure we have the latest stats after that last loop.
    as_group = connection.describe_auto_scaling_groups(AutoScalingGroupNames=[group_name])['AutoScalingGroups'][0]
    props = get_properties(as_group)
    log.debug("Waiting for {0} = {1}, currently {2}".format(prop, desired_size, props[prop]))
    # now we make sure that we have enough instances in a viable state
    wait_timeout = time.time() + wait_timeout
    while wait_timeout > time.time() and desired_size > props[prop]:
        log.debug("Waiting for {0} = {1}, currently {2}".format(prop, desired_size, props[prop]))
        time.sleep(10)
        as_group = connection.describe_auto_scaling_groups(AutoScalingGroupNames=[group_name])['AutoScalingGroups'][0]
        props = get_properties(as_group)
    if wait_timeout <= time.time():
        # waiting took too long
        module.fail_json(msg = "Waited too long for new instances to become viable. %s" % time.asctime())
    log.debug("Reached {0}: {1}".format(prop, desired_size))
    return props

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
        mutually_exclusive = [['replace_all_instances', 'replace_instances']]
    )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    state = module.params.get('state')
    replace_instances = module.params.get('replace_instances')
    replace_all_instances = module.params.get('replace_all_instances')
    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
    try:
        connection = boto3_conn(module,
                                conn_type='client',
                                resource='autoscaling',
                                region=region,
                                endpoint=ec2_url,
                                **aws_connect_params)
        if not connection:
            module.fail_json(msg="failed to connect to AWS for the given region: %s" % str(region))
    except botocore.exceptions.NoCredentialsError as e:
        module.fail_json(msg=str(e))
    changed = create_changed = replace_changed = False

    if state == 'present':
        create_changed, asg_properties=create_autoscaling_group(connection, module)
    elif state == 'absent':
        changed = delete_autoscaling_group(connection, module)
        module.exit_json( changed = changed )
    if replace_all_instances or replace_instances:
        replace_changed, asg_properties=replace(connection, module)
    if create_changed or replace_changed:
        changed = True
    module.exit_json( changed = changed, **asg_properties )

if __name__ == '__main__':
    main()
