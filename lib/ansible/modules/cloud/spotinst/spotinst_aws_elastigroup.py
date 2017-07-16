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
                    'status': ['preview'],
                    'supported_by': 'curated'}

DOCUMENTATION = """
---
author: Spotinst
availability_vs_cost:
  choices:
    - availabilityOriented
    - costOriented
    - balanced
  description:
    - The strategy orientation._
  required: true
availability_zones:
  description:
    - _Information about one or more availability Zones for the group.
  fields:
    - name
    - subnet_id
    - placement_group_name
  required: true
block_device_mappings:
  description:
    - Array list of block devices that are exposed to the instance, You can specify virtual devices and EBS volumes
  fields:
    - device_name
    - no_device
    - ebs
  required: false
chef:
  description:
    - chef integration
  fields:
    - chef_server
    - organization
    - user
    - pem_key
    - chef_version
  required: false
description:
  - Can create, update, or delete Spotinst AWS Elastigroups
  - Launch configuration is part of the elastigroup configuration, so no additional modules are necessary for handling the launch configuration
  - This module requires that you install the spotinst Python SDK (pip install spotinst)
  - You will have to have a credentials file in this location : ~/.spotinst/credentials
  - The credentials file must contain a row that looks like this
  - token = <YOUR TOKEN>
  - Full documentation available here : https://help.spotinst.com/hc/en-us/articles/115003530285-Ansible-

down_scaling_policies:
  description:
    - Down scaling policies for this elastigroup
  fields:
    - policy_name
    - namespace
    - metric_name
    - dimensions
    - statistic
    - evaluation_periods
    - period
    - threshold
    - cooldown
    - unit
    - operator
    - action_type
    - adjustment
    - min_target_capacity
    - max_target_capacity
    - target
    - maximum
    - minimum
  required: false
draining_timeout:
  description:
    - seconds to allow the instance be drained from incoming TCP connections and detached from ELB before termination, in scale down operations.
  required: false
ebs_optimized:
  description:
    - Enable EBS optimization for supported instances which are not enabled by default. Note - additional charges will be applied.
  required: false
ebs_volume_pool:
  description:
    - he EBS pool list for re-attach when available.
  fields:
    - volume_ids
    - device_name
  required: false
ecs:
  description:
    - ECS Integration
  fields:
    - cluster_name
  required: false
elastic_ips:
  description:
    - _List of ElasticIps Allocation Ids to associate to the group instances
  required: false
fallback_to_ondemand:
  description:
    - In case of no spots available, Elastigroup will launch an On-demand instance instead
  required: false
health_check_grace_period:
  default: 300
  description:
    - The amount of time, in seconds, after the instance has launched to starts and check its health.
  required: false
health_check_type:
  choices:
    - ELB
    - HCS
    - TARGET_GROUP
    - MLB
    - EC2
  description:
    - he service to use for the health check.
  required: false
iam_role_name:
  description:
    - The instance profile iamRole name
    - Only use iam_role_arn, or iam_role_name
  required: false
iam_role_arn:
  description:
    - The instance profile iamRole arn
    - Only use iam_role_arn, or iam_role_name
  required: false
ignore_changes:
  choices:
    - image_id
    - target
  description:
    - list of fields on which changes should be ignored when updating
  required: false
image_id:
  description:
    - The image Id used to launch the instance. In case of conflict between Instance type and image type, an error will be returned
  required: true
key_pair:
  description:
    - Specify a Key Pair to attach to the instances
  required: true
kubernetes:
  description:
    - kubernetes integration
  fields:
    - api_server
    - token
  required: false
lifetime_period:
  description:
    - ~
  required: false
load_balancers:
  description:
    - List of elastic load balancer names
  required: false
max_size:
  description:
    - The upper limit number of instances that you can scale up to
  required: true
mesosphere:
  description:
    - Mesosphere integration
  fields:
    - api_server
  required: false
min_size:
  description:
    - The lower limit number of instances that you can scale down to
  required: true
module: spotinst_aws_elastigroup
monitoring:
  description:
    - Describes whether instance Enhanced Monitoring is enabled
  required: true
name:
  description:
    - Unique name for elastigroup to be created, updated or deleted
  required: true
network_interfaces:
  description:
    - List of network interfaces in an EC2 instance for AWS CloudFormation.
  fields:
    - description
    - device_index
    - secondary_private_ip_address_count
    - associate_public_ip_address
    - delete_on_termination
    - groups
    - network_interface_id
    - private_ip_address
    - subnet_id
    - associate_ipv6_address
    - private_ip_addresses
  required: false
on_demand_count:
  description:
    - Number of on demand instances to launch. All other instances will be spot instances. Either set this parameter or the risk parameter
  required: Required if risk is not set
on_demand_instance_type:
  description:
    - On-demand instance type that will be provisioned
  required: true
opsworks:
  description:
    - opsworks integration
  fields:
    - layer_id
  required: false
options: ~
persistence:
  description:
    - You can register persistence (Stateful) recovery arguments
  fields:
    - should_persist_root_device
    - should_persist_block_devices
    - should_persist_private_ip
  required: false
product:
  choices:
    - Linux/UNIX
    - SUSE Linux
    - Windows
    - Linux/UNIX (Amazon VPC)
    - SUSE Linux (Amazon VPC)
    - Windows
  description:
    - Operation system type._
  required: true
rancher:
  description:
    - Rancher integration
  fields:
    - access_key
    - secret_key
    - master_host
  required: false
rightscale:
  description:
    - Rightscale Integration
  fields:
    - account_id
    - refresh_token
  required: false
risk:
  description:
    -
      ? The percentage of Spot instances to launch (range
      : 0 - 100).
  required: Required if on_demand_count is not st
scheduled_tasks:
  description:
    - All scheduled tasks for this group
  fields:
    - adjustment
    - scale_target_capacity
    - scale_min_capacity
    - scale_max_capacity
    - adjustment_percentage
    - batch_size_percentage
    - cron_expression
    - frequency
    - grace_period
    - task_type
    - is_enabled
  required: false
security_group_ids:
  description:
    - One or more security group IDs. In case of update it will override the existing Security Group with the new given array
  required: true
short_description: Create, update or delete Spotinst AWS Elastigroups
shut_down_script:
  description:
    - The Base64-encoded shutdown script that executet prior to instnace termination
  required: false
signals:
  description:
    - The signals defined for this group
  fields:
    - name
    - timeout
  required: false
spin_up_time:
  description:
    - ~
  required: false
spot_instance_types:
  description:
    - Spot instance type that will be provisioned._
  required: true
state:
  choices:
    - present
    - absent
  description:
    - create or delete the elastigroup
  required: false
tags:
  description:
    - tags for the elastigroup
  fields:
    - key
    - value
  required: false
target:
  description:
    - The number of instances to launch
  required: true
target_group_arns:
  description:
    - List of target group arns instances should be registered to
  required: false
tenancy:
  choices:
    - default
    - dedicated
  description:
    - ~
  required: false
terminate_at_end_of_billing_hour:
  description:
    - ~
  required: false
unit:
  choices:
    - instance
    - weight
  description:
    - The capacity unit to launch instances by.
  required: true
up_scaling_policies:
  description:
    - Up scaling policies for this elastigroup
  fields:
    - policy_name
    - namespace
    - metric_name
    - dimensions
    - statistic
    - evaluation_periods
    - period
    - threshold
    - cooldown
    - unit
    - operator
    - action_type
    - adjustment
    - min_target_capacity
    - max_target_capacity
    - target
    - maximum
    - minimum
  required: false
user_data:
  description:
    - he Base64-encoded MIME user data to make available to the instances
  required: false
utilize_reserved_instances:
  description:
    - In case of any available Reserved Instances, Elastigroup will utilize them before purchasing Spot instances
  required: false
"""

