#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}
DOCUMENTATION = """
---
module: spotinst_aws_elastigroup
version_added: 2.5
short_description: Create, update or delete Spotinst AWS Elastigroups
author: Spotinst (@talzur)
description:
  - Can create, update, or delete Spotinst AWS Elastigroups
    Launch configuration is part of the elastigroup configuration,
    so no additional modules are necessary for handling the launch configuration.
    You will have to have a credentials file in this location - <home>/.spotinst/credentials
    The credentials file must contain a row that looks like this
    token = <YOUR TOKEN>
    Full documentation available at https://help.spotinst.com/hc/en-us/articles/115003530285-Ansible-
requirements:
  - python >= 2.7
  - spotinst_sdk >= 1.0.38
options:

  credentials_path:
    description:
      - (String) Optional parameter that allows to set a non-default credentials path.
       Default is ~/.spotinst/credentials

  account_id:
    description:
      - (String) Optional parameter that allows to set an account-id inside the module configuration
       By default this is retrieved from the credentials path

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

  chef:
    description:
      - (Object) The Chef integration configuration.;
        Expects the following keys - chef_server (String),
        organization (String),
        user (String),
        pem_key (String),
        chef_version (String)

  draining_timeout:
    description:
      - (Integer) Time for instance to be drained from incoming requests and deregistered from ELB before termination.

  ebs_optimized:
    description:
      - (Boolean) Enable EBS optimization for supported instances which are not enabled by default.;
        Note - additional charges will be applied.
    type: bool

  ebs_volume_pool:
    description:
      - (List of Objects) a list of hash/dictionaries of EBS devices to reattach to the elastigroup when available;
        '[{"key":"value", "key":"value"}]';
        keys allowed are -
        volume_ids (List of Strings),
        device_name (String)

  ecs:
    description:
      - (Object) The ECS integration configuration.;
        Expects the following key -
        cluster_name (String)


  elastic_ips:
    description:
      - (List of Strings) List of ElasticIps Allocation Ids (Example C(eipalloc-9d4e16f8)) to associate to the group instances

  fallback_to_od:
    description:
      - (Boolean) In case of no spots available, Elastigroup will launch an On-demand instance instead
    type: bool
  health_check_grace_period:
    description:
      - (Integer) The amount of time, in seconds, after the instance has launched to start and check its health.
    default: 300

  health_check_unhealthy_duration_before_replacement:
    description:
      - (Integer) Minimal mount of time instance should be unhealthy for us to consider it unhealthy.

  health_check_type:
    choices:
      - ELB
      - HCS
      - TARGET_GROUP
      - MLB
      - EC2
    description:
      - (String) The service to use for the health check.

  iam_role_name:
    description:
      - (String) The instance profile iamRole name
      - Only use iam_role_arn, or iam_role_name

  iam_role_arn:
    description:
      - (String) The instance profile iamRole arn
      - Only use iam_role_arn, or iam_role_name

  id:
    description:
      - (String) The group id if it already exists and you want to update, or delete it.
        This will not work unless the uniqueness_by field is set to id.
        When this is set, and the uniqueness_by field is set, the group will either be updated or deleted, but not created.

  ignore_changes:
    choices:
      - image_id
      - target
    description:
      - (List of Strings) list of fields on which changes should be ignored when updating

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

  lifetime_period:
    description:
      - (String) lifetime period

  load_balancers:
    description:
      - (List of Strings) List of classic ELB names

  max_size:
    description:
      - (Integer) The upper limit number of instances that you can scale up to
    required: true

  mesosphere:
    description:
      - (Object) The Mesosphere integration configuration.
        Expects the following key -
        api_server (String)

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

  on_demand_count:
    description:
      - (Integer) Required if risk is not set
      - Number of on demand instances to launch. All other instances will be spot instances.;
        Either set this parameter or the risk parameter

  on_demand_instance_type:
    description:
      - (String) On-demand instance type that will be provisioned
    required: true

  opsworks:
    description:
      - (Object) The elastigroup OpsWorks integration configration.;
        Expects the following key -
        layer_id (String)

  persistence:
    description:
      - (Object) The Stateful elastigroup configration.;
        Accepts the following keys -
        should_persist_root_device (Boolean),
        should_persist_block_devices (Boolean),
        should_persist_private_ip (Boolean)

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
        version (String),
        access_key (String),
        secret_key (String),
        master_host (String)

  right_scale:
    description:
      - (Object) The Rightscale integration configuration.;
        Expects the following keys -
        account_id (String),
        refresh_token (String)

  risk:
    description:
      - (Integer) required if on demand is not set. The percentage of Spot instances to launch (0 - 100).

  roll_config:
    description:
      - (Object) Roll configuration.;
        If you would like the group to roll after updating, please use this feature.
        Accepts the following keys -
        batch_size_percentage(Integer, Required),
        grace_period - (Integer, Required),
        health_check_type(String, Optional)

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

  security_group_ids:
    description:
      - (List of Strings) One or more security group IDs. ;
        In case of update it will override the existing Security Group with the new given array
    required: true

  shutdown_script:
    description:
      - (String) The Base64-encoded shutdown script that executes prior to instance termination.
        Encode before setting.

  signals:
    description:
      - (List of Objects) a list of hash/dictionaries of signals to configure in the elastigroup;
        keys allowed are -
        name (String, required),
        timeout (Integer)

  spin_up_time:
    description:
      - (Integer) spin up time, in seconds, for the instance

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

  tags:
    description:
      - (List of tagKey:tagValue paris) a list of tags to configure in the elastigroup. Please specify list of keys and values (key colon value);

  target:
    description:
      - (Integer) The number of instances to launch
    required: true

  target_group_arns:
    description:
      - (List of Strings) List of target group arns instances should be registered to

  tenancy:
    choices:
      - default
      - dedicated
    description:
      - (String) dedicated vs shared tenancy

  terminate_at_end_of_billing_hour:
    description:
      - (Boolean) terminate at the end of billing hour
    type: bool
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
        policy_name (String, required),
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


  down_scaling_policies:
    description:
      - (List of Objects) a list of hash/dictionaries of scaling policies to configure in the elastigroup;
        '[{"key":"value", "key":"value"}]';
        keys allowed are -
        policy_name (String, required),
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

  target_tracking_policies:
    description:
      - (List of Objects) a list of hash/dictionaries of target tracking policies to configure in the elastigroup;
        '[{"key":"value", "key":"value"}]';
        keys allowed are -
        policy_name (String, required),
        namespace (String, required),
        source (String, required),
        metric_name (String, required),
        statistic (String, required),
        unit (String, required),
        cooldown (String, required),
        target (String, required)

  uniqueness_by:
    choices:
      - id
      - name
    description:
      - (String) If your group names are not unique, you may use this feature to update or delete a specific group.
        Whenever this property is set, you must set a group_id in order to update or delete a group, otherwise a group will be created.


  user_data:
    description:
      - (String) Base64-encoded MIME user data. Encode before setting the value.


  utilize_reserved_instances:
    description:
      - (Boolean) In case of any available Reserved Instances,
         Elastigroup will utilize your reservations before purchasing Spot instances.
    type: bool

  wait_for_instances:
    description:
      - (Boolean) Whether or not the elastigroup creation / update actions should wait for the instances to spin
    type: bool

  wait_timeout:
    description:
      - (Integer) How long the module should wait for instances before failing the action.;
        Only works if wait_for_instances is True.

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


# In this example we create a basic group configuration with a target tracking scaling policy defined

- hosts: localhost
  tasks:
    - name: create elastigroup
      spotinst_aws_elastigroup:
          account_id: act-92d45673
          state: present
          risk: 100
          availability_vs_cost: balanced
          availability_zones:
            - name: us-west-2a
              subnet_id: subnet-79da021e
          image_id: ami-f173cc91
          fallback_to_od: true
          tags:
            - Creator: ValueOfCreatorTag
            - Environment: ValueOfEnvironmentTag
          key_pair: spotinst-labs-oregon
          max_size: 10
          min_size: 0
          target: 2
          unit: instance
          monitoring: True
          name: ansible-group-1
          on_demand_instance_type: c3.large
          product: Linux/UNIX
          security_group_ids:
            - sg-46cdc13d
          spot_instance_types:
            - c3.large
          target_tracking_policies:
            - policy_name: target-tracking-1
              namespace: AWS/EC2
              metric_name: CPUUtilization
              statistic: average
              unit: percent
              target: 50
              cooldown: 120
          do_not_update:
            - image_id
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
    type: str
    sample: "sig-12345"

'''

HAS_SPOTINST_SDK = False
__metaclass__ = type

import os
import time
from ansible.module_utils.basic import AnsibleModule

try:
    import spotinst_sdk as spotinst
    from spotinst_sdk import SpotinstClientException

    HAS_SPOTINST_SDK = True

except ImportError:
    pass

eni_fields = ('description',
              'device_index',
              'secondary_private_ip_address_count',
              'associate_public_ip_address',
              'delete_on_termination',
              'groups',
              'network_interface_id',
              'private_ip_address',
              'subnet_id',
              'associate_ipv6_address')

private_ip_fields = ('private_ip_address',
                     'primary')

capacity_fields = (dict(ansible_field_name='min_size',
                        spotinst_field_name='minimum'),
                   dict(ansible_field_name='max_size',
                        spotinst_field_name='maximum'),
                   'target',
                   'unit')

lspec_fields = ('user_data',
                'key_pair',
                'tenancy',
                'shutdown_script',
                'monitoring',
                'ebs_optimized',
                'image_id',
                'health_check_type',
                'health_check_grace_period',
                'health_check_unhealthy_duration_before_replacement',
                'security_group_ids')

iam_fields = (dict(ansible_field_name='iam_role_name',
                   spotinst_field_name='name'),
              dict(ansible_field_name='iam_role_arn',
                   spotinst_field_name='arn'))

scheduled_task_fields = ('adjustment',
                         'adjustment_percentage',
                         'batch_size_percentage',
                         'cron_expression',
                         'frequency',
                         'grace_period',
                         'task_type',
                         'is_enabled',
                         'scale_target_capacity',
                         'scale_min_capacity',
                         'scale_max_capacity')

scaling_policy_fields = ('policy_name',
                         'namespace',
                         'metric_name',
                         'dimensions',
                         'statistic',
                         'evaluation_periods',
                         'period',
                         'threshold',
                         'cooldown',
                         'unit',
                         'operator')

tracking_policy_fields = ('policy_name',
                          'namespace',
                          'source',
                          'metric_name',
                          'statistic',
                          'unit',
                          'cooldown',
                          'target',
                          'threshold')

action_fields = (dict(ansible_field_name='action_type',
                      spotinst_field_name='type'),
                 'adjustment',
                 'min_target_capacity',
                 'max_target_capacity',
                 'target',
                 'minimum',
                 'maximum')

signal_fields = ('name',
                 'timeout')

multai_lb_fields = ('balancer_id',
                    'project_id',
                    'target_set_id',
                    'az_awareness',
                    'auto_weight')

persistence_fields = ('should_persist_root_device',
                      'should_persist_block_devices',
                      'should_persist_private_ip')

strategy_fields = ('risk',
                   'utilize_reserved_instances',
                   'fallback_to_od',
                   'on_demand_count',
                   'availability_vs_cost',
                   'draining_timeout',
                   'spin_up_time',
                   'lifetime_period')

ebs_fields = ('delete_on_termination',
              'encrypted',
              'iops',
              'snapshot_id',
              'volume_type',
              'volume_size')

bdm_fields = ('device_name',
              'virtual_name',
              'no_device')

kubernetes_fields = ('api_server',
                     'token')

right_scale_fields = ('account_id',
                      'refresh_token')

rancher_fields = ('access_key',
                  'secret_key',
                  'master_host',
                  'version')

chef_fields = ('chef_server',
               'organization',
               'user',
               'pem_key',
               'chef_version')

az_fields = ('name',
             'subnet_id',
             'placement_group_name')

opsworks_fields = ('layer_id',)

scaling_strategy_fields = ('terminate_at_end_of_billing_hour',)

mesosphere_fields = ('api_server',)

ecs_fields = ('cluster_name',)

multai_fields = ('multai_token',)


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
        should_create, group_id = find_group_with_same_name(groups, name)

    if should_create is True:
        if state == 'present':
            eg = expand_elastigroup(module, is_update=False)
            module.debug(str(" [INFO] " + message + "\n"))
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

    health_check_type = module.params.get('health_check_type')

    if wait_timeout is None:
        wait_timeout = 300

    wait_timeout = time.time() + wait_timeout
    target = module.params.get('target')
    state = module.params.get('state')
    instances = list()

    if state == 'present' and group_id is not None and wait_for_instances is True:

        is_amount_fulfilled = False
        while is_amount_fulfilled is False and wait_timeout > time.time():
            instances = list()
            amount_of_fulfilled_instances = 0

            if health_check_type is not None:
                healthy_instances = client.get_instance_healthiness(group_id=group_id)

                for healthy_instance in healthy_instances:
                    if(healthy_instance.get('healthStatus') == 'HEALTHY'):
                        amount_of_fulfilled_instances += 1
                        instances.append(healthy_instance)

            else:
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
    for group in groups:
        if group['name'] == name:
            return False, group.get('id')

    return True, None


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
    availability_zones_list = module.params['availability_zones']
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

    eg_compute.availability_zones = expand_list(availability_zones_list, az_fields, 'AvailabilityZone')

    expand_launch_spec(eg_compute, module, is_update, do_not_update)

    eg.compute = eg_compute


def expand_ebs_volume_pool(eg_compute, ebs_volumes_list):
    if ebs_volumes_list is not None:
        eg_volumes = []

        for volume in ebs_volumes_list:
            eg_volume = spotinst.aws_elastigroup.EbsVolume()

            if volume.get('device_name') is not None:
                eg_volume.device_name = volume.get('device_name')
            if volume.get('volume_ids') is not None:
                eg_volume.volume_ids = volume.get('volume_ids')

            if eg_volume.device_name is not None:
                eg_volumes.append(eg_volume)

        if len(eg_volumes) > 0:
            eg_compute.ebs_volume_pool = eg_volumes


def expand_launch_spec(eg_compute, module, is_update, do_not_update):
    eg_launch_spec = expand_fields(lspec_fields, module.params, 'LaunchSpecification')

    if module.params['iam_role_arn'] is not None or module.params['iam_role_name'] is not None:
        eg_launch_spec.iam_role = expand_fields(iam_fields, module.params, 'IamRole')

    tags = module.params['tags']
    load_balancers = module.params['load_balancers']
    target_group_arns = module.params['target_group_arns']
    block_device_mappings = module.params['block_device_mappings']
    network_interfaces = module.params['network_interfaces']

    if is_update is True:
        if 'image_id' in do_not_update:
            delattr(eg_launch_spec, 'image_id')

    expand_tags(eg_launch_spec, tags)

    expand_load_balancers(eg_launch_spec, load_balancers, target_group_arns)

    expand_block_device_mappings(eg_launch_spec, block_device_mappings)

    expand_network_interfaces(eg_launch_spec, network_interfaces)

    eg_compute.launch_specification = eg_launch_spec


def expand_integrations(eg, module):
    rancher = module.params.get('rancher')
    mesosphere = module.params.get('mesosphere')
    ecs = module.params.get('ecs')
    kubernetes = module.params.get('kubernetes')
    right_scale = module.params.get('right_scale')
    opsworks = module.params.get('opsworks')
    chef = module.params.get('chef')

    integration_exists = False

    eg_integrations = spotinst.aws_elastigroup.ThirdPartyIntegrations()

    if mesosphere is not None:
        eg_integrations.mesosphere = expand_fields(mesosphere_fields, mesosphere, 'Mesosphere')
        integration_exists = True

    if ecs is not None:
        eg_integrations.ecs = expand_fields(ecs_fields, ecs, 'EcsConfiguration')
        integration_exists = True

    if kubernetes is not None:
        eg_integrations.kubernetes = expand_fields(kubernetes_fields, kubernetes, 'KubernetesConfiguration')
        integration_exists = True

    if right_scale is not None:
        eg_integrations.right_scale = expand_fields(right_scale_fields, right_scale, 'RightScaleConfiguration')
        integration_exists = True

    if opsworks is not None:
        eg_integrations.opsworks = expand_fields(opsworks_fields, opsworks, 'OpsWorksConfiguration')
        integration_exists = True

    if rancher is not None:
        eg_integrations.rancher = expand_fields(rancher_fields, rancher, 'Rancher')
        integration_exists = True

    if chef is not None:
        eg_integrations.chef = expand_fields(chef_fields, chef, 'ChefConfiguration')
        integration_exists = True

    if integration_exists:
        eg.third_parties_integration = eg_integrations


def expand_capacity(eg, module, is_update, do_not_update):
    eg_capacity = expand_fields(capacity_fields, module.params, 'Capacity')

    if is_update is True:
        delattr(eg_capacity, 'unit')

        if 'target' in do_not_update:
            delattr(eg_capacity, 'target')

    eg.capacity = eg_capacity


def expand_strategy(eg, module):
    persistence = module.params.get('persistence')
    signals = module.params.get('signals')

    eg_strategy = expand_fields(strategy_fields, module.params, 'Strategy')

    terminate_at_end_of_billing_hour = module.params.get('terminate_at_end_of_billing_hour')

    if terminate_at_end_of_billing_hour is not None:
        eg_strategy.eg_scaling_strategy = expand_fields(scaling_strategy_fields,
                                                        module.params, 'ScalingStrategy')

    if persistence is not None:
        eg_strategy.persistence = expand_fields(persistence_fields, persistence, 'Persistence')

    if signals is not None:
        eg_signals = expand_list(signals, signal_fields, 'Signal')

        if len(eg_signals) > 0:
            eg_strategy.signals = eg_signals

    eg.strategy = eg_strategy


def expand_multai(eg, module):
    multai_load_balancers = module.params.get('multai_load_balancers')

    eg_multai = expand_fields(multai_fields, module.params, 'Multai')

    if multai_load_balancers is not None:
        eg_multai_load_balancers = expand_list(multai_load_balancers, multai_lb_fields, 'MultaiLoadBalancer')

        if len(eg_multai_load_balancers) > 0:
            eg_multai.balancers = eg_multai_load_balancers
            eg.multai = eg_multai


def expand_scheduled_tasks(eg, module):
    scheduled_tasks = module.params.get('scheduled_tasks')

    if scheduled_tasks is not None:
        eg_scheduling = spotinst.aws_elastigroup.Scheduling()

        eg_tasks = expand_list(scheduled_tasks, scheduled_task_fields, 'ScheduledTask')

        if len(eg_tasks) > 0:
            eg_scheduling.tasks = eg_tasks
            eg.scheduling = eg_scheduling


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

        if len(eg_total_lbs) > 0:
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

        if len(eg_tags) > 0:
            eg_launchspec.tags = eg_tags


def expand_block_device_mappings(eg_launchspec, bdms):
    if bdms is not None:
        eg_bdms = []

        for bdm in bdms:
            eg_bdm = expand_fields(bdm_fields, bdm, 'BlockDeviceMapping')

            if bdm.get('ebs') is not None:
                eg_bdm.ebs = expand_fields(ebs_fields, bdm.get('ebs'), 'EBS')

            eg_bdms.append(eg_bdm)

        if len(eg_bdms) > 0:
            eg_launchspec.block_device_mappings = eg_bdms


def expand_network_interfaces(eg_launchspec, enis):
    if enis is not None:
        eg_enis = []

        for eni in enis:
            eg_eni = expand_fields(eni_fields, eni, 'NetworkInterface')

            eg_pias = expand_list(eni.get('private_ip_addresses'), private_ip_fields, 'PrivateIpAddress')

            if eg_pias is not None:
                eg_eni.private_ip_addresses = eg_pias

            eg_enis.append(eg_eni)

        if len(eg_enis) > 0:
            eg_launchspec.network_interfaces = eg_enis


def expand_scaling(eg, module):
    up_scaling_policies = module.params['up_scaling_policies']
    down_scaling_policies = module.params['down_scaling_policies']
    target_tracking_policies = module.params['target_tracking_policies']

    eg_scaling = spotinst.aws_elastigroup.Scaling()

    if up_scaling_policies is not None:
        eg_up_scaling_policies = expand_scaling_policies(up_scaling_policies)
        if len(eg_up_scaling_policies) > 0:
            eg_scaling.up = eg_up_scaling_policies

    if down_scaling_policies is not None:
        eg_down_scaling_policies = expand_scaling_policies(down_scaling_policies)
        if len(eg_down_scaling_policies) > 0:
            eg_scaling.down = eg_down_scaling_policies

    if target_tracking_policies is not None:
        eg_target_tracking_policies = expand_target_tracking_policies(target_tracking_policies)
        if len(eg_target_tracking_policies) > 0:
            eg_scaling.target = eg_target_tracking_policies

    if eg_scaling.down is not None or eg_scaling.up is not None or eg_scaling.target is not None:
        eg.scaling = eg_scaling


def expand_list(items, fields, class_name):
    if items is not None:
        new_objects_list = []
        for item in items:
            new_obj = expand_fields(fields, item, class_name)
            new_objects_list.append(new_obj)

        return new_objects_list


def expand_fields(fields, item, class_name):
    class_ = getattr(spotinst.aws_elastigroup, class_name)
    new_obj = class_()

    # Handle primitive fields
    if item is not None:
        for field in fields:
            if isinstance(field, dict):
                ansible_field_name = field['ansible_field_name']
                spotinst_field_name = field['spotinst_field_name']
            else:
                ansible_field_name = field
                spotinst_field_name = field
            if item.get(ansible_field_name) is not None:
                setattr(new_obj, spotinst_field_name, item.get(ansible_field_name))

    return new_obj


def expand_scaling_policies(scaling_policies):
    eg_scaling_policies = []

    for policy in scaling_policies:
        eg_policy = expand_fields(scaling_policy_fields, policy, 'ScalingPolicy')
        eg_policy.action = expand_fields(action_fields, policy, 'ScalingPolicyAction')
        eg_scaling_policies.append(eg_policy)

    return eg_scaling_policies


def expand_target_tracking_policies(tracking_policies):
    eg_tracking_policies = []

    for policy in tracking_policies:
        eg_policy = expand_fields(tracking_policy_fields, policy, 'TargetTrackingPolicy')
        eg_tracking_policies.append(eg_policy)

    return eg_tracking_policies


def main():
    fields = dict(
        account_id=dict(type='str'),
        availability_vs_cost=dict(type='str', required=True),
        availability_zones=dict(type='list', required=True),
        block_device_mappings=dict(type='list'),
        chef=dict(type='dict'),
        credentials_path=dict(type='path', default="~/.spotinst/credentials"),
        do_not_update=dict(default=[], type='list'),
        down_scaling_policies=dict(type='list'),
        draining_timeout=dict(type='int'),
        ebs_optimized=dict(type='bool'),
        ebs_volume_pool=dict(type='list'),
        ecs=dict(type='dict'),
        elastic_beanstalk=dict(type='dict'),
        elastic_ips=dict(type='list'),
        fallback_to_od=dict(type='bool'),
        id=dict(type='str'),
        health_check_grace_period=dict(type='int'),
        health_check_type=dict(type='str'),
        health_check_unhealthy_duration_before_replacement=dict(type='int'),
        iam_role_arn=dict(type='str'),
        iam_role_name=dict(type='str'),
        image_id=dict(type='str', required=True),
        key_pair=dict(type='str'),
        kubernetes=dict(type='dict'),
        lifetime_period=dict(type='int'),
        load_balancers=dict(type='list'),
        max_size=dict(type='int', required=True),
        mesosphere=dict(type='dict'),
        min_size=dict(type='int', required=True),
        monitoring=dict(type='str'),
        multai_load_balancers=dict(type='list'),
        multai_token=dict(type='str', no_log=True),
        name=dict(type='str', required=True),
        network_interfaces=dict(type='list'),
        on_demand_count=dict(type='int'),
        on_demand_instance_type=dict(type='str'),
        opsworks=dict(type='dict'),
        persistence=dict(type='dict'),
        product=dict(type='str', required=True),
        rancher=dict(type='dict'),
        right_scale=dict(type='dict'),
        risk=dict(type='int'),
        roll_config=dict(type='dict'),
        scheduled_tasks=dict(type='list'),
        security_group_ids=dict(type='list', required=True),
        shutdown_script=dict(type='str'),
        signals=dict(type='list'),
        spin_up_time=dict(type='int'),
        spot_instance_types=dict(type='list', required=True),
        state=dict(default='present', choices=['present', 'absent']),
        tags=dict(type='list'),
        target=dict(type='int', required=True),
        target_group_arns=dict(type='list'),
        tenancy=dict(type='str'),
        terminate_at_end_of_billing_hour=dict(type='bool'),
        token=dict(type='str', no_log=True),
        unit=dict(type='str'),
        user_data=dict(type='str'),
        utilize_reserved_instances=dict(type='bool'),
        uniqueness_by=dict(default='name', choices=['name', 'id']),
        up_scaling_policies=dict(type='list'),
        target_tracking_policies=dict(type='list'),
        wait_for_instances=dict(type='bool', default=False),
        wait_timeout=dict(type='int')
    )

    module = AnsibleModule(argument_spec=fields)

    if not HAS_SPOTINST_SDK:
        module.fail_json(msg="the Spotinst SDK library is required. (pip install spotinst_sdk)")

    # Retrieve creds file variables
    creds_file_loaded_vars = dict()

    credentials_path = module.params.get('credentials_path')

    try:
        with open(credentials_path, "r") as creds:
            for line in creds:
                eq_index = line.find('=')
                var_name = line[:eq_index].strip()
                string_value = line[eq_index + 1:].strip()
                creds_file_loaded_vars[var_name] = string_value
    except IOError:
        pass
    # End of creds file retrieval

    token = module.params.get('token')
    if not token:
        token = os.environ.get('SPOTINST_TOKEN')
    if not token:
        token = creds_file_loaded_vars.get("token")

    account = module.params.get('account_id')
    if not account:
        account = os.environ.get('SPOTINST_ACCOUNT_ID') or os.environ.get('ACCOUNT')
    if not account:
        account = creds_file_loaded_vars.get("account")

    client = spotinst.SpotinstClient(auth_token=token, print_output=False)

    if account is not None:
        client = spotinst.SpotinstClient(auth_token=token, print_output=False, account_id=account)

    group_id, message, has_changed = handle_elastigroup(client=client, module=module)

    instances = retrieve_group_instances(client=client, module=module, group_id=group_id)

    module.exit_json(changed=has_changed, group_id=group_id, message=message, instances=instances)


if __name__ == '__main__':
    main()
