#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}
DOCUMENTATION = """
---
module: spotinst_ocean_cloud
version_added: 2.8
short_description: Create, update or delete Spotinst Ocean
author: Spotinst (@jeffnoehren)
description:
  - Can create, update, or delete Spotinst Ocean
    You will have to have a credentials file in this location - <home>/.spotinst/credentials
    The credentials file must contain a row that looks like this
    token = <YOUR TOKEN>
    Full documentation available at U(https://help.spotinst.com/hc/en-us/articles/115003530285-Ansible-)
requirements:
  - python >= 2.7
  - spotinst_sdk >= 1.0.44
options:

  id:
    type: str
    description:
      - Optional parameters for Updating or deleting cluster based on id. Must have uniquness_by set to "id"

  credentials_path:
    type: str
    default: "/root/.spotinst/credentials"
    description:
      - Optional parameter that allows to set a non-default credentials path.

  account_id:
    type: str
    description:
      - Optional parameter that allows to set an account-id inside the module configuration. By default this is retrieved from the credentials path

  token:
    type: str
    description:
      - Optional parameter that allows to set an token inside the module configuration. By default this is retrieved from the credentials path

  state:
    type: str
    choices:
      - present
      - absent
    default: present
    description:
      - create or delete the elastigroup

  uniqueness_by:
    type: str
    choices:
      - id
      - name
    default: name
    description:
      - If your group names are not unique, you may use this feature to update or delete a specific group.
        Whenever this property is set, you must set a group_id in order to update or delete a group, otherwise a group will be created.

  name:
    type: str
    description:
      - Name for Ocean cluster
    required: true

  controller_cluster_id:
    type: str
    description:
      - This ID must be unique for each Ocean cluster per account
    required: true

  region:
    type: str
    description:
      - Region to deploy Ocean cluster instance Groups
    required: true

  auto_scaler:
    type: dict
    description:
      - Schema containing info on how auto scaler will function
    required: true

  capacity:
    type: dict
    description:
      - Schema containing target, min, and max
    required: true

  strategy:
    type: dict
    description:
      - Schema containing how to run the cluster
    required: true

  compute:
    type: dict
    description:
      - Schema containing info on the type of compute resources to use
    required: true
"""
EXAMPLES = """
#In this basic example, we create an ocean cluster

- hosts: localhost
  tasks:
    - name: create ocean
      spotinst_ocean_cloud:
        account_id: YOUR_ACCOUNT_ID
        token: YOUR_API_TOKEN
        state: present
        name: ansible_test_ocean
        region: us-west-2
        controller_cluster_id: ocean.k8s
        auto_scaler:
          is_enabled: True
          cooldown: 180
          resource_limits:
            max_memory_gib: 1500
            max_vCpu: 750
          down:
            evaluation_periods: 3
          headroom:
            cpu_per_unit: 2000
            memory_per_unit: 0
            num_of_units: 4
          is_auto_config: True
        capacity:
          minimum: 0
          maximum: 0
          target: 0
        strategy:
          utilize_reserved_instances: False
          fallback_to_od: True
          spot_percentage: 100
        compute:
          instance_types:
            whitelist:
              - c4.8xlarge
          subnet_ids:
            - sg-123456
          launch_specification:
            security_group_ids:
              - sg-123456
            image_id: ami-123456
            key_pair: Noam-key
            tags:
              - tag_key: tags
                tag_value: test
      register: result
    - debug: var=result
"""
RETURN = """
---
result:
    type: str
    sample: o-d861f48d
    returned: success
    description: Created Ocean Cluster successfully
"""
HAS_SPOTINST_SDK = False
__metaclass__ = type

import os
import time
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    import spotinst_sdk as spotinst
    from spotinst_sdk import SpotinstClientException

    HAS_SPOTINST_SDK = True

except ImportError:
    pass