EXAMPLES = '''
# Basic configuration YAML example

- hosts: localhost
  tasks:
    - name: create elastigroup
      spotinst_aws_elastigroup:
          state: present
          risk: 100
          availability_vs_cost: balanced
          availability_zones:
            - name: us-west-2a
              subnet_id: subnet-2b68a15c
          image_id: ami-f173cc91
          key_pair: spotinst-oregon
          max_size: 15
          min_size: 0
          target: 0
          unit: instance
          monitoring: True
          name: ansible-group
          on_demand_instance_type: c3.large
          product: Linux/UNIX
          load_balancers:
            - test-lb-1
          security_group_ids:
            - sg-8f4b8fe9
          spot_instance_types:
            - c3.large
          state: absent
          do_not_update:
            - image_id
            - target
      register: result
    - debug: var=result
'''

RETURN = '''
---
'''

HAS_SPOTINST_SDK = False

from os.path import expanduser

from ansible.module_utils.basic import AnsibleModule

try:
    import spotinst

    HAS_SPOTINST_SDK = True

except ImportError:
    pass


def handle_elastigroup(client, module):
    has_changed = False
    name = module.params.get('name')
    state = module.params.get('state')

    groups = client.get_elastigroups()

    group_found, group_id = find_group_with_same_name(groups, name)
    message = 'None'

    if group_found is True:
        eg = expand_elastigroup(module, is_update=True)

        if state == 'present':
            group = client.update_elastigroup(group_update=eg, group_id=group_id)
            message = 'Updated group successfully.'
            has_changed = True

        elif state == 'absent':
            client.delete_elastigroup(group_id=group_id)
            message = 'Deleted group successfully.'
            has_changed = True

    else:
        if state == 'present':
            eg = expand_elastigroup(module, is_update=False)

            group = client.create_elastigroup(group=eg)
            group_id = group['id']
            message = 'Created group Successfully.'
            has_changed = True

        elif state == 'absent':
            message = 'Cannot delete non-existent group.'
            has_changed = False
            pass

    return group_id, message, has_changed


