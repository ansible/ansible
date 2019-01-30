#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}
DOCUMENTATION = """
---
module: spotinst_mrscaler
version_added: 2.8
short_description: Create, update or delete Spotinst MrScaler
author: Spotinst (@jeffnoehren)
description:
  - Can create, update, or delete Spotinst MrScaler
    You will have to have a credentials file in this location - <home>/.spotinst/credentials
    The credentials file must contain a row that looks like this
    token = <YOUR TOKEN>
    Full documentation available at U(https://help.spotinst.com/hc/en-us/articles/115003530285-Ansible-)
requirements:
  - python >= 2.7
  - spotinst_sdk >= 1.0.44
options:

  id:
    description:
      - (String) The group id if it already exists and you want to update, or delete it.
        This will not work unless the uniqueness_by field is set to id.
        When this is set, and the uniqueness_by field is set, the group will either be updated or deleted, but not created.

  token:
    type: str
    description:
      - Spotinst API Token

  credentials_path:
    type: str
    default: /root/.spotinst/credentials
    description:
      - Optional parameter that allows to set a non-default credentials path.
    required: false

  account_id:
    type: str
    description:
      - Optional parameter that allows to set an account-id inside the module configuration. By default  this is retrieved from the credentials path
    required: false

  state:
    type: str
    choices:
      - present
      - absent
    default: present
    description:
      - If set to present will either create or update, if absent will delete
    required: false

  uniqueness_by:
    type: str
    choices:
      - id
      - name
    default: name
    description:
      - If set to id an id must be provided, if name no id is needed
    required: false

  name:
    type: str
    description:
      - Name for EMR cluster
    required: true

  description:
    type: str
    description:
      - Description of EMR cluster
    required: false

  region:
    type: str
    description:
      - Region to deploy EMR cluster instance Groups
    required: true

  strategy:
    type: dict
    description:
      - Choose to create new cluster, clone an existing cluster or wrap an existing cluster

  scheduling:
    type: dict
    description:
      - List of Scheduled tasks to perform

  scaling:
    type: dict
    description:
      - Lists of up and down scaling policies

  compute:
    type: dict
    description:
      - Schema that contains instance groups and other important resource parameters

  cluster:
    type: dict
    description:
      - Schema that contains cluster parameters

"""
EXAMPLES = """
#Create an EMR Cluster

- hosts: localhost
  tasks:
    - name: create emr
      spotinst_mrScaler:
        account_id: YOUR_ACCOUNT_ID
        token: YOUR_SPOTINST_TOKEN
        state: present
        name: ansible_test_group
        description: this is from ansible
        region: us-west-2
        strategy:
          new:
            release_label: emr-5.17.0
          provisioning_timeout:
            timeout: 15
            timeout_action: terminate
        compute:
          availability_zones:
            - name: us-west-2b
              subnet_id:
          instance_groups:
            master_group:
              instance_types:
                - m3.xlarge
              target: 1
              life_cycle: ON_DEMAND
            core_group:
              instance_types:
                - m3.xlarge
              target: 1
              life_cycle: SPOT
            task_group:
              instance_types:
                - m3.xlarge
              capacity:
                minimum: 0
                maximum: 0
                target: 0
              life_cycle: SPOT
          emr_managed_master_security_group: sg-1234567
          emr_managed_slave_security_group: sg-1234567
          additional_master_security_groups: sg-1234567
            - sg-1234567
          additional_slave_security_groups:
            - sg-1234567
          ec2_key_name: Noam-key
          applications:
            - name: Ganglia
              version: "1.0"
            - name: Hadoop
        cluster:
          visible_to_all_users: true
          termination_protected: false
          keep_job_flow_alive_when_no_steps: true
          log_uri: s3://job-status
          additional_info: "{'test':'more information'}"
          job_flow_role: EMR_EC2_DefaultRole
          security_configuration: test
      register: result
    - debug: var=result
"""
RETURN = """
---
result:
    type: str
    returned: success
    sample: simrs-35124875
    description: Created EMR Cluster successfully.
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
def expand_emr_request(module, is_update):
    do_not_update = module.params.get('do_not_update') or []

    name = module.params.get('name')
    description = module.params.get('description')
    region = module.params.get('region')

    strategy = module.params.get('strategy')
    scheduling = module.params.get('scheduling')
    scaling = module.params.get('scaling')
    compute = module.params.get('compute')
    cluster = module.params.get('cluster')

    emr = spotinst.spotinst_emr.EMR()

    if name is not None:
        emr.name = name
    if description is not None:
        emr.description = description
    if region is not None and not is_update:
        emr.region = region

    if not is_update:
        # Strategy
        if strategy is not None:
            expand_strategy(emr=emr, strategy=strategy)
        # Scheduling
        if scheduling is not None:
            expand_scheduling(emr=emr, scheduling=scheduling)
        # Scaling
        if scaling is not None:
            expand_scaling(emr=emr, scaling=scaling)

    # Compute
    if compute is not None:
        expand_compute(emr=emr, compute=compute, is_update=is_update, do_not_update=do_not_update)
    # Cluster
    if cluster is not None:
        expand_cluster(emr=emr, cluster=cluster, is_update=is_update, do_not_update=do_not_update)

    return emr


# region Strategy
def expand_strategy(emr, strategy):
    emr_strategy = spotinst.spotinst_emr.Strategy()

    wrap = strategy.get('wrap')
    clone = strategy.get('clone')
    new = strategy.get('new')
    provisioning_timeout = strategy.get('provisioning_timeout')

    if wrap is not None:
        expand_wrap(emr_strategy=emr_strategy, wrap=wrap)
    if clone is not None:
        expand_clone(emr_strategy=emr_strategy, clone=clone)
    if new is not None:
        expand_new(emr_strategy=emr_strategy, new=new)
    if provisioning_timeout is not None:
        expand_provisioning_timeout(emr_strategy=emr_strategy, provisioning_timeout=provisioning_timeout)

    emr.strategy = emr_strategy


def expand_wrap(emr_strategy, wrap):
    emr_wrapping = spotinst.spotinst_emr.Wrapping()
    source_cluster_id = wrap.get('source_cluster_id')

    if source_cluster_id is not None:
        emr_wrapping.source_cluster_id = source_cluster_id

    emr_strategy.wrapping = emr_wrapping


def expand_clone(emr_strategy, clone):
    emr_cloning = spotinst.spotinst_emr.Cloning()

    origin_cluster_id = clone.get('origin_cluster_id')
    include_steps = clone.get('include_steps')
    number_of_retries = clone.get('number_of_retries')

    if origin_cluster_id is not None:
        emr_cloning.origin_cluster_id = origin_cluster_id
    if include_steps is not None:
        emr_cloning.include_steps = include_steps
    if number_of_retries is not None:
        emr_cloning.number_of_retries = number_of_retries

    emr_strategy.cloning = emr_cloning


def expand_new(emr_strategy, new):
    emr_new = spotinst.spotinst_emr.New()

    release_label = new.get('release_label')
    number_of_retries = new.get('number_of_retries')

    if release_label is not None:
        emr_new.release_label = release_label
    if number_of_retries is not None:
        emr_new.number_of_retries = number_of_retries

    emr_strategy.new = emr_new


def expand_provisioning_timeout(emr_strategy, provisioning_timeout):
    emr_provisioning_timeout = spotinst.spotinst_emr.ProvisioningTimeout()

    timeout = provisioning_timeout.get('timeout')
    timeout_action = provisioning_timeout.get('timeout_action')

    if timeout is not None:
        emr_provisioning_timeout.timeout = timeout
    if timeout_action is not None:
        emr_provisioning_timeout.timeout_action = timeout_action

    emr_strategy.provisioning_timeout = emr_provisioning_timeout
# endregion


# region Compute
def expand_compute(emr, compute, is_update, do_not_update):
    emr_compute = spotinst.spotinst_emr.Compute()

    ebs_root_volume_size = compute.get('ebs_root_volume_size')
    availability_zones = compute.get('availability_zones')
    bootstrap_actions = compute.get('bootstrap_actions')
    steps = compute.get('steps')
    instance_groups = compute.get('instance_groups')
    configurations = compute.get('configurations')
    emr_managed_master_security_group = compute.get('emr_managed_master_security_group')
    emr_managed_slave_security_group = compute.get('emr_managed_slave_security_group')
    additional_master_security_groups = compute.get('additional_master_security_groups')
    service_access_security_group = compute.get('service_access_security_group')
    custom_ami_id = compute.get('custom_ami_id')
    repo_upgrade_on_boot = compute.get('repo_upgrade_on_boot')
    additional_slave_security_groups = compute.get('additional_slave_security_groups')
    ec2_key_name = compute.get('ec2_key_name')
    applications = compute.get('applications')

    # params not able to be Updated
    if not is_update:
        if ebs_root_volume_size is not None:
            emr_compute.ebs_root_volume_size = ebs_root_volume_size

        if availability_zones is not None:
            emr_compute.availability_zones = availability_zones

        if bootstrap_actions is not None:
            expand_bootstrap_actions(emr_compute=emr_compute, bootstrap_actions=bootstrap_actions)

        if steps is not None:
            expand_steps(emr_compute=emr_compute, steps=steps)

        if configurations is not None:
            expand_configurations(emr_compute=emr_compute, configurations=configurations)

        if emr_managed_master_security_group is not None:
            emr_compute.emr_managed_master_security_group = emr_managed_master_security_group

        if emr_managed_slave_security_group is not None:
            emr_compute.emr_managed_slave_security_group = emr_managed_slave_security_group

        if additional_master_security_groups is not None:
            emr_compute.additional_master_security_groups = additional_master_security_groups

        if service_access_security_group is not None:
            emr_compute.service_access_security_group = service_access_security_group

        if custom_ami_id is not None:
            emr_compute.custom_ami_id = custom_ami_id

        if repo_upgrade_on_boot is not None:
            emr_compute.repo_upgrade_on_boot = repo_upgrade_on_boot

        if additional_slave_security_groups is not None:
            emr_compute.additional_slave_security_groups = additional_slave_security_groups

        if ec2_key_name is not None:
            emr_compute.ec2_key_name = ec2_key_name

        if applications is not None:
            expand_applications(emr_compute=emr_compute, applications=applications)

    # instance_groups is able to be Updated
    if instance_groups is not None:
        expand_instance_groups(emr_compute=emr_compute, instance_groups=instance_groups, is_update=is_update, do_not_update=do_not_update)

    emr.compute = emr_compute


def expand_bootstrap_actions(emr_compute, bootstrap_actions):
    emr_bootstrap_actions = spotinst.spotinst_emr.BootstrapActions()
    file = bootstrap_actions.get('file')

    if file is not None:
        expand_file(schema=emr_bootstrap_actions, file=file)

    emr_compute.bootstrap_actions = emr_bootstrap_actions


def expand_steps(emr_compute, steps):
    emr_steps = spotinst.spotinst_emr.Steps()
    file = steps.get('file')

    if file is not None:
        expand_file(schema=emr_steps, file=file)

    emr_compute.steps = emr_steps


# region Instance Groups
def expand_instance_groups(emr_compute, instance_groups, is_update, do_not_update):
    emr_instance_groups = spotinst.spotinst_emr.InstanceGroups()

    master_group = instance_groups.get('master_group')
    core_group = instance_groups.get('core_group')
    task_group = instance_groups.get('task_group')

    # in create
    if not is_update:
        if master_group is not None:
            expand_master_group(emr_instance_groups=emr_instance_groups, master_group=master_group)
        if core_group is not None:
            expand_core_group(emr_instance_groups=emr_instance_groups, core_group=core_group, is_update=is_update)
        if task_group is not None:
            expand_task_group(emr_instance_groups=emr_instance_groups, task_group=task_group, is_update=is_update)

    # in update
    else:
        if core_group is not None and 'core_group' not in do_not_update:
            expand_core_group(emr_instance_groups=emr_instance_groups, core_group=core_group, is_update=is_update)
        if task_group is not None and 'task_group' not in do_not_update:
            expand_task_group(emr_instance_groups=emr_instance_groups, task_group=task_group, is_update=is_update)

    emr_compute.instance_groups = emr_instance_groups


def expand_master_group(emr_instance_groups, master_group):
    emr_master_groups = spotinst.spotinst_emr.MasterGroup()

    instance_types = master_group.get('instance_types')
    target = master_group.get('target')
    life_cycle = master_group.get('life_cycle')
    configurations = master_group.get('configurations')

    if instance_types is not None:
        emr_master_groups.instance_types = instance_types
    if target is not None:
        emr_master_groups.target = target
    if life_cycle is not None:
        emr_master_groups.life_cycle = life_cycle
    if configurations is not None:
        expand_configurations(schema=emr_master_groups, configurations=configurations)

    emr_instance_groups.master_group = emr_master_groups


def expand_core_group(emr_instance_groups, core_group, is_update):
    emr_core_group = spotinst.spotinst_emr.CoreGroup()

    instance_types = core_group.get('instance_types')
    target = core_group.get('target')
    capacity = core_group.get('capacity')
    life_cycle = core_group.get('life_cycle')
    ebs_configuration = core_group.get('ebs_configuration')
    configurations = core_group.get('configurations')

    # Not able to Update
    if not is_update:
        if instance_types is not None:
            emr_core_group.instance_types = instance_types
        if target is not None:
            emr_core_group.target = target
        if life_cycle is not None:
            emr_core_group.life_cycle = life_cycle
        if ebs_configuration is not None:
            expand_ebs_configuration(schema=emr_core_group, ebs_configuration=ebs_configuration)
        if configurations is not None:
            expand_configurations(schema=emr_core_group, configurations=configurations)

    if capacity is not None:
        expand_capacity(schema=emr_core_group, capacity=capacity)

    emr_instance_groups.core_group = emr_core_group


def expand_task_group(emr_instance_groups, task_group, is_update):
    emr_task_group = spotinst.spotinst_emr.TaskGroup()

    instance_types = task_group.get('instance_types')
    capacity = task_group.get('capacity')
    life_cycle = task_group.get('life_cycle')
    ebs_configuration = task_group.get('ebs_configuration')
    configurations = task_group.get('configurations')

    # Not able to Update
    if not is_update:
        if instance_types is not None:
            emr_task_group.instance_types = instance_types
        if life_cycle is not None:
            emr_task_group.life_cycle = life_cycle
        if ebs_configuration is not None:
            expand_ebs_configuration(schema=emr_task_group, ebs_configuration=ebs_configuration)
        if configurations is not None:
            expand_configurations(schema=emr_task_group, configurations=configurations)

    if capacity is not None:
        expand_capacity(schema=emr_task_group, capacity=capacity)

    emr_instance_groups.task_group = emr_task_group


def expand_ebs_configuration(schema, ebs_configuration):
    emr_ebs_configuration = spotinst.spotinst_emr.EbsConfiguration()

    ebs_block_device_configs = ebs_configuration.get('ebs_block_device_configs')
    ebs_optimized = ebs_configuration.get('ebs_optimized')

    if ebs_block_device_configs is not None:
        emr_block_configs_list = []

        for single_ebs_block_config in ebs_block_device_configs:
            emr_single_ebs_block_config = spotinst.spotinst_emrSingleEbsConfig()

            volume_specification = single_ebs_block_config.get('volume_specification')
            volumes_per_instance = single_ebs_block_config.get('volumes_per_instance')

            if volume_specification is not None:
                emr_single_ebs_block_config.volume_specification = volume_specification
            if volumes_per_instance is not None:
                emr_single_ebs_block_config.volumes_per_instance = volumes_per_instance

            emr_block_configs_list.append(emr_single_ebs_block_config)

        emr_ebs_configuration.ebs_block_device_configs = emr_block_configs_list

    if ebs_optimized is not None:
        emr_ebs_configuration.ebs_optimized = ebs_optimized

    schema.ebs_configuration = emr_ebs_configuration


def expand_capacity(schema, capacity):
    emr_capacity = spotinst.spotinst_emr.Capacity()

    target = capacity.get('target')
    maximum = capacity.get('maximum')
    minimum = capacity.get('minimum')

    if target is not None:
        emr_capacity.target = target
    if maximum is not None:
        emr_capacity.maximum = maximum
    if minimum is not None:
        emr_capacity.minimum = minimum

    schema.capacity = emr_capacity
# endregion


def expand_configurations(schema, configurations):
    emr_configurations = spotinst.spotinst_emr.Configurations()
    file = schema.get('file')

    if file is not None:
        expand_file(schema=emr_configurations, file=file)

    emr_configurations.configurations = emr_configurations


def expand_applications(emr_compute, applications):
    application_list = []

    for single_application in applications:
        emr_application = spotinst.spotinst_emr.Application()

        name = single_application.get('name')
        args = single_application.get('args')
        version = single_application.get('version')

        if name is not None:
            emr_application.name = name
        if args is not None:
            emr_application.args = args
        if version is not None:
            emr_application.version = version

        application_list.append(emr_application)

    emr_compute.applications = application_list


def expand_file(schema, file):
    emr_file = spotinst.spotinst_emr.File()

    bucket = file.get('bucket')
    key = file.get('key')

    if bucket is not None:
        emr_file.bucket = bucket
    if key is not None:
        emr_file.key = key

    schema.file = emr_file
# endregion


# region Cluster
def expand_cluster(emr, cluster, is_update, do_not_update):
    emr_cluster = spotinst.spotinst_emr.Cluster()

    visible_to_all_users = cluster.get('visible_to_all_users')
    termination_protected = cluster.get('termination_protected')
    keep_job_flow_alive_when_no_steps = cluster.get('keep_job_flow_alive_when_no_steps')
    log_uri = cluster.get('log_uri')
    additional_info = cluster.get('additional_info')
    job_flow_role = cluster.get('job_flow_role')
    security_configuration = cluster.get('security_configuration')

    # in create
    if not is_update:
        if visible_to_all_users is not None:
            emr_cluster.visible_to_all_users = visible_to_all_users

        if keep_job_flow_alive_when_no_steps is not None:
            emr_cluster.keep_job_flow_alive_when_no_steps = keep_job_flow_alive_when_no_steps

        if log_uri is not None:
            emr_cluster.log_uri = log_uri

        if additional_info is not None:
            emr_cluster.additional_info = additional_info

        if job_flow_role is not None:
            emr_cluster.job_flow_role = job_flow_role

        if security_configuration is not None:
            emr_cluster.security_configuration = security_configuration

        if termination_protected is not None:
            emr_cluster.termination_protected = termination_protected

    # in update
    else:
        if termination_protected is not None and 'termination_protected' not in do_not_update:
            emr_cluster.termination_protected = termination_protected

    emr.cluster = emr_cluster
# endregion


# region scheduling
def expand_scheduling(emr, scheduling):
    emr_scheduing = spotinst.spotinst_emr.Scheduling()
    tasks = scheduling.get('scheduling')

    if tasks is not None:
        expand_tasks(emr_scheduing=emr_scheduing, tasks=tasks)

    emr.scheduling = emr_scheduing


def expand_tasks(emr_scheduing, tasks):
    task_list = []

    for single_task in tasks:
        task = spotinst.spotinst_emr.Task()

        is_enabled = single_task.get('is_enabled')
        instance_group_type = single_task.get('instance_group_type')
        task_type = single_task.get('task_type')
        cron_expression = single_task.get('cron_expression')
        target_capacity = single_task.get('target_capacity')
        min_capacity = single_task.get('min_capacity')
        max_capacity = single_task.get('max_capacity')

        if is_enabled is not None:
            task.is_enabled = is_enabled
        if instance_group_type is not None:
            task.instance_group_type = instance_group_type
        if task_type is not None:
            task.task_type = task_type
        if cron_expression is not None:
            task.cron_expression = cron_expression
        if target_capacity is not None:
            task.target_capacity = target_capacity
        if min_capacity is not None:
            task.min_capacity = min_capacity
        if max_capacity is not None:
            task.max_capacity = max_capacity

        task_list.append(task)

    emr_scheduing.tasks = task_list
# endregion


# region Scaling
def expand_scaling(emr, scaling):
    emr_scaling = spotinst.spotinst_emr.Scaling()

    up = scaling.get('up')
    down = scaling.get('down')

    if up is not None:
        expand_metrics(emr_scaling=emr_scaling, metrics=up, direction="up")
    if down is not None:
        expand_metrics(emr_scaling=emr_scaling, metrics=down, direction="down")

    emr.scaling = emr_scaling


def expand_metrics(emr_scaling, metrics, direction):
    metric_list = []

    for single_metric in metrics:
        emr_metric = spotinst.spotinst_emr.Metric()

        metric_name = single_metric.get('metric_name')
        statistic = single_metric.get('statistic')
        unit = single_metric.get('unit')
        threshold = single_metric.get('threshold')
        adjustment = single_metric.get('adjustment')
        namespace = single_metric.get('namespace')
        period = single_metric.get('period')
        evaluation_periods = single_metric.get('evaluation_periods')
        action = single_metric.get('action')
        cooldown = single_metric.get('cooldown')
        dimensions = single_metric.get('dimensions')
        operator = single_metric.get('operator')

        if metric_name is not None:
            emr_metric.metric_name

        if statistic is not None:
            emr_metric.statistic

        if unit is not None:
            emr_metric.unit

        if threshold is not None:
            emr_metric.threshold

        if adjustment is not None:
            emr_metric.adjustment

        if namespace is not None:
            emr_metric.namespace

        if period is not None:
            emr_metric.period

        if evaluation_periods is not None:
            emr_metric.evaluation_periods

        if action is not None:
            expand_action(emr_metric=emr_metric, action=action)

        if cooldown is not None:
            emr_metric.cooldown

        if dimensions is not None:
            expand_dimensions(emr_metric=emr_metric, dimensions=dimensions)

        if operator is not None:
            emr_metric.operator

        metric_list.append(emr_metric)

    if direction == "up":
        emr_scaling.up = metric_list

    if direction == "down":
        emr_scaling.down = metric_list


def expand_action(emr_metric, action):
    emr_action = spotinst.spotinst_emr.Action()

    type_val = action.get('type')
    adjustment = action.get('adjustment')
    min_target_capacity = action.get('min_target_capacity')
    target = action.get('target')
    minimum = action.get('minimum')
    maximum = action.get('maximum')

    if type_val is not None:
        emr_action.type = type_val
    if adjustment is not None:
        emr_action.adjustment = adjustment
    if min_target_capacity is not None:
        emr_action.min_target_capacity = min_target_capacity
    if target is not None:
        emr_action.target = target
    if minimum is not None:
        emr_action.minimum = minimum
    if maximum is not None:
        emr_action.maximum = maximum

    emr_metric.action = emr_action


def expand_dimensions(emr_metric, dimensions):
    dim_list = []

    for single_dim in dimensions:
        emr_dimension = spotinst.spotinst_emr.Dimension()
        name = single_dim.get('name')

        if name is not None:
            emr_dimension.name = name

        dim_list.append(emr_dimension)

    emr_metric.dimensions = dim_list
# endregion
# endregion


# region Util Functions
def handle_emr(client, module):
    request_type, emr_id = get_request_type_and_id(client=client, module=module)

    group_id = None
    message = None
    has_changed = False

    if request_type == "create":
        group_id, message, has_changed = handle_create(client=client, module=module)
    elif request_type == "update":
        group_id, message, has_changed = handle_update(client=client, module=module, emr_id=emr_id)
    elif request_type == "delete":
        group_id, message, has_changed = handle_delete(client=client, module=module, emr_id=emr_id)
    else:
        module.fail_json(msg="Action Not Allowed")

    return group_id, message, has_changed


def get_request_type_and_id(client, module):
    request_type = None
    emr_id = None
    should_create = False

    name = module.params.get('name')
    state = module.params.get('state')
    uniqueness_by = module.params.get('uniqueness_by')
    external_emr_id = module.params.get('id')

    if uniqueness_by == 'id':
        if external_emr_id is None:
            should_create = True
        else:
            emr_id = external_emr_id
    else:
        clusters = client.get_all_emr()
        should_create, emr_id = find_clusters_with_same_name(clusters=clusters, name=name)

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

    return request_type, emr_id


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
    cluster_request = expand_emr_request(module=module, is_update=False)
    emr = client.create_emr(emr=cluster_request)

    emr_id = emr['id']
    message = 'Created EMR Cluster Successfully.'
    has_changed = True

    return emr_id, message, has_changed


def handle_update(client, module, emr_id):
    cluster_request = expand_emr_request(module=module, is_update=True)
    client.update_emr(emr_id=emr_id, emr=cluster_request)

    message = 'Updated EMR Cluster successfully.'
    has_changed = True

    return emr_id, message, has_changed


def handle_delete(client, module, emr_id):
    client.delete_emr(emr_id=emr_id)

    message = 'Deleted EMR Cluster successfully.'
    has_changed = True

    return emr_id, message, has_changed
# endregion


def main():
    fields = dict(
        account_id=dict(type='str', fallback=(env_fallback, ['SPOTINST_ACCOUNT_ID', 'ACCOUNT'])),
        token=dict(type='str', fallback=(env_fallback, ['SPOTINST_TOKEN'])),
        state=dict(default='present', choices=['present', 'absent']),
        id=dict(type='str'),
        uniqueness_by=dict(default='name', choices=['name', 'id']),
        credentials_path=dict(type='path', default="~/.spotinst/credentials"),

        name=dict(type='str'),
        description=dict(type='str'),
        region=dict(type='str'),
        strategy=dict(type='dict'),
        compute=dict(type='dict'),
        cluster=dict(type='dict'),
        scheduling=dict(type='dict'),
        scaling=dict(type='dict'))

    module = AnsibleModule(argument_spec=fields)

    if not HAS_SPOTINST_SDK:
        module.fail_json(msg="the Spotinst SDK library is required. (pip install spotinst_sdk)")

    client = get_client(module=module)

    group_id, message, has_changed = handle_emr(client=client, module=module)

    module.exit_json(changed=has_changed, group_id=group_id, message=message)


if __name__ == '__main__':
    main()