# region Request Builder Funcitons
def expand_ocean_request(module, is_update):
    do_not_update = module.params.get('do_not_update') or []

    name = module.params.get('name')
    controller_cluster_id = module.params.get('controller_cluster_id')
    region = module.params.get('region')

    auto_scaler = module.params.get('auto_scaler')
    capacity = module.params.get('capacity')
    strategy = module.params.get('strategy')
    compute = module.params.get('compute')

    ocean = spotinst.spotinst_ocean.Ocean()

    if name is not None:
        if is_update:
            if 'name' not in do_not_update:
                ocean.name = name
        else:
            ocean.name = name

    if controller_cluster_id is not None:
        if is_update:
            if 'controller_cluster_id' not in do_not_update:
                ocean.controller_cluster_id = controller_cluster_id
        else:
            ocean.controller_cluster_id = controller_cluster_id

    if region is not None and not is_update:
        ocean.region = region

    # Auto Scaler
    if auto_scaler is not None:
        if is_update:
            if 'auto_scaler' not in do_not_update:
                expand_auto_scaler(ocean=ocean, auto_scaler=auto_scaler)
        else:
            expand_auto_scaler(ocean=ocean, auto_scaler=auto_scaler)
    # Capacity
    if capacity is not None:
        if is_update:
            if 'capacity' not in do_not_update:
                expand_capacity(ocean=ocean, capacity=capacity)
        else:
            expand_capacity(ocean=ocean, capacity=capacity)
    # Strategy
    if strategy is not None:
        if is_update:
            if 'strategy' not in do_not_update:
                expand_strategy(ocean=ocean, strategy=strategy)
        else:
            expand_strategy(ocean=ocean, strategy=strategy)
    # Compute
    if compute is not None:
        if is_update:
            if 'compute' not in do_not_update:
                expand_compute(ocean=ocean, compute=compute)
        else:
            expand_compute(ocean=ocean, compute=compute)

    return ocean


# region Auto Scaler
def expand_auto_scaler(ocean, auto_scaler):
    ocean_auto_scaler = spotinst.spotinst_ocean.AutoScaler()

    is_enabled = auto_scaler.get('is_enabled')
    cooldown = auto_scaler.get('cooldown')
    resource_limits = auto_scaler.get('resource_limits')
    down = auto_scaler.get('down')
    headroom = auto_scaler.get('headroom')
    is_auto_config = auto_scaler.get('is_auto_config')

    if is_enabled is not None:
        ocean_auto_scaler.is_enabled = is_enabled
    if cooldown is not None:
        ocean_auto_scaler.cooldown = cooldown
    if resource_limits is not None:
        expand_resource_limits(ocean_auto_scaler=ocean_auto_scaler, resource_limits=resource_limits)
    if down is not None:
        expand_down(ocean_auto_scaler=ocean_auto_scaler, down=down)
    if headroom is not None:
        expand_headroom(ocean_auto_scaler=ocean_auto_scaler, headroom=headroom)
    if is_auto_config is not None:
        ocean_auto_scaler.is_auto_config = is_auto_config

    ocean.auto_scaler = ocean_auto_scaler


def expand_resource_limits(ocean_auto_scaler, resource_limits):
    ocean_resource_limits = spotinst.spotinst_ocean.ResourceLimits()

    max_memory_gib = resource_limits.get('max_memory_gib')
    max_vCpu = resource_limits.get('max_vCpu')

    if max_memory_gib is not None:
        ocean_resource_limits.max_memory_gib = max_memory_gib
    if max_vCpu is not None:
        ocean_resource_limits.max_vCpu = max_vCpu

    ocean_auto_scaler.resource_limits = ocean_resource_limits


def expand_down(ocean_auto_scaler, down):
    ocean_down = spotinst.spotinst_ocean.Down()
    evaluation_periods = down.get('evaluation_periods')

    if evaluation_periods is not None:
        ocean_down.evaluation_periods = evaluation_periods

    ocean_auto_scaler.down = ocean_down


def expand_headroom(ocean_auto_scaler, headroom):
    ocean_headroom = spotinst.spotinst_ocean.Headroom()

    cpu_per_unit = headroom.get('cpu_per_unit')
    memory_per_unit = headroom.get('memory_per_unit')
    num_of_units = headroom.get('num_of_units')

    if cpu_per_unit is not None:
        ocean_headroom.cpu_per_unit = cpu_per_unit
    if memory_per_unit is not None:
        ocean_headroom.memory_per_unit = memory_per_unit
    if num_of_units is not None:
        ocean_headroom.num_of_units = num_of_units

    ocean_auto_scaler.headroom = ocean_headroom
# endregion