def find_group_with_same_name(groups, name):
    group_found = False
    group_id = ""
    for group in groups:
        if group['name'] == name:
            group_found = True
            group_id = group.get('id')
            break

    return group_found, group_id


def expand_elastigroup(module, is_update):
    do_not_update = module.params['do_not_update']
    name = module.params.get('name')

    eg = spotinst.aws_elastigroup.Elastigroup()
    description = module.params.get('description')

    if name is not None:
        eg.name = name
    if description is not None:
        eg.description = description

    # Capacity
    expand_capacity(eg, module, is_update, do_not_update)
    # Strategy
    expand_strategy(eg, module)
    # Scaling
    expand_scaling(eg, module)
    # Third party integrations
    expand_integrations(eg, module)
    # Compute
    expand_compute(eg, module, is_update, do_not_update)

    # Multai
    expand_multai(eg, module)

    # Scheduling
    expand_scheduled_tasks(eg, module)

    return eg


def expand_compute(eg, module, is_update, do_not_update):
    elastic_ips = module.params['elastic_ips']
    on_demand_instance_type = module.params.get('on_demand_instance_type')
    spot_instance_types = module.params['spot_instance_types']
    ebs_volume_pool = module.params['ebs_volume_pool']
    availability_zones = module.params['availability_zones']
    product = module.params.get('product')

    eg_compute = spotinst.aws_elastigroup.Compute()

    if product is not None:
        # Only put product on group creation
        if is_update is not True:
            eg_compute.product = product

    if elastic_ips is not None:
        eg_compute.elastic_ips = elastic_ips

    if on_demand_instance_type or spot_instance_types is not None:
        eg_instance_types = spotinst.aws_elastigroup.InstanceTypes()

        if on_demand_instance_type is not None:
            eg_instance_types.spot = spot_instance_types
        if spot_instance_types is not None:
            eg_instance_types.ondemand = on_demand_instance_type

        if eg_instance_types.spot is not None or eg_instance_types.ondemand is not None:
            eg_compute.instance_types = eg_instance_types

    expand_ebs_volume_pool(eg_compute, ebs_volume_pool)

    expand_availability_zones(eg_compute, availability_zones)

    expand_launch_spec(eg_compute, module, is_update, do_not_update)

    eg.compute = eg_compute


def expand_availability_zones(eg_compute, az_list):
    if az_list is not None:
        eg_azs = []

        for az in az_list:
            eg_az = spotinst.aws_elastigroup.AvailabilityZone()
            if az.get('name') is not None:
                eg_az.name = az.get('name')
            if az.get('subnet_id') is not None:
                eg_az.subnet_id = az.get('subnet_id')
            if az.get('placement_group_name') is not None:
                eg_az.placement_group_name = az.get('placement_group_name')

            if eg_az.name is not None:
                eg_azs.append(eg_az)

        if eg_azs.__sizeof__() > 0:
            eg_compute.availability_zones = eg_azs


def expand_ebs_volume_pool(eg_compute, ebs_volumes_list):
    if ebs_volumes_list is not None:
        eg_volumes = []

        for volume in ebs_volumes_list:
            eg_volume = spotinst.aws_elastigroup.EbsVolume()

            if volume.get('device_name') is not None:
                eg_volume.device_name = volume.get('device_name')
            if volume.get('volume_ids') is not None:
                eg_volume.volume_ids = volume.get('volume_ids')

            if eg_volume.deviceName is not None:
                eg_volumes.append(eg_volume)

        if eg_volumes.__sizeof__() > 0:
            eg_compute.ebs_volume_pool = eg_volumes


