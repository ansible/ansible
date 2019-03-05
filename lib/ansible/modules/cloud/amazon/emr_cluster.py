#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: emr_cluster
short_description:  Creates and deletes EMR Clusters.
version_added: "2.8"
description:
  - Creates and deletes EMR Clusters, you could set up EMR Steps
    (spark jobs, for example) when it starts.
requirements: [boto3]
options:
  name:
    description:
      - The name of the Cluster. Required if C(state=present).
    required: false
  log_uri:
    description:
      - The bucket path to store logs.
    required: false
  additional_info:
    description:
      - A JSON string for selecting additional features.
    required: false
  ami_version:
    description:
      - Applies only to Amazon EMR AMI versions 3.x and 2.x. For EMR release 4.0 and later
        I(release_label) is used. To specify a custom AMI, use I(custom_ami_id).
    required: false
  release_label:
    description:
      - Determines what's the versions of the open source application packages installed
        on the Cluster. See U(https://docs.aws.amazon.com/emr/latest/ReleaseGuide/emr-release-components.html).
    required: false
  instances:
    description:
      - Settings for specify the number and type of the Amazon EC2 instances. Required if I(state=present).
    required: false
    suboptions:
      master_instance_type:
        description:
          - The EC2 instance type of the master node.
      slave_instance_type:
        description:
          - The EC2 instance type of the core node.
      instance_count:
        description:
          - The number of EC2 core node on the Cluster.
      instance_groups:
        description:
          - A list to customize the number and the type of the instances in the Cluster for
            MASTER, CORE and Task node. See U(https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-master-core-task-nodes.html)
        suboptions:
          name:
            description:
              - Friendly name given to the instance group.
          market:
            description:
              - Define if the instance group will use ON_DEMAND or SPOT instances.
            choices: ['ON_DEMAND', 'SPOT']
          instance_role:
            description:
              - The role of the instance group in the cluster.
            required: true
            choices: ['MASTER', 'CORE', 'TASK']
          instance_type:
            description:
              - The instance type for all instances in the group.
            required: true
          instance_count:
            description:
              - The number of instances for the instance group.
            required: true
          auto_scaling_policy:
            description:
              - An automatic scaling policy for a core or task instance group.
                See U(https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/emr.html#EMR.Client.run_job_flow)
      instance_fleets:
        description:
          - Using instance_fleets to specify target capacities for On-Demand and
            Spot instances.
        suboptions:
          name:
            description:
              - A friendly name of the instance fleet.
          instance_fleet_type:
            description:
              - The node type.
            required: true
            choices: ['MASTER', 'CORE', 'TASK']
          target_on_demand_capacity:
            description:
              - How many On-Demand instances to provision.
          target_spot_capacity:
            description:
              - How many Spot instances to provision.
          instance_type_configs:
            description:
              - Define EC2 settings in the instance fleet.
            suboptions:
              instance_type:
                description:
                  - An EC2 instance type.
                required: true
              weighted_capacity:
                description:
                  - The number of units that a provisioned instance of this
                    type provides toward fulfilling the target capacities.
              bid_price:
                description:
                  - The bid price for each EC2 Spot instance
              bid_price_as_percentage_of_on_demand_price:
                description:
                  - The bid price, as an percentage of On-Demand price.
              launch_specifications:
                description:
                  - The launch specification, which determines the defined
                    duration and provision timeout behavior.
      ec2_key_name:
        description:
          - The name of the EC2 key pair.
      placement:
        description:
          - The availability zone in which the cluster runs.
      keep_job_flow_alive_when_no_steps:
        description:
          - Specifies if the cluster should be avaiable after completing all steps.
        default: false
      termination_protected:
        description:
          - Determines termination protection.
      hadoop_version:
        description:
          - Applies only to Amazon EMR release versions earlier than 4.0. The Hadoop version for the cluster
      ec2_subnet_id:
        description:
          - Applies to clusters that use the uniform instance group configuration.
      ec2_subnet_ids:
        description:
          - Applies to clusters that use the instance fleets configuration.
      emr_managed_master_security_group:
        description:
          - The identifier of the Amazon EC2 security group for the master node.
      emr_managed_slave_security_group:
        description:
          - The identifier of the Amazon EC2 security group for the core and task nodes.
      additional_master_security_groups:
        description:
          - A list of additional Amazon EC2 security group IDs for the master node
      additional_slave_security_groups:
        description:
          - A list of additional Amazon EC2 security group IDs for the core and task nodes.
  steps:
    description:
      - List of steps to run.
    required: false
    suboptions:
      name:
        description:
          - The name of the step.
        required: true
      action_on_failure:
        description:
          - The action to take when step fails.
        choices:
          - TERMINATE_JOB_FLOW
          - TERMINATE_CLUSTER
          - CANCEL_AND_WAIT
          - CONTINUE
        default: TERMINATE_CLUSTER
      hadoop_jar_step:
        description:
          - A dict with parameters to step.
        suboptions:
          properties:
            description:
              - A list of java properties that are set when the step runs.
          jar:
            description:
              - A path to a JAR file run during the step.
            required: true
          main_class:
            description:
              - The name of the main class in the specified java file.
          args:
            description:
              - A list of arguments passed to JAR.
  bootstrap_actions:
    description:
      - A list of boostrap actions to run before cluster starts.
    required: false
    suboptions:
      name:
        description:
          - A friendly name for the action.
      script_path:
        description:
          - The s3 location of the script.
      args:
        description:
          - Arguments pass to the script.
            The script will access these arguments throughout $1, $2 and so on.
  supported_products:
    description:
      - For Amazon EMR releases 4.x and later, use I(Applications).
        A list of strings that indicates third-party software to use
    required: false
  new_supported_products:
    description:
      - For Amazon EMR releases 4.x and later, use I(Applications).
        A list of strings that indicates third-party software to use with the job flow that accepts a user argument list.
    required: false
  applications:
    description:
      - Applies to Amazon EMR releases 4.0 and later.
        A case-insensitive list of applications for Amazon EMR to install and configure when launching the cluster.
    required: false
  visible_to_all_users:
    description:
      - Defines if the cluster will be avaiable for all users.
    required: false
    default: true
  job_flow_role:
    description:
      - The IAM Role used by EC2 instances.
    required: false
    default: EMR_EC2_DefaultRole
  service_role:
    description:
      - The IAM role that will be assumed by the Amazon EMR service.
    required: false
    default: EMR_DefaultRole
  security_configuration:
    description:
      - The name of a security configuration to apply to the cluster.
    required: false
  auto_scaling_role:
    description:
      - An IAM role for automatic scaling policies
    required: false
  scale_down_behavior:
    description:
      - Specifies the way that individual Amazon EC2 instances terminate.
    required: false
  custom_ami_id:
    description:
      - The ID of a custom AMI. If specified, Amazon EMR uses this AMI when it launches cluster EC2 instances.
        See U(https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-custom-ami.html).
    required: false
  ebs_root_volume_size:
    description:
      -  The size in GB of the root device.
    required: false
  repo_upgrade_on_boot:
    description:
      - Applies only when CustomAmiID is used. Specifies which updates from the Amazon Linux
        AMI package repositories to apply automatically when the instance boots using the AMI.
    required: false
  kerberos_attributes:
    description:
      - Attributes for Kerberos configuration when Kerberos authentication is enabled using a security configuration
    required: false
  state:
    description:
      - Create or destroy the EMR.
    choices: ['present', 'absent']
    default: present
  cluster_id:
    description:
      - The cluster_id used when state is absent. Required when C(state=absent).
    required: false
  tags:
    description:
      - A dict with tags that will be associate with EC2 instances.
    required: false
  wait:
    description:
      - Wait until the EMR state is RUNNING
    required: false
  wait_delay:
    description:
      - The amount of time in seconds to wait between attempts.
    required: false
    type: int
    default: 30
  wait_max_attempts:
    description:
      - The number of attempts to EMR state is RUNNING.
    required: false
    type: int
    default: 60
  configurations:
    description:
      - A dict with custom settings for applications installed
        in the EMR. See U(https://docs.aws.amazon.com/emr/latest/ReleaseGuide/emr-configure-apps.html)
    required: false
  ebs_volumes:
    description:
      - A list to create extra volumes
    required: false
    suboptions:
      type:
        description:
          - The volume type.
        choices: ['gp2', 'io1', 'standard']
        default: gp2
      size:
        description:
          - The volume size in Gigabytes.
      iops:
        description;
          - The number of I/O operations that the volume supports.
      device:
        description:
          - The device name that is exposed to the instance.
      volumes_per_instance:
        description:
          - Number of EBS volumes that will be associated with every instance in the group.
  ebs_optimized:
    description:
      - Indicates whether a volume is EBS-optimized.
    required: false
    type: bool
    default: false
author:
  - Wellington Moreira Ramos (@wmaramos)
extends_documentation_fragment:
  - aws
  - ec2
notes:
  - This module will get EMR name when the state is present to verify if the cluster already exist, but
    the EMR API don't have a unique field to ensure that behavior, so could you've some cases that
    exists more than one cluster with the same name. At this case you'll receive a warn.
'''

EXAMPLES = '''
- emr_cluster:
    name: emr-jobs
    region: us-east-1
    log_uri: s3://bucket-name/logs/emr
    wait: yes
    ebs_optimized: yes
    ebs_volumes:
      - type: gp2
        size: 300
    bootstrap_actions:
      - name: bootstrap
        script_bootstrap_action:
          path: s3://bucket-name/path/to/script.sh
          args:
            - argv1
            - argv2
    configurations:
      core-site:
        hadoop.security.groups.cache.secs: 250
      mapred-site:
        mapred.tasktracker.map.tasks.maximum: 2
        mapreduce.map.sort.spill.percent: 0.90
        mapreduce.tasktracker.reduce.tasks.maximum: 5
      spark:
        maximizeResourceAllocation: true
      hbase-site:
        hbase.rootdir: s3://bucket-name/hbase-site
    applications:
      - name: Hadoop
      - name: Spark
      - name: HBase
    steps:
      - name: s3-dist-cp
        hadoop_jar_step:
          jar: command-runner.jar
          action_on_failure: TERMINATE_CLUSTER
          args:
            - "s3-dist-cp"
            - "--src=s3://bucket-name/events"
            - "--dest=hdfs:///aggregate"
            - "--groupBy=.*/[0-9]{4}/[0-9]{2}/.*gz"
            - "--targetSize=128"
            - "--outputCode=snappy"
    instances:
      ec2_key_name: ec2_key
      ec2_subnet_id: subnet-923a31db
      additional_slave_security_groups:
        - sg-8eb2b1f1
      additional_master_security_groups:
        - sg-8eb2b1f1
      instance_groups:
        - name: master
          instance_role: MASTER
          instance_count: 1
          instance_type: m3.xlarge
          market: ON_DEMAND
        - name: core
          instance_role: CORE
          instance_count: 4
          instance_type: m3.xlarge
          market: ON_DEMAND
'''

RETURN = '''
---
applications:
  description: The applications installed on this cluster.
  returned: always
  type: complex
  contains:
    name:
      description: The name of the application.
      returned: always
      type: str
    version:
      description: The version of the application.
      returned: always
      type: str
    args:
      description: Arguments for EMR pass to application.
      type: str
    additional_info:
      description: Meta information about third party applications.
      type: str
auto_terminate:
  description: Specifies if the cluter should be terminate after completing all steps.
  returned: always
  type: bool
changed:
  description: Specifies if any settings was changed or not.
  returned: always
  type: bool
configurations:
  description: The list of configurations supplied to EMR cluster.
  returned: always
  type: complex
  contains:
    classification:
      description: The classification whithin a configuration. See U(https://docs.aws.amazon.com/emr/latest/ReleaseGuide/emr-configure-apps.html)
      type: str
      sample: mapred-site
    properties:
      description: A dict with all settings applied to classification.
      type: dict
      sample:
        mapred.tasktracker.map.tasks.maximum: 2
        mapreduce.map.sort.spill.percent: 0.9
        mapreduce.tasktracker.reduce.tasks.maximum: 5
ec2_instance_attributes:
    description: Provides information about EC2 settings.
    returned: always
    type: complex
    contains:
      ec2_key_name:
        description: The EC2 key pair use to connect to hadoop user.
        type: str
        sample: emr-key-name
      ec2_subnet_id:
        description: The Amazon VPC subnet
        type: str
        sample: subnet-925a31cd
      requested_ec2_subnet_ids:
        description: Specifies one or more EC2 subnets. Applies only with instance_fleets.
        type: list
        sample:
          - "subnet-923affd"
      ec2_availability_zone:
        description: The availability zone in which cluster runs.
        type: str
        sample: us-east-1a
      requested_ec2_availability_zones:
        description: Specified one or more availability zones. Applies only with instance_fleets.
        type: list
        sample:
          - "us-east-1a"
          - "us-east-1b"
      iam_instance_profile:
        description: The IAM role that was specified when cluster was launched.
        type: str
        sample: EMR_EC2_DefaultRole
      emr_managed_master_security_group:
        description: The indentifier of EC2 security group for the master node.
        type: str
        sample: sg-a9cd833a
      emr_managed_slave_security_group:
        description: The indentifier of EC2 security group for the core and task nodes.
        type: str
        sample: sg-a9cd833a
      service_access_security_group:
        description: The identifier of EC2 security group for the EMR service.
        type: str
        sample: sg-dab1ffab
      additional_master_security_groups:
        description: A list of additional EC2 security group for the master node.
        type: list
        sample:
          - "sg-a9cd990a"
          - "sg-dab1ffab"
      additional_slave_security_groups:
        description: A list of additional EC2 security group for the core and task node.
        type: list
        sample:
          - "sg-a9cd990a"
          - "sg-dab1ffab"
id:
  description: The unique id for the cluster.
  type: str
  sample: j-3130XEPLZZOH4
instance_collection_type:
  description: Then instance group configuration.
  type: str
  sample: INSTANCE_GROUP
log_uri:
  description: The path to S3 location where logs are stored.
  type: str
  sample: s3://path/to/s3/logs
master_public_dns_name:
  description: The DNS record point to master node.
  type: str
  sample: ip-172-16-0-81.ec2.internal
name:
  description: Friendly name to the cluster.
  type: str
  sample: emr-job
normalized_instance_hours:
  description: An approximation of the cost of the cluster, represented in m1.small/hours.
  type: int
  sample: 12
release_label:
  description: The EMR release label, which determines the version of applications.
  type: str
  sample: emr-5.15.0
scale_down_behavior:
  description: The way that individual EC2 instance terminate when automatic scale-in.
  type: str
  sample: TERMINATE_AT_TASK_COMPLETION
service_role:
  description: The IAM role that will be assumed by EMR Service.
  type: str
  sample: EMR_DefaultRole
status:
  description: The current status of the cluster.
  type: str
  sample: RUNNING
tags:
  description: EC2 tags used by cluster when was launched.
  type: complex
  contains:
    key:
      description: The name of key.
      type: str
    value:
      description: The value of the key.
      type: str
  sample:
    - key: Name
      value: emr-cluster
termination_protected:
  description: Specifies if termination protection is enable.
  type: bool
visible_to_all_users:
  description: Specified if the cluster will be visible for all users.
  type: bool
'''

import re
from ansible.module_utils.ec2 import (
    camel_dict_to_snake_dict,
    snake_dict_to_camel_dict,
    ansible_dict_to_boto3_tag_list
)

from ansible.module_utils.aws.core import AnsibleAWSModule

try:
    from botocore.exceptions import BotoCoreError, ClientError, WaiterError
except ImportError:
    pass  # handled by AnsibleAWSModule


def remove_none_object(obj):
    if isinstance(obj, (list, tuple, set)):
        return type(obj)(remove_none_object(x) for x in obj if x is not None)
    elif isinstance(obj, dict):
        return type(obj)((remove_none_object(k), remove_none_object(v))
                         for k, v in obj.items() if k is not None and v is not None)
    else:
        return obj


def check_emr_cluster(client, module):
    name = module.params.get('name')

    try:
        emr_clusters = client.list_clusters(ClusterStates=['STARTING',
                                                           'BOOTSTRAPPING',
                                                           'RUNNING',
                                                           'WAITING'])
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e)

    response = [emr for emr in emr_clusters['Clusters']
                if re.compile(name).match(emr['Name'])]

    if response:
        changed = False

        if len(response) > 1:
            module.warn(
                warning='More than one Cluster match with name {0} just only the first will be describe'.format(emr['Name']))

        try:
            resource = client.describe_cluster(
                ClusterId=response[0]['Id'])['Cluster']
        except (ClientError, BotoCoreError) as e:
            module.fail_json_aws(e)

        return changed, camel_dict_to_snake_dict(resource)
    else:
        return create_emr_cluster(client, module)


def terminate_emr_cluster(client, module):
    cluster_id = module.params.get('cluster_id')
    wait = module.params.get('wait')

    try:
        resource = client.describe_cluster(ClusterId=cluster_id)['Cluster']

        if resource['Status']['State'] == 'TERMINATED':
            changed = False
            # Remove sensitive information
            if 'KerberosAttributes' in resource:
                del resource['KerberosAttributes']
            return changed, camel_dict_to_snake_dict(resource)

        client.terminate_job_flows(JobFlowIds=[cluster_id])
        resource = client.describe_cluster(ClusterId=cluster_id)['Cluster']
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e)

    if wait:
        waiter = client.get_waiter('cluster_terminated')
        wait_delay = module.params.get('wait_delay')
        wait_max_attempts = module.params.get('wait_max_attempts')

        try:
            waiter.wait(ClusterId=cluster_id, WaiterConfig={
                        'Delay': wait_delay, 'MaxAttempts': wait_max_attempts})
            resource = client.describe_cluster(
                ClusterId=cluster_id)['Cluster']
        except (ClientError, BotoCoreError, WaiterError) as e:
            module.fail_json_aws(e)

    changed = True
    # Remove sensitive information
    if 'KerberosAttributes' in resource:
        del resource['KerberosAttributes']
    return changed, camel_dict_to_snake_dict(resource)


def create_emr_cluster(client, module):
    wait = module.params.get('wait')

    params = remove_none_object(module.params)

    for param in params.keys():
        if param not in emr_argument_spec():
            del params[param]

    if 'tags' in module.params and module.params.get('tags'):
        params['tags'] = ansible_dict_to_boto3_tag_list(
            module.params.get('tags'))

    params = snake_dict_to_camel_dict(params, capitalize_first=True)

    if 'configurations' in module.params and module.params.get('configurations'):
        configurations = module.params.get('configurations')
        params['Configurations'] = []

        for key in configurations.keys():
            properties = {}
            for k, v in configurations[key].iteritems():
                if isinstance(v, bool):
                    properties[k] = str(v).lower()
                else:
                    properties[k] = str(v)

            params['Configurations'].append(
                {'Classification': key, 'Properties': properties})

    if 'ebs_volumes' in module.params and module.params.get('ebs_volumes'):
        volumes = remove_none_object(module.params.get('ebs_volumes'))

        device_configs = {'EbsBlockDeviceConfigs': []}

        for v in volumes:
            spec = {'VolumeSpecification': {}, 'VolumesPerInstance': 1}

            if 'iops' in v:
                spec['VolumeSpecification']['Iops'] = v['iops']

            if 'device' in v:
                spec['Device'] = v['device']

            if 'volumes_per_instance' in v:
                spec['VolumesPerInstance'] = v['volumes_per_instance']

            spec['VolumeSpecification']['SizeInGB'] = v['size']
            spec['VolumeSpecification']['VolumeType'] = v['type']

            device_configs['EbsBlockDeviceConfigs'].append(spec)

        if 'InstanceGroups' in params['Instances']:
            for i in params['Instances']['InstanceGroups']:
                i['EbsConfiguration'] = device_configs

            if 'ebs_optimized' in module.params and module.params.get('ebs_volumes'):
                i['EbsConfiguration']['EbsOptimized'] = module.params.get(
                    'ebs_optimized')

        elif 'InstanceFleets' in params['Instances']:
            for i in params['Instances']['InstanceFleets']:
                for t in i['InstanceTypeConfigs']:
                    t['EbsConfiguration'] = device_configs

                    if 'ebs_optimized' in module.params and module.params.get('ebs_optimized'):
                        t['EbsConfiguration']['EbsOptimized'] = module.params.get(
                            'ebs_optimized')

    try:
        job_flow_id = client.run_job_flow(**params)['JobFlowId']
        resource = client.describe_cluster(ClusterId=job_flow_id)['Cluster']
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e)

    if wait:
        waiter = client.get_waiter('cluster_running')
        wait_delay = module.params.get('wait_delay')
        wait_max_attempts = module.params.get('wait_max_attempts')

        try:
            waiter.wait(ClusterId=job_flow_id, WaiterConfig={
                        'Delay': wait_delay, 'MaxAttempts': wait_max_attempts})
            resource = client.describe_cluster(
                ClusterId=job_flow_id)['Cluster']
        except (ClientError, BotoCoreError, WaiterError) as e:
            module.fail_json_aws(e)

    changed = True
    # Remove sensitive information
    if 'KerberosAttributes' in resource:
        del resource['KerberosAttributes']
    return changed, camel_dict_to_snake_dict(resource)


def emr_argument_spec():
    spec = dict(
        dict(
            name=dict(type='str'),
            log_uri=dict(type='str'),
            additional_info=dict(type='str'),
            ami_version=dict(type='str'),
            release_label=dict(type='str'),
            instances=dict(
                type='dict',
                options=dict(
                    master_instance_type=dict(type='str'),
                    slave_instance_type=dict(type='str'),
                    instance_count=dict(type='int'),
                    instance_groups=dict(
                        type='list',
                        elements='dict',
                        options=dict(
                            name=dict(type='str'),
                            market=dict(type='str', choices=['ON_DEMAND', 'SPOT']),
                            instance_role=dict(type='str', choices=['MASTER', 'CORE', 'TASK'], required=True),
                            instance_type=dict(type='str', required=True),
                            instance_count=dict(type='int', required=True),
                            auto_scaling_policy=dict(type='dict')
                        )
                    ),
                    instance_fleets=dict(
                        type='list',
                        elements='dict',
                        options=dict(
                            name=dict(type='str'),
                            instance_fleet_type=dict(type='str', choices=['MASTER', 'CORE', 'TASK'], required=True),
                            target_on_demand_capacity=dict(type='int'),
                            target_spot_capacity=dict(type='int'),
                            instance_type_configs=dict(
                                type='list',
                                elements='dict',
                                options=dict(
                                    instance_type=dict(type='str', required=True),
                                    weighted_capacity=dict(type='int'),
                                    bid_price=dict(type='str'),
                                    bid_price_as_percentage_of_on_demand_price=dict(type='float'),
                                    launch_specifications=dict(type='dict')
                                )
                            ),
                            launch_specifications=dict(type='dict')
                        )
                    ),
                    ec2_key_name=dict(type='str'),
                    placement=dict(type='dict'),
                    keep_job_flow_alive_when_no_steps=dict(type='bool', default=False),
                    termination_protected=dict(type='bool', default=False),
                    hadoop_version=dict(type='str'),
                    ec2_subnet_id=dict(type='str'),
                    ec2_subnets_ids=dict(type='list', elements='str'),
                    emr_managed_master_security_group=dict(type='str'),
                    emr_managed_slave_security_group=dict(type='str'),
                    additional_master_security_groups=dict(type='list', elements='str'),
                    additional_slave_security_groups=dict(type='list', elements='str')
                )
            ),
            steps=dict(
                type='list',
                elements='dict',
                options=dict(
                    name=dict(type='str'),
                    action_on_failure=dict(
                        type='str',
                        choices=[
                            'TERMINATE_JOB_FLOW',
                            'TERMINATE_CLUSTER',
                            'CANCEL_AND_WAIT',
                            'CONTINUE'
                        ],
                        default='TERMINATE_CLUSTER'
                    ),
                    hadoop_jar_step=dict(type='dict')
                )
            ),
            bootstrap_actions=dict(type='list', elements='dict'),
            supported_products=dict(type='list', elements='str'),
            new_supported_products=dict(type='list', elements='dict'),
            applications=dict(type='list', elements='dict'),
            visible_to_all_users=dict(type='bool', default=True),
            job_flow_role=dict(type='str', default='EMR_EC2_DefaultRole'),
            service_role=dict(type='str', default='EMR_DefaultRole'),
            security_configuration=dict(type='str'),
            auto_scaling_role=dict(type='str'),
            scale_down_behavior=dict(typ='str', choices=['TERMINATE_AT_INSTANCE_HOUR', 'TERMINATE_AT_TASK_COMPLETION']),
            custom_ami_id=dict(type='str'),
            ebs_root_volume_size=dict(type='int'),
            repo_upgrade_on_boot=dict(type='str', choices=['SECURITY', 'NONE']),
            kerberos_attributes=dict(type='dict', no_log=True)
        )
    )

    return spec


def main():
    argument_spec = emr_argument_spec()
    argument_spec.update(
        dict(
            state=dict(type='str', choices=['present', 'absent'], default='present'),
            configurations=dict(type='dict'),
            ebs_volumes=dict(
                type='list',
                elements='dict',
                options=dict(
                    type=dict(type='str', choices=['gp2', 'io1', 'standard'], default='gp2'),
                    iops=dict(type='int'),
                    size=dict(type='int'),
                    device=dict(type='str'),
                    volumes_per_instance=dict(type='int')
                )
            ),
            ebs_optimized=dict(type='bool', default=False),
            cluster_id=dict(type='str'),
            tags=dict(type='dict'),
            wait=dict(type='bool', default=False),
            wait_delay=dict(type='int', default=30),
            wait_max_attempts=dict(type='int', default=60)
        )
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              required_if=[
                                  ['state', 'present', ['name', 'instances', 'release_label']],
                                  ['state', 'absent', ['cluster_id']]
                              ],
                              supports_check_mode=True)

    case = {
        'present': check_emr_cluster,
        'absent': terminate_emr_cluster
    }

    state = module.params.get('state')
    client = module.client('emr')

    changed, response = case.get(state)(client, module)

    module.exit_json(changed=changed, **response)


if __name__ == '__main__':
    main()
