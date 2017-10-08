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
from __future__ import (absolute_import, division, print_function)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}
DOCUMENTATION = """
---
module: spotinst_aws_elastigroup
version_added: 2.4
short_description: Create, update or delete Spotinst AWS Elastigroups
author: Spotinst
description:
  - Can create, update, or delete Spotinst AWS Elastigroups
    Launch configuration is part of the elastigroup configuration,
    so no additional modules are necessary for handling the launch configuration.
    This module requires that you install the spotinst Python SDK (pip install spotinst)
    You will have to have a credentials file in this location - <home>/.spotinst/credentials
    The credentials file must contain a row that looks like this
    token = <YOUR TOKEN>
    Full documentation available at https://help.spotinst.com/hc/en-us/articles/115003530285-Ansible-
options:

  availability_vs_cost:
    choices:
      - availabilityOriented
      - costOriented
      - balanced
    description:
      - (String) The strategy orientation.
    required: true

  availability_zones:
    description:
      - (List of Objects) a list of hash/dictionaries of Availability Zones that are configured in the elastigroup;
        '[{"key":"value", "key":"value"}]';
        keys allowed are
        name (String),
        subnet_id (String),
        placement_group_name (String),
    required: true

  block_device_mappings:
    description:
      - (List of Objects) a list of hash/dictionaries of Block Device Mappings for elastigroup instances;
        You can specify virtual devices and EBS volumes.;
        '[{"key":"value", "key":"value"}]';
        keys allowed are
        device_name (List of Strings),
        virtual_name (String),
        no_device (String),
        ebs (Object, expects the following keys-
        delete_on_termination(Boolean),
        encrypted(Boolean),
        iops (Integer),
        snapshot_id(Integer),
        volume_type(String),
        volume_size(Integer))
    required: false

  chef:
    description:
      - (Object) The Chef integration configuration.;
        Expects the following keys - chef_server (String),
        organization (String),
        user (String),
        pem_key (String),
        chef_version (String)
    required: false

  draining_timeout:
    description:
      - (Integer) Time for instance to be drained from incoming requests and deregistered from ELB before termination.
    required: false

  ebs_optimized:
    description:
      - (Boolean) Enable EBS optimization for supported instances which are not enabled by default.;
        Note - additional charges will be applied.
    required: false

  ebs_volume_pool:
    description:
      - (List of Objects) a list of hash/dictionaries of EBS devices to reattach to the elastigroup when available;
        '[{"key":"value", "key":"value"}]';
        keys allowed are -
        volume_ids (List of Strings),
        device_name (String)
    required: false

  ecs:
    description:
      - (Object) The ECS integration configuration.;
        Expects the following key -
        cluster_name (String)
    required: false

  elastic_ips:
    description:
      - (List of Strings) List of ElasticIps Allocation Ids to associate to the group instances
    required: false

  fallback_to_od:
    description:
      - (Boolean) In case of no spots available, Elastigroup will launch an On-demand instance instead
    required: false

  health_check_grace_period:
    description:
      - (Integer) The amount of time, in seconds, after the instance has launched to start and check its health.
    default: 300
    required: false

  health_check_unhealthy_duration_before_replacement:
    description:
      - (Integer) Minimal mount of time instance should be unhealthy for us to consider it unhealthy.
    required: false

  health_check_type:
    choices:
      - ELB
      - HCS
      - TARGET_GROUP
      - MLB
      - EC2
    description:
      - (String) The service to use for the health check.
    required: false

  iam_role_name:
    description:
      - (String) The instance profile iamRole name
      - Only use iam_role_arn, or iam_role_name
    required: false

  iam_role_arn:
    description:
      - (String) The instance profile iamRole arn
      - Only use iam_role_arn, or iam_role_name
    required: false

  id:
    description:
      - (String) The group id if it already exists and you want to update, or delete it.
        This will not work unless the uniqueness_by field is set to id.
        When this is set, and the uniqueness_by field is set, the group will either be updated or deleted, but not created.
    required: false

  ignore_changes:
    choices:
      - image_id
      - target
    description:
      - (List of Strings) list of fields on which changes should be ignored when updating
    required: false

  image_id:
    description:
      - (String) The image Id used to launch the instance.;
        In case of conflict between Instance type and image type, an error will be returned
    required: true

  key_pair:
    description:
      - (String) Specify a Key Pair to attach to the instances
    required: true

  kubernetes:
    description:
      - (Object) The Kubernetes integration configuration.
        Expects the following keys -
        api_server (String),
        token (String)
    required: false

  lifetime_period:
    description:
      - (String) lifetime period
    required: false

  load_balancers:
    description:
      - (List of Strings) List of classic ELB names
    required: false

  max_size:
    description:
      - (Integer) The upper limit number of instances that you can scale up to
    required: true

  mesosphere:
    description:
      - (Object) The Mesosphere integration configuration.
        Expects the following key -
        api_server (String)
    required: false

  min_size:
    description:
      - (Integer) The lower limit number of instances that you can scale down to
    required: true

  monitoring:
    description:
      - (Boolean) Describes whether instance Enhanced Monitoring is enabled
    required: true

  name:
    description:
      - (String) Unique name for elastigroup to be created, updated or deleted
    required: true

  network_interfaces:
    description:
      - (List of Objects) a list of hash/dictionaries of network interfaces to add to the elastigroup;
        '[{"key":"value", "key":"value"}]';
        keys allowed are -
        description (String),
        device_index (Integer),
        secondary_private_ip_address_count (Integer),
        associate_public_ip_address (Boolean),
        delete_on_termination (Boolean),
        groups (List of Strings),
        network_interface_id (String),
        private_ip_address (String),
        subnet_id (String),
        associate_ipv6_address (Boolean),
        private_ip_addresses (List of Objects, Keys are privateIpAddress (String, required) and primary (Boolean))

    required: false

  on_demand_count:
    description:
      - (Integer) Required if risk is not set
      - Number of on demand instances to launch. All other instances will be spot instances.;
        Either set this parameter or the risk parameter
    required: false

  on_demand_instance_type:
    description:
      - (String) On-demand instance type that will be provisioned
    required: true

  opsworks:
    description:
      - (Object) The elastigroup OpsWorks integration configration.;
        Expects the following key -
        layer_id (String)
    required: false

  persistence:
    description:
      - (Object) The Stateful elastigroup configration.;
        Accepts the following keys -
        should_persist_root_device (Boolean),
        should_persist_block_devices (Boolean),
        should_persist_private_ip (Boolean)
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
      - (String) Operation system type._
    required: true

  rancher:
    description:
      - (Object) The Rancher integration configuration.;
        Expects the following keys -
        access_key (String),
        secret_key (String),
        master_host (String)
    required: false

  right_scale:
    description:
      - (Object) The Rightscale integration configuration.;
        Expects the following keys -
        account_id (String),
        refresh_token (String)
    required: false

  risk:
    description:
      - (Integer) required if on demand is not set. The percentage of Spot instances to launch (0 - 100).
    required: false

  roll_config:
    description:
      - (Object) Roll configuration.;
        If you would like the group to roll after updating, please use this feature.
        Accepts the following keys -
        batch_size_percentage(Integer, Required),
        grace_period - (Integer, Required),
        health_check_type(String, Optional),
    required: false

  scheduled_tasks:
    description:
      - (List of Objects) a list of hash/dictionaries of scheduled tasks to configure in the elastigroup;
        '[{"key":"value", "key":"value"}]';
        keys allowed are -
        adjustment (Integer),
        scale_target_capacity (Integer),
        scale_min_capacity (Integer),
        scale_max_capacity (Integer),
        adjustment_percentage (Integer),
        batch_size_percentage (Integer),
        cron_expression (String),
        frequency (String),
        grace_period (Integer),
        task_type (String, required),
        is_enabled (Boolean)
    required: false

  security_group_ids:
    description:
      - (List of Strings) One or more security group IDs. ;
        In case of update it will override the existing Security Group with the new given array
    required: true

  shut_down_script:
    description:
      - (String) The Base64-encoded shutdown script that executes prior to instance termination.
        Encode before setting.
    required: false

  signals:
    description:
      - (List of Objects) a list of hash/dictionaries of signals to configure in the elastigroup;
        keys allowed are -
        name (String, required),
        timeout (Integer)
    required: false

  spin_up_time:
    description:
      - (Integer) spin up time, in seconds, for the instance
    required: false

  spot_instance_types:
    description:
      - (List of Strings) Spot instance type that will be provisioned.
    required: true

  state:
    choices:
      - present
      - absent
    description:
      - (String) create or delete the elastigroup
    required: false

  tags:
    description:
      - (Dictionary) a dictionary of tags to configure in the elastigroup. Please specify list of keys and values (key colon value);
    required: false

  target:
    description:
      - (Integer) The number of instances to launch
    required: true

  target_group_arns:
    description:
      - (List of Strings) List of target group arns instances should be registered to
    required: false

  tenancy:
    choices:
      - default
      - dedicated
    description:
      - (String) dedicated vs shared tenancy
    required: false

  terminate_at_end_of_billing_hour:
    description:
      - (Boolean) terminate at the end of billing hour
    required: false

  unit:
    choices:
      - instance
      - weight
    description:
      - (String) The capacity unit to launch instances by.
    required: true

  up_scaling_policies:
    description:
      - (List of Objects) a list of hash/dictionaries of scaling policies to configure in the elastigroup;
        '[{"key":"value", "key":"value"}]';
        keys allowed are -
        are policy_name (String, required),
        namespace (String, required),
        metric_name (String, required),
        dimensions (List of Objects, Keys allowed are name (String, required) and value (String)),
        statistic (String, required)
        evaluation_periods (String, required),
        period (String, required),
        threshold (String, required),
        cooldown (String, required),
        unit (String, required),
        operator (String, required),
        action_type (String, required),
        adjustment (String),
        min_target_capacity (String),
        target (String),
        maximum (String),
        minimum (String)
    required: false

  down_scaling_policies:
    description:
      - (List of Objects) a list of hash/dictionaries of scaling policies to configure in the elastigroup;
        '[{"key":"value", "key":"value"}]';
        keys allowed are -
        are policy_name (String, required),
        namespace (String, required),
        metric_name (String, required),
        dimensions ((List of Objects), Keys allowed are name (String, required) and value (String)),
        statistic (String, required),
        evaluation_periods (String, required),
        period (String, required),
        threshold (String, required),
        cooldown (String, required),
        unit (String, required),
        operator (String, required),
        action_type (String, required),
        adjustment (String),
        max_target_capacity (String),
        target (String),
        maximum (String),
        minimum (String)
    required: false

  uniqueness_by:
    choices:
      - id
      - name
    description:
      - (String) If your group names are not unique, you may use this feature to update or delete a specific group.
        Whenever this property is set, you must set a group_id in order to update or delete a group, otherwise a group will be created.
    required: false

  user_data:
    description:
      - (String) Base64-encoded MIME user data. Encode before setting the value.
    required: false

  utilize_reserved_instances:
    description:
      - (Boolean) In case of any available Reserved Instances,
         Elastigroup will utilize your reservations before purchasing Spot instances.
    required: false

  wait_for_instances:
    description:
      - (Boolean) Whether or not the elastigroup creation / update actions should wait for the instances to spin
    required: false

  wait_timeout:
    description:
      - (Integer) How long the module should wait for instances before failing the action.;
        Only works if wait_for_instances is True.
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
          do_not_update:
            - image_id
            - target
      register: result
    - debug: var=result

# In this example, we create an elastigroup and wait 600 seconds to retrieve the instances, and use their private ips

- hosts: localhost
  tasks:
    - name: create elastigroup
      spotinst_aws_elastigroup:
          state: present
          account_id: act-1a9dd2b
          risk: 100
          availability_vs_cost: balanced
          availability_zones:
            - name: us-west-2a
              subnet_id: subnet-2b68a15c
          tags:
            - Environment: someEnvValue
            - OtherTagKey: otherValue
          image_id: ami-f173cc91
          key_pair: spotinst-oregon
          max_size: 5
          min_size: 0
          target: 0
          unit: instance
          monitoring: True
          name: ansible-group-tal
          on_demand_instance_type: c3.large
          product: Linux/UNIX
          security_group_ids:
            - sg-8f4b8fe9
          block_device_mappings:
            - device_name: '/dev/sda1'
              ebs:
                volume_size: 100
                volume_type: gp2
          spot_instance_types:
            - c3.large
          do_not_update:
            - image_id
          wait_for_instances: True
          wait_timeout: 600
      register: result

    - name: Store private ips to file
      shell: echo {{ item.private_ip }}\\n >> list-of-private-ips
      with_items: "{{ result.instances }}"
    - debug: var=result

# In this example, we create an elastigroup with multiple block device mappings, tags, and also an account id
# In organizations with more than one account, it is required to specify an account_id

- hosts: localhost
  tasks:
    - name: create elastigroup
      spotinst_aws_elastigroup:
          state: present
          account_id: act-1a9dd2b
          risk: 100
          availability_vs_cost: balanced
          availability_zones:
            - name: us-west-2a
              subnet_id: subnet-2b68a15c
          tags:
            - Environment: someEnvValue
            - OtherTagKey: otherValue
          image_id: ami-f173cc91
          key_pair: spotinst-oregon
          max_size: 5
          min_size: 0
          target: 0
          unit: instance
          monitoring: True
          name: ansible-group-tal
          on_demand_instance_type: c3.large
          product: Linux/UNIX
          security_group_ids:
            - sg-8f4b8fe9
          block_device_mappings:
            - device_name: '/dev/xvda'
              ebs:
                volume_size: 60
                volume_type: gp2
            - device_name: '/dev/xvdb'
              ebs:
                volume_size: 120
                volume_type: gp2
          spot_instance_types:
            - c3.large
          do_not_update:
            - image_id
          wait_for_instances: True
          wait_timeout: 600
      register: result

    - name: Store private ips to file
      shell: echo {{ item.private_ip }}\\n >> list-of-private-ips
      with_items: "{{ result.instances }}"
    - debug: var=result

# In this example we have set up block device mapping with ephemeral devices

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
          block_device_mappings:
            - device_name: '/dev/xvda'
              virtual_name: ephemeral0
            - device_name: '/dev/xvdb/'
              virtual_name: ephemeral1
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

# In this example we create a basic group configuration with a network interface defined.
# Each network interface must have a device index

- hosts: localhost
  tasks:
    - name: create elastigroup
      spotinst_aws_elastigroup:
          state: present
          risk: 100
          availability_vs_cost: balanced
          network_interfaces:
            - associate_public_ip_address: true
              device_index: 0
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
          do_not_update:
            - image_id
            - target
      register: result
    - debug: var=result
'''
RETURN = '''
---
instances:
    description: List of active elastigroup instances and their details.
    returned: success
    type: dict
    sample: [
         {
            "spotInstanceRequestId": "sir-regs25zp",
            "instanceId": "i-09640ad8678234c",
            "instanceType": "m4.large",
            "product": "Linux/UNIX",
            "availabilityZone": "us-west-2b",
            "privateIp": "180.0.2.244",
            "createdAt": "2017-07-17T12:46:18.000Z",
            "status": "fulfilled"
        }
    ]
group_id:
    description: Created / Updated group's ID.
    returned: success
    type: string
    sample: "sig-12345"

'''

HAS_SPOTINST_SDK = False
__metaclass__ = type

import os
import time
from os.path import expanduser
from ansible.module_utils.basic import AnsibleModule

try:
    import spotinst
    from spotinst import SpotinstClientException

    HAS_SPOTINST_SDK = True

except ImportError:
    pass


def handle_elastigroup(client, module):
    has_changed = False
    should_create = False
    group_id = None
    message = 'None'

    name = module.params.get('name')
    state = module.params.get('state')
    uniqueness_by = module.params.get('uniqueness_by')
    external_group_id = module.params.get('id')

    if uniqueness_by == 'id':
        if external_group_id is None:
            should_create = True
        else:
            should_create = False
            group_id = external_group_id
    else:
        groups = client.get_elastigroups()
        group_found, group_id = find_group_with_same_name(groups, name)
        if group_found is True:
            should_create = False
        else:
            should_create = True

    if should_create is True:
        if state == 'present':
            eg = expand_elastigroup(module, is_update=False)

            group = client.create_elastigroup(group=eg)
            group_id = group['id']
            message = 'Created group Successfully.'
            has_changed = True

        elif state == 'absent':
            message = 'Cannot delete non-existent group.'
            has_changed = False
    else:
        eg = expand_elastigroup(module, is_update=True)

        if state == 'present':
            group = client.update_elastigroup(group_update=eg, group_id=group_id)
            message = 'Updated group successfully.'

            try:
                roll_config = module.params.get('roll_config')
                if roll_config:
                    eg_roll = spotinst.aws_elastigroup.Roll(
                        batch_size_percentage=roll_config.get('batch_size_percentage'),
                        grace_period=roll_config.get('grace_period'),
                        health_check_type=roll_config.get('health_check_type')
                    )
                    roll_response = client.roll_group(group_roll=eg_roll, group_id=group_id)
                    message = 'Updated and started rolling the group successfully.'
            except SpotinstClientException as exc:
                message = 'Updated group successfully, but failed to perform roll. Error:' + str(exc)
            has_changed = True

        elif state == 'absent':
            try:
                client.delete_elastigroup(group_id=group_id)
            except SpotinstClientException as exc:
                if "GROUP_DOESNT_EXIST" in exc.message:
                    pass
                else:
                    module.fail_json(msg="Error while attempting to delete group : " + exc.message)

            message = 'Deleted group successfully.'
            has_changed = True

    return group_id, message, has_changed


def retrieve_group_instances(client, module, group_id):
    wait_timeout = module.params.get('wait_timeout')
    wait_for_instances = module.params.get('wait_for_instances')

    if wait_timeout is None:
        wait_timeout = 300

    wait_timeout = time.time() + wait_timeout
    target = module.params.get('target')
    state = module.params.get('state')
    instances = list()

    if state == 'present' and group_id is not None and wait_for_instances is True:

        is_amount_fulfilled = False
        while is_amount_fulfilled is False and wait_timeout > time.time():
            amount_of_fulfilled_instances = 0
            active_instances = client.get_elastigroup_active_instances(group_id=group_id)

            for active_instance in active_instances:
                if active_instance.get('private_ip') is not None:
                    amount_of_fulfilled_instances += 1
                    instances.append(active_instance)

            if amount_of_fulfilled_instances >= target:
                is_amount_fulfilled = True

            time.sleep(10)

    return instances


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
    right_scale = module.params.get('right_scale')
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

    if right_scale:
        eg_right_scale = spotinst.aws_elastigroup.RightScaleConfiguration(account_id=right_scale.get('account_id'),
                                                                          refresh_token=right_scale.get(
                                                                              'refresh_token'))
        eg_integrations.right_scale = eg_right_scale

    if opsworks:
        eg_opsworks = spotinst.aws_elastigroup.OpsWorksConfiguration(layer_id=opsworks.get('layer_id'))
        eg_integrations.ops_works = eg_opsworks

    if eg_integrations.rancher is not None \
            or eg_integrations.right_scale is not None \
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
    fallback_to_od = module.params.get('fallback_to_od')
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
    if fallback_to_od is not None:
        eg_strategy.fallback_to_od = fallback_to_od
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

            if task.get('scale_target_capacity') is not None:
                eg_task.scale_target_capacity = task.get('scale_target_capacity')

            if task.get('scale_min_capacity') is not None:
                eg_task.scale_min_capacity = task.get('scale_min_capacity')

            if task.get('scale_max_capacity') is not None:
                eg_task.scale_max_capacity = task.get('scale_max_capacity')


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

            if eg_multai_load_balancer.balancer_id is not None:
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
            if tag.keys():
                eg_tag.tag_key = tag.keys()[0]
            if tag.values():
                eg_tag.tag_value = tag.values()[0]

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
            eg_launchspec.block_device_mappings = eg_bdms


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

        eg_policy.action = eg_scaling_action

        if policy.get('unit') is not None:
            eg_policy.unit = policy.get('unit')

        if policy.get('operator') is not None:
            eg_policy.operator = policy.get('operator')

        eg_scaling_policies.append(eg_policy)

    return eg_scaling_policies


def main():
    fields = dict(
        account_id=dict(type='str'),
        availability_vs_cost=dict(type='str'),
        availability_zones=dict(type='list'),
        block_device_mappings=dict(type='list'),
        chef=dict(type='dict', required=False, default=None),
        do_not_update=dict(default=[], type='list'),
        down_scaling_policies=dict(type='list'),
        draining_timeout=dict(type='int'),
        ebs_optimized=dict(type='bool'),
        ebs_volume_pool=dict(type='list'),
        ecs=dict(type='dict', required=False, default=None),
        elastic_beanstalk=dict(type='dict', required=False, default=None),
        elastic_ips=dict(type='list'),
        fallback_to_od=dict(type='bool'),
        id=dict(type='str', required=False, default=None),
        health_check_grace_period=dict(type='int'),
        health_check_type=dict(type='str'),
        health_check_unhealthy_duration_before_replacement=dict(type='int'),
        iam_role_arn=dict(type='str'),
        iam_role_name=dict(type='str'),
        image_id=dict(type='str'),
        key_pair=dict(type='str'),
        kubernetes=dict(type='dict', required=False, default=None),
        lifetime_period=dict(type='int'),
        load_balancers=dict(type='list'),
        max_size=dict(type='int'),
        mesosphere=dict(type='dict', required=False, default=None),
        min_size=dict(type='int'),
        monitoring=dict(type='str'),
        multai_load_balancers=dict(type='list'),
        multai_token=dict(type='str'),
        name=dict(type='str'),
        network_interfaces=dict(type='list'),
        on_demand_count=dict(type='int'),
        on_demand_instance_type=dict(type='str'),
        opsworks=dict(type='dict', required=False, default=None),
        persistence=dict(type='dict', required=False, default=None),
        product=dict(type='str'),
        rancher=dict(type='dict', required=False, default=None),
        right_scale=dict(type='dict', required=False, default=None),
        risk=dict(type='int'),
        roll_config=dict(type='dict', required=False, default=None),
        scheduled_tasks=dict(type='list'),
        security_group_ids=dict(type='list'),
        shutdown_script=dict(type='str'),
        signals=dict(type='list'),
        spin_up_time=dict(type='int'),
        spot_instance_types=dict(type='list'),
        state=dict(default='present', choices=['present', 'absent']),
        tags=dict(type='list'),
        target=dict(type='int'),
        target_group_arns=dict(type='list'),
        tenancy=dict(type='str'),
        terminate_at_end_of_billing_hour=dict(type='bool'),
        unit=dict(type='str'),
        user_data=dict(type='str'),
        utilize_reserved_instances=dict(type='bool'),
        uniqueness_by=dict(default='name', choices=['name', 'id']),
        up_scaling_policies=dict(type='list'),
        wait_for_instances=dict(required=False, type='bool', default=False),
        wait_timeout=dict(type='int', required=False),
    )

    module = AnsibleModule(argument_spec=fields)

    if not HAS_SPOTINST_SDK:
        module.fail_json(msg="the Spotinst SDK library is required. (pip install spotinst)")

    token = os.environ.get('SPOTINST_TOKEN')

    if not token:
        creds = retrieve_creds()
        token = creds["token"]

    client = spotinst.SpotinstClient(auth_token=token, print_output=False)

    eg_account_id = module.params.get('account_id')

    if eg_account_id is not None:
        client = spotinst.SpotinstClient(auth_token=token, print_output=False, account_id=eg_account_id)

    group_id, message, has_changed = handle_elastigroup(client=client, module=module)

    instances = retrieve_group_instances(client=client, module=module, group_id=group_id)

    module.exit_json(changed=has_changed, group_id=group_id, message=message, instances=instances)


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