def expand_launch_spec(eg_compute, module, is_update, do_not_update):
    user_data = module.params.get('user_data')
    key_pair = module.params.get('key_pair')
    iam_role_name = module.params.get('iam_role_name')
    iam_role_arn = module.params.get('iam_role_arn')
    tenancy = module.params.get('tenancy')
    shutdown_script = module.params.get('shutdown_script')
    monitoring = module.params.get('monitoring')
    ebs_optimized = module.params.get('ebs_optimized')
    image_id = module.params.get('image_id')
    health_check_type = module.params.get('health_check_type')
    health_check_grace_period = module.params.get('health_check_grace_period')
    health_check_unhealthy_duration_before_replacement = module.params.get(
        'health_check_unhealthy_duration_before_replacement')
    security_group_ids = module.params['security_group_ids']
    tags = module.params['tags']

    load_balancers = module.params['load_balancers']
    target_group_arns = module.params['target_group_arns']
    block_device_mappings = module.params['block_device_mappings']
    network_interfaces = module.params['network_interfaces']

    eg_launch_spec = spotinst.aws_elastigroup.LaunchSpecification()

    if user_data is not None:
        eg_launch_spec.user_data = user_data

    if monitoring is not None:
        eg_launch_spec.monitoring = monitoring

    if ebs_optimized is not None:
        eg_launch_spec.ebs_optimized = ebs_optimized

    if tenancy is not None:
        eg_launch_spec.tenancy = tenancy

    if shutdown_script is not None:
        eg_launch_spec.shutdown_script = shutdown_script

    if ebs_optimized is not None:
        eg_launch_spec.ebs_optimized = ebs_optimized

    if iam_role_name or iam_role_arn is not None:
        eg_iam_role = spotinst.aws_elastigroup.IamRole()

        if iam_role_name is not None:
            eg_iam_role.name = iam_role_name
        elif iam_role_arn is not None:
            eg_iam_role.arn = iam_role_arn

        if eg_iam_role.name is not None or eg_iam_role.arn is not None:
            eg_launch_spec.iam_role = eg_iam_role

    if key_pair is not None:
        eg_launch_spec.key_pair = key_pair

    if image_id is not None:
        if is_update is True:
            if 'image_id' not in do_not_update:
                eg_launch_spec.image_id = image_id
        else:
            eg_launch_spec.image_id = image_id

    if health_check_type is not None:
        eg_launch_spec.health_check_type = health_check_type

    if health_check_grace_period is not None:
        eg_launch_spec.health_check_grace_period = health_check_grace_period

    if health_check_unhealthy_duration_before_replacement is not None:
        eg_launch_spec.health_check_unhealthy_duration_before_replacement = health_check_unhealthy_duration_before_replacement

    if security_group_ids is not None:
        eg_launch_spec.security_group_ids = security_group_ids

    expand_tags(eg_launch_spec, tags)

    expand_tags(eg_launch_spec, tags)

    expand_load_balancers(eg_launch_spec, load_balancers, target_group_arns)

    expand_block_device_mappings(eg_launch_spec, block_device_mappings)

    expand_network_interfaces(eg_launch_spec, network_interfaces)

    eg_compute.launch_specification = eg_launch_spec


def expand_integrations(eg, module):
    rancher = module.params.get('rancher')
    mesosphere = module.params.get('mesosphere')
    elastic_beanstalk = module.params.get('elastic_beanstalk')
    ecs = module.params.get('ecs')
    kubernetes = module.params.get('kubernetes')
    rightscale = module.params.get('rightscale')
    opsworks = module.params.get('opsworks')
    chef = module.params.get('chef')
    eg_integrations = spotinst.aws_elastigroup.ThirdPartyIntegrations()
    if rancher:
        eg_rancher = spotinst.aws_elastigroup.Rancher(access_key=rancher.get('access_key'),
                                                      secret_key=rancher.get('secret_key'),
                                                      master_host=rancher.get('master_host'))
        eg_integrations.rancher = eg_rancher

    if chef:
        eg_chef = spotinst.aws_elastigroup.ChefConfiguration(chef_server=chef.get('chef_server'),
                                                             organization=chef.get('organization'),
                                                             user=chef.get('user'),
                                                             pem_key=chef.get('pem_key'),
                                                             chef_version=chef.get('chef_version'))
        eg_integrations.chef = eg_chef

    if mesosphere:
        eg_mesosphere = spotinst.aws_elastigroup.Mesosphere(api_server=mesosphere.get('api_server'))
        eg_integrations.mesosphere = eg_mesosphere

    if ecs:
        eg_ecs = spotinst.aws_elastigroup.EcsConfiguration(cluster_name=ecs.get('cluster_name'))
        eg_integrations.ecs = eg_ecs

    if kubernetes:
        eg_kube = spotinst.aws_elastigroup.KubernetesConfiguration(api_server=kubernetes.get('api_server'),
                                                                   token=kubernetes.get('token'))
        eg_integrations.kubernetes = eg_kube

    if rightscale:
        eg_rightscale = spotinst.aws_elastigroup.RightScaleConfiguration(account_id=rightscale.get('account_id'),
                                                                         refresh_token=rightscale.get('refresh_token'))
        eg_integrations.right_scale = eg_rightscale

    if opsworks:
        eg_opsworks = spotinst.aws_elastigroup.OpsWorksConfiguration(layer_id=opsworks.get('layer_id'))
        eg_integrations.ops_works = eg_opsworks

    if eg_integrations.rancher is not None \
            or eg_integrations.rightScale is not None \
            or eg_integrations.ops_works is not None \
            or eg_integrations.chef is not None \
            or eg_integrations.ecs is not None \
            or eg_integrations.elastic_beanstalk is not None \
            or eg_integrations.mesosphere is not None \
            or eg_integrations.kubernetes is not None:
        eg.third_parties_integration = eg_integrations