# region Capacity
def expand_capacity(ocean, capacity):
    ocean_capacity = spotinst.spotinst_ocean.Capacity()

    minimum = capacity.get('minimum')
    maximum = capacity.get('maximum')
    target = capacity.get('target')

    if minimum is not None:
        ocean_capacity.minimum = minimum
    if maximum is not None:
        ocean_capacity.maximum = maximum
    if target is not None:
        ocean_capacity.target = target

    ocean.capacity = ocean_capacity
# endregion


# region Strategy
def expand_strategy(ocean, strategy):
    ocean_strategy = spotinst.spotinst_ocean.Strategy()

    utilize_reserved_instances = strategy.get('utilize_reserved_instances')
    fallback_to_od = strategy.get('fallback_to_od')
    spot_percentage = strategy.get('spot_percentage')

    if utilize_reserved_instances is not None:
        ocean_strategy.utilize_reserved_instances = utilize_reserved_instances
    if fallback_to_od is not None:
        ocean_strategy.fallback_to_od = fallback_to_od
    if spot_percentage is not None:
        ocean_strategy.spot_percentage = spot_percentage

    ocean.strategy = ocean_strategy
# endregion


# region Compute
def expand_compute(ocean, compute):
    ocean_compute = spotinst.spotinst_ocean.Compute()

    instance_types = compute.get('instance_types')
    subnet_ids = compute.get('subnet_ids')
    launch_specification = compute.get('launch_specification')

    if instance_types is not None:
        expand_instance_types(ocean_compute=ocean_compute, instance_types=instance_types)
    if subnet_ids is not None:
        ocean_compute.subnet_ids = subnet_ids
    if launch_specification is not None:
        expand_launch_specification(ocean_compute=ocean_compute, launch_specification=launch_specification)

    ocean.compute = ocean_compute


def expand_instance_types(ocean_compute, instance_types):
    ocean_instance_types = spotinst.spotinst_ocean.InstanceTypes()

    whitelist = instance_types.get('whitelist')
    blacklist = instance_types.get('blacklist')

    if whitelist is not None:
        ocean_instance_types.whitelist = whitelist
    if blacklist is not None:
        ocean_instance_types.blacklist = blacklist

    ocean_compute.instance_types = ocean_instance_types


def expand_launch_specification(ocean_compute, launch_specification):
    ocean_launch_specs = spotinst.spotinst_ocean.LaunchSpecifications()

    security_group_ids = launch_specification.get('security_group_ids')
    image_id = launch_specification.get('image_id')
    iam_instance_profile = launch_specification.get('iam_instance_profile')
    key_pair = launch_specification.get('key_pair')
    user_data = launch_specification.get('user_data')
    tags = launch_specification.get('tags')

    if security_group_ids is not None:
        ocean_launch_specs.security_group_ids = security_group_ids

    if image_id is not None:
        ocean_launch_specs.image_id = image_id

    if iam_instance_profile is not None:
        expand_iam_instance_profile(ocean_launch_specs=ocean_launch_specs, iam_instance_profile=iam_instance_profile)

    if key_pair is not None:
        ocean_launch_specs.key_pair = key_pair

    if user_data is not None:
        ocean_launch_specs.user_data = user_data

    if tags is not None:
        expand_tags(ocean_launch_specs=ocean_launch_specs, tags=tags)

    ocean_compute.launch_specification = ocean_launch_specs


def expand_iam_instance_profile(ocean_launch_specs, iam_instance_profile):
    ocean_iam_instance_profile = spotinst.spotinst_ocean.IamInstanceProfile()

    arn = iam_instance_profile.get('arn')
    name = iam_instance_profile.get('name')

    if arn is not None:
        ocean_iam_instance_profile.arn = arn
    if name is not None:
        ocean_iam_instance_profile.name = name

    ocean_launch_specs.iam_instance_profile = ocean_iam_instance_profile


def expand_tags(ocean_launch_specs, tags):
    tag_list = []

    for single_tag in tags:
        tag = spotinst.spotinst_ocean.Tag()

        tag_key = single_tag.get('tag_key')
        tag_value = single_tag.get('tag_value')

        if tag_key is not None:
            tag.tag_key = tag_key
        if tag_value is not None:
            tag.tag_value = tag_value

        tag_list.append(tag)

    ocean_launch_specs.tags = tag_list