def expand_capacity(eg, module, is_update, do_not_update):
    min_size = module.params.get('min_size')
    max_size = module.params.get('max_size')
    target = module.params.get('target')
    unit = module.params.get('unit')

    eg_capacity = spotinst.aws_elastigroup.Capacity()

    if min_size is not None:
        eg_capacity.minimum = min_size

    if max_size is not None:
        eg_capacity.maximum = max_size

    if target is not None:
        if is_update is True:
            if 'target' not in do_not_update:
                eg_capacity.target = target
        else:
            eg_capacity.target = target

    if unit is not None:
        # Only put unit on group creation
        if is_update is not True:
            eg_capacity.unit = unit

    eg.capacity = eg_capacity


def expand_strategy(eg, module):
    risk = module.params.get('risk')
    utilize_reserved_instances = module.params.get('utilize_reserved_instances')
    fallback_to_ondemand = module.params.get('fallback_to_ondemand')
    on_demand_count = module.params.get('on_demand_count')
    availability_vs_cost = module.params.get('availability_vs_cost')
    draining_timeout = module.params.get('draining_timeout')
    spin_up_time = module.params.get('spin_up_time')
    lifetime_period = module.params.get('lifetime_period')
    terminate_at_end_of_billing_hour = module.params.get('terminate_at_end_of_billing_hour')
    persistence = module.params.get('persistence')
    signals = module.params['signals']

    eg_strategy = spotinst.aws_elastigroup.Strategy()

    if risk is not None:
        eg_strategy.risk = risk
    if utilize_reserved_instances is not None:
        eg_strategy.utilize_reserved_instances = utilize_reserved_instances
    if fallback_to_ondemand is not None:
        eg_strategy.fallback_to_ondemand = fallback_to_ondemand
    if on_demand_count is not None:
        eg_strategy.on_demand_count = on_demand_count
    if availability_vs_cost is not None:
        eg_strategy.availability_vs_cost = availability_vs_cost
    if draining_timeout is not None:
        eg_strategy.draining_timeout = draining_timeout
    if spin_up_time is not None:
        eg_strategy.spin_up_time = spin_up_time
    if lifetime_period is not None:
        eg_strategy.lifetime_period = lifetime_period
    if terminate_at_end_of_billing_hour is not None:
        eg_scaling_strategy = spotinst.aws_elastigroup.ScalingStrategy()
        eg_scaling_strategy.terminate_at_end_of_billing_hour = terminate_at_end_of_billing_hour
        eg_strategy.eg_scaling_strategy = eg_scaling_strategy

    expand_persistence(eg_strategy, persistence)

    expand_signals(eg_strategy, signals)

    eg.strategy = eg_strategy


def expand_multai(eg, module):
    multai_token = module.params.get('multai_token')
    multai_load_balancers = module.params.get('multai_load_balancers')

    eg_multai = spotinst.aws_elastigroup.Multai()

    if multai_token is not None:
        eg_multai.multai_token = multai_token

    expand_multai_load_balancers(eg_multai, multai_load_balancers)

    eg.multai = eg_multai


def expand_scheduled_tasks(eg, module):
    scheduled_tasks = module.params.get('scheduled_tasks')

    if scheduled_tasks is not None:
        eg_scheduling = spotinst.aws_elastigroup.Scheduling()
        eg_tasks = []

        for task in scheduled_tasks:

            eg_task = spotinst.aws_elastigroup.ScheduledTask()

            if task.get('adjustment') is not None:
                eg_task.adjustment = task.get('adjustment')

            if task.get('adjustment_percentage') is not None:
                eg_task.adjustment_percentage = task.get('adjustment_percentage')

            if task.get('batch_size_percentage') is not None:
                eg_task.batch_size_percentage = task.get('batch_size_percentage')

            if task.get('cron_expression') is not None:
                eg_task.cron_expression = task.get('cron_expression')

            if task.get('frequency') is not None:
                eg_task.frequency = task.get('frequency')

            if task.get('grace_period') is not None:
                eg_task.grace_period = task.get('grace_period')

            if task.get('task_type') is not None:
                eg_task.task_type = task.get('task_type')

            if task.get('is_enabled') is not None:
                eg_task.is_enabled = task.get('is_enabled')

            eg_tasks.append(eg_task)

        if eg_tasks.__sizeof__() > 0:
            eg_scheduling.tasks = eg_tasks
            eg.scheduling = eg_scheduling


def expand_signals(eg_strategy, signals):
    if signals is not None:
        eg_signals = []

        for signal in signals:
            eg_signal = spotinst.aws_elastigroup.Signal()
            if signal.get('name') is not None:
                eg_signal.name = signal.get('name')
            if signal.get('timeout') is not None:
                eg_signal.timeout = signal.get('timeout')

            if eg_signal.name is not None:
                eg_signals.append(eg_signal)

        if eg_signals.__sizeof__() > 0:
            eg_strategy.signals = eg_signals


def expand_multai_load_balancers(eg_multai, multai_load_balancers):
    if multai_load_balancers is not None:
        eg_multai_load_balancers = []

        for multai_load_balancer in multai_load_balancers:
            eg_multai_load_balancer = spotinst.aws_elastigroup.MultaiLoadBalancer()
            if multai_load_balancer.get('balancer_id') is not None:
                eg_multai_load_balancer.balancer_id = multai_load_balancer.get('balancer_id')
            if multai_load_balancer.get('project_id') is not None:
                eg_multai_load_balancer.project_id = multai_load_balancer.get('project_id')
            if multai_load_balancer.get('target_set_id') is not None:
                eg_multai_load_balancer.target_set_id = multai_load_balancer.get('target_set_id')
            if multai_load_balancer.get('az_awareness') is not None:
                eg_multai_load_balancer.az_awareness = multai_load_balancer.get('az_awareness')
            if multai_load_balancer.get('auto_weight') is not None:
                eg_multai_load_balancer.auto_weight = multai_load_balancer.get('auto_weight')

            if eg_multai_load_balancer.balancerId is not None:
                eg_multai_load_balancers.append(eg_multai_load_balancer)

        if eg_multai_load_balancers.__sizeof__() > 0:
            eg_multai.balancers = eg_multai_load_balancers


def expand_load_balancers(eg_launchspec, load_balancers, target_group_arns):
    if load_balancers is not None or target_group_arns is not None:
        eg_load_balancers_config = spotinst.aws_elastigroup.LoadBalancersConfig()
        eg_total_lbs = []

        if load_balancers is not None:
            for elb_name in load_balancers:
                eg_elb = spotinst.aws_elastigroup.LoadBalancer()
                if elb_name is not None:
                    eg_elb.name = elb_name
                    eg_elb.type = 'CLASSIC'
                    eg_total_lbs.append(eg_elb)

        if target_group_arns is not None:
            for target_arn in target_group_arns:
                eg_elb = spotinst.aws_elastigroup.LoadBalancer()
                if target_arn is not None:
                    eg_elb.arn = target_arn
                    eg_elb.type = 'TARGET_GROUP'
                    eg_total_lbs.append(eg_elb)

        if eg_total_lbs.__sizeof__() > 0:
            eg_load_balancers_config.load_balancers = eg_total_lbs
            eg_launchspec.load_balancers_config = eg_load_balancers_config


def expand_tags(eg_launchspec, tags):
    if tags is not None:
        eg_tags = []

        for tag in tags:
            eg_tag = spotinst.aws_elastigroup.Tag()
            if tag.get('key') is not None:
                eg_tag.tag_key = tag.get('key')
            if tag.get('value') is not None:
                eg_tag.tag_value = tag.get('value')

            eg_tags.append(eg_tag)

        if eg_tags.__sizeof__() > 0:
            eg_launchspec.tags = eg_tags


def expand_block_device_mappings(eg_launchspec, bdms):
    if bdms is not None:
        eg_bdms = []

        for bdm in bdms:
            eg_bdm = spotinst.aws_elastigroup.BlockDeviceMapping()
            if bdm.get('device_name') is not None:
                eg_bdm.device_name = bdm.get('device_name')

            if bdm.get('virtual_name') is not None:
                eg_bdm.virtual_name = bdm.get('virtual_name')

            if bdm.get('no_device') is not None:
                eg_bdm.no_device = bdm.get('no_device')

            if bdm.get('ebs') is not None:
                eg_ebs = spotinst.aws_elastigroup.EBS()

                ebs = bdm.get('ebs')

                if ebs.get('delete_on_termination') is not None:
                    eg_ebs.delete_on_termination = ebs.get('delete_on_termination')

                if ebs.get('encrypted') is not None:
                    eg_ebs.encrypted = ebs.get('encrypted')

                if ebs.get('iops') is not None:
                    eg_ebs.iops = ebs.get('iops')

                if ebs.get('snapshot_id') is not None:
                    eg_ebs.snapshot_id = ebs.get('snapshot_id')

                if ebs.get('volume_type') is not None:
                    eg_ebs.volume_type = ebs.get('volume_type')

                if ebs.get('volume_size') is not None:
                    eg_ebs.volume_size = ebs.get('volume_size')

                eg_bdm.ebs = eg_ebs

            eg_bdms.append(eg_bdm)

        if eg_bdms.__sizeof__() > 0:
            eg_launchspec.bl = eg_bdms