# endregion
# endregion


# region Util Functions
def handle_ocean(client, module):
    request_type, ocean_id = get_request_type_and_id(client=client, module=module)

    group_id = None
    message = None
    has_changed = False

    if request_type == "create":
        group_id, message, has_changed = handle_create(client=client, module=module)
    elif request_type == "update":
        group_id, message, has_changed = handle_update(client=client, module=module, ocean_id=ocean_id)
    elif request_type == "delete":
        group_id, message, has_changed = handle_delete(client=client, module=module, ocean_id=ocean_id)
    else:
        module.fail_json(msg="Action Not Allowed")

    return group_id, message, has_changed


def get_request_type_and_id(client, module):
    request_type = None
    ocean_id = "None"
    should_create = False

    name = module.params.get('name')
    state = module.params.get('state')
    uniqueness_by = module.params.get('uniqueness_by')
    external_ocean_id = module.params.get('id')

    if uniqueness_by == 'id':
        if external_ocean_id is None:
            should_create = True
        else:
            ocean_id = external_ocean_id
    else:
        clusters = client.get_all_ocean_cluster()
        should_create, ocean_id = find_clusters_with_same_name(clusters=clusters, name=name)

    if should_create is True:
        if state == 'present':
            request_type = "create"

        elif state == 'absent':
            request_type = None

    else:
        if state == 'present':
            request_type = "update"

        elif state == 'absent':
            request_type = "delete"

    return request_type, ocean_id


def find_clusters_with_same_name(clusters, name):
    for cluster in clusters:
        if cluster['name'] == name:
            return False, cluster['id']

    return True, None


def get_client(module):
    # Retrieve creds file variables
    creds_file_loaded_vars = dict()

    credentials_path = module.params.get('credentials_path')

    if credentials_path is not None:
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
        token = creds_file_loaded_vars.get("token")

    account = module.params.get('account_id')
    if not account:
        account = creds_file_loaded_vars.get("account")

    client = spotinst.SpotinstClient(auth_token=token, print_output=False)

    if account is not None:
        client = spotinst.SpotinstClient(auth_token=token, account_id=account, print_output=False)

    return client
# endregion


# region Request Functions
def handle_create(client, module):
    cluster_request = expand_ocean_request(module=module, is_update=False)
    ocean = client.create_ocean_cluster(ocean=cluster_request)

    ocean_id = ocean['id']
    message = 'Created Ocean Cluster successfully'
    has_changed = True

    return ocean_id, message, has_changed


def handle_update(client, module, ocean_id):
    cluster_request = expand_ocean_request(module=module, is_update=True)
    client.update_ocean_cluster(ocean_id=ocean_id, ocean=cluster_request)

    message = 'Updated Ocean Cluster successfully'
    has_changed = True

    return ocean_id, message, has_changed


def handle_delete(client, module, ocean_id):
    client.delete_ocean_cluster(ocean_id=ocean_id)

    message = 'Deleted Ocean Cluster successfully'
    has_changed = True

    return ocean_id, message, has_changed
# endregion


def main():
    fields = dict(
        account_id=dict(type='str', fallback=(env_fallback, ['SPOTINST_ACCOUNT_ID', 'ACCOUNT'])),
        token=dict(type='str', fallback=(env_fallback, ['SPOTINST_TOKEN'])),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        id=dict(type='str'),
        uniqueness_by=dict(type='str', default='name', choices=['name', 'id']),
        credentials_path=dict(type='path', default="~/.spotinst/credentials"),

        name=dict(type='str'),
        controller_cluster_id=dict(type='str'),
        region=dict(type='str'),
        auto_scaler=dict(type='dict'),
        capacity=dict(type='dict'),
        strategy=dict(type='dict'),
        compute=dict(type='dict'))

    module = AnsibleModule(argument_spec=fields)

    if not HAS_SPOTINST_SDK:
        module.fail_json(msg="the Spotinst SDK library is required. (pip install spotinst_sdk)")

    client = get_client(module=module)

    group_id, message, has_changed = handle_ocean(client=client, module=module)

    module.exit_json(changed=has_changed, group_id=group_id, message=message, instances=[])


if __name__ == '__main__':
    main()