def expand_network_interfaces(eg_launchspec, enis):
    if enis is not None:
        eg_enis = []

        for eni in enis:
            eg_eni = spotinst.aws_elastigroup.NetworkInterface()

            if eni.get('description') is not None:
                eg_eni.description = eni.get('description')

            if eni.get('device_index') is not None:
                eg_eni.device_index = eni.get('device_index')

            if eni.get('secondary_private_ip_address_count') is not None:
                eg_eni.secondary_private_ip_address_count = eni.get('secondary_private_ip_address_count')

            if eni.get('associate_public_ip_address') is not None:
                eg_eni.associate_public_ip_address = eni.get('associate_public_ip_address')

            if eni.get('delete_on_termination') is not None:
                eg_eni.delete_on_termination = eni.get('delete_on_termination')

            if eni.get('groups') is not None:
                eg_eni.groups = eni['groups']

            if eni.get('network_interface_id') is not None:
                eg_eni.network_interface_id = eni.get('network_interface_id')

            if eni.get('private_ip_address') is not None:
                eg_eni.private_ip_address = eni.get('private_ip_address')

            if eni.get('subnet_id') is not None:
                eg_eni.subnet_id = eni.get('subnet_id')

            if eni.get('associate_ipv6_address') is not None:
                eg_eni.associate_ipv6_address = eni.get('associate_ipv6_address')

            expand_private_ip_addresses(eg_eni, eni)

            eg_enis.append(eg_eni)

        if eg_enis.__sizeof__() > 0:
            eg_launchspec.network_interfaces = eg_enis


def expand_private_ip_addresses(eg_eni, eni):
    if eni.get('private_ip_addresses') is not None:
        eg_pias = []
        pias = eni.get('private_ip_addresses')

        for pia in pias:
            eg_pia = spotinst.aws_elastigroup.PrivateIpAddress()

            eg_pia_address = pia.get('private_ip_address')
            eg_pia_primary = pia.get('primary')
            eg_pia.private_ip_address = eg_pia_address
            eg_pia.primary = eg_pia_primary

            eg_pias.append(eg_pia)

        eg_eni.private_ip_addresses = eg_pias


def expand_persistence(eg_strategy, persistence):
    if persistence is not None:
        eg_persistence = spotinst.aws_elastigroup.Persistence()
        eg_persistence.should_persist_root_device = persistence.get('should_persist_root_device')
        eg_persistence.should_persist_block_devices = persistence.get('should_persist_block_devices')
        eg_persistence.should_persist_private_ip = persistence.get('should_persist_private_ip')
        eg_strategy.persistence = eg_persistence


def expand_scaling(eg, module):
    up_scaling_policies = module.params['up_scaling_policies']
    down_scaling_policies = module.params['down_scaling_policies']

    eg_scaling = spotinst.aws_elastigroup.Scaling()

    if up_scaling_policies is not None:
        eg_up_scaling_policies = expand_scaling_policies(up_scaling_policies)
        if eg_up_scaling_policies.__sizeof__() > 0:
            eg_scaling.up = eg_up_scaling_policies

    if down_scaling_policies is not None:
        eg_down_scaling_policies = expand_scaling_policies(down_scaling_policies)
        if eg_down_scaling_policies.__sizeof__() > 0:
            eg_scaling.down = eg_down_scaling_policies

    if eg_scaling.down is not None or eg_scaling.up is not None:
        eg.scaling = eg_scaling


def expand_scaling_policies(scaling_policies):
    eg_scaling_policies = []

    for policy in scaling_policies:
        eg_policy = spotinst.aws_elastigroup.ScalingPolicy()

        if policy.get('policy_name') is not None:
            eg_policy.policy_name = policy.get('policy_name')

        if policy.get('namespace') is not None:
            eg_policy.namespace = policy.get('namespace')

        if policy.get('metric_name') is not None:
            eg_policy.metric_name = policy.get('metric_name')

        if policy.get('dimensions') is not None:
            eg_policy.dimensions = policy.get('dimensions')

        if policy.get('statistic') is not None:
            eg_policy.statistic = policy.get('statistic')

        if policy.get('evaluation_periods') is not None:
            eg_policy.evaluation_periods = policy.get('evaluation_periods')

        if policy.get('period') is not None:
            eg_policy.period = policy.get('period')

        if policy.get('threshold') is not None:
            eg_policy.threshold = policy.get('threshold')

        if policy.get('cooldown') is not None:
            eg_policy.cooldown = policy.get('cooldown')

        eg_scaling_action = spotinst.aws_elastigroup.ScalingPolicyAction()

        if policy.get('action_type') is not None:
            eg_scaling_action.type = policy.get('action_type')

        if policy.get('adjustment') is not None:
            eg_scaling_action.adjustment = policy.get('adjustment')

        if policy.get('min_target_capacity') is not None:
            eg_scaling_action.min_target_capacity = policy.get('min_target_capacity')

        if policy.get('max_target_capacity') is not None:
            eg_scaling_action.max_target_capacity = policy.get('max_target_capacity')

        if policy.get('target') is not None:
            eg_scaling_action.target = policy.get('target')

        if policy.get('minimum') is not None:
            eg_scaling_action.minimum = policy.get('minimum')

        if policy.get('maximum') is not None:
            eg_scaling_action.maximum = policy.get('maximum')

        if policy.get('unit') is not None:
            eg_policy.unit = policy.get('unit')

        if policy.get('operator') is not None:
            eg_policy.operator = policy.get('operator')

        eg_scaling_policies.append(eg_policy)

    return eg_scaling_policies


def main():
    if not HAS_SPOTINST_SDK:
        raise Exception("the Spotinst SDK library is required. (pip install spotinst)")

    fields = dict(
        state=dict(default='present', choices=['present', 'absent']),
        do_not_update=dict(default=[], type='list'),
        name=dict(type='str'),
        elastic_ips=dict(type='list'),
        on_demand_instance_type=dict(type='str'),
        spot_instance_types=dict(type='list'),
        ebs_volume_pool=dict(type='list'),
        availability_zones=dict(type='list'),
        product=dict(type='str'),
        user_data=dict(type='str'),
        key_pair=dict(type='str'),
        iam_role_name=dict(type='str'),
        iam_role_arn=dict(type='str'),
        tenancy=dict(type='str'),
        shutdown_script=dict(type='str'),
        monitoring=dict(type='str'),
        ebs_optimized=dict(type='bool'),
        image_id=dict(type='str'),
        health_check_type=dict(type='str'),
        health_check_grace_period=dict(type='int'),
        security_group_ids=dict(type='list'),
        tags=dict(type='list'),
        load_balancers=dict(type='list'),
        target_group_arns=dict(type='list'),
        block_device_mappings=dict(type='list'),
        network_interfaces=dict(type='list'),
        scheduled_tasks=dict(type='list'),
        rancher=dict(required=False, default=None),
        mesosphere=dict(required=False, default=None),
        elastic_beanstalk=dict(required=False, default=None),
        ecs=dict(required=False, default=None),
        kubernetes=dict(required=False, default=None),
        rightscale=dict(required=False, default=None),
        opsworks=dict(required=False, default=None),
        chef=dict(required=False, default=None),
        max_size=dict(type='int'),
        min_size=dict(type='int'),
        target=dict(type='int'),
        unit=dict(type='str'),
        utilize_reserved_instances=dict(type='bool'),
        fallback_to_ondemand=dict(type='bool'),
        risk=dict(type='int'),
        on_demand_count=dict(type='int'),
        availability_vs_cost=dict(type='str'),
        draining_timeout=dict(type='int'),
        spin_up_time=dict(type='int'),
        lifetime_period=dict(type='int'),
        terminate_at_end_of_billing_hour=dict(type='bool'),
        persistence=dict(required=False, default=None),
        signals=dict(type='list'),
        multai_load_balancers=dict(type='list'),
        multai_token=dict(type='str'),
        account_id=dict(type='str'),
        up_scaling_policies=dict(type='list'),
        down_scaling_policies=dict(type='list')
    )

    module = AnsibleModule(argument_spec=fields)

    creds = retrieve_creds()
    token = creds["token"]

    client = spotinst.SpotinstClient(auth_token=token, print_output=False)

    eg_account_id = module.params.get('account_id')

    if eg_account_id is not None:
        client = spotinst.SpotinstClient(auth_token=token, print_output=False, account_id=eg_account_id)

    group_id, message, has_changed = handle_elastigroup(client=client, module=module)

    module.exit_json(changed=has_changed, group_id=group_id, message=message)


def retrieve_creds():
    # Retrieve auth token
    home = expanduser("~")
    vars = dict()
    with open(home + "/.spotinst/credentials", "r") as creds:
        for line in creds:
            eq_index = line.find('=')
            var_name = line[:eq_index].strip()
            string_value = line[eq_index + 1:].strip()
            vars[var_name] = string_value
    return vars


if __name__ == '__main__':
    main()
