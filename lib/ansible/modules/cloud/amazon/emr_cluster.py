#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: emr_cluster
short_description:  Creating or Terminating EMR Clusters
version_added: "2.6"
description:
  - creating or terminating EMR Clusters
  - steps (jobs spark for example) can be setup when Cluster is creating
  - this module will check EMR name when state is present to check if cluster already exist
    but EMR API don't have a unique field to ensure that behavior
  - basically this module only receive args and send to boto3, so any argument supported
    by method run_job_flow() can be used when state is create.
    check http://boto3.readthedocs.io/en/latest/reference/services/emr.html#EMR.Client.run_job_flow
    for more information
  - it depends on boto3
options:
  region:
    description:
      - region where the module creating or terminating EMR Cluster
  name:
    description:
      - name to be used when EMR is creating
  instances:
    description:
      - specifications about EC2 instances
  log_uri:
    description:
      - s3 path to store logs from EMR
  release_label:
    description:
      - release label for the Amazon EMR
      - default emr-5.11.0
  steps:
    description:
      - list of steps will be run
  bootstrap_actions:
    description:
      - list of action to run before Hadoop Starts
  applications:
    description:
      - list of Applications that will be enabled on EMR
  configurations:
    description:
      - dict of specific configuratins that will be pass for applications and Amazon EMR
  service_role:
    description:
      - IAM role that will be assumed by the Amazon EMR
      - default EMR_DefaultRole
  job_flow_role:
    description:
      - IAM role that will be assumed by the Amazon EC2
      - default EMR_EC2_DefaultRole
  ebs_root_volume_size:
    description:
      - settings for EBS on root
  ebs_optimized:
    description:
      - define if ebs is optimized
  ebs_volumes:
    description:
      - list to create extra volumes see section EbsBlockDeviceConfigs in
        http://boto3.readthedocs.io/en/latest/reference/services/emr.html#EMR.Client.run_job_flow
  state:
    description:
      - ensure cluster is create or terminate
      - default present
  wait:
    description:
      - wait until EMR is RUNNING if state is create or present and TERMINATED if state is absent
      - default false
  wait_delay:
    description:
      - the amount of time in seconds to wait between attempts
      - default 30
  wait_max_attempts:
    description:
      - the number of attempts for cluster become to correct state
      - default 60
  cluster_id:
    description:
      - id from EMR that will be terminate
      - this arg just only used by state terminate
  additional_info:
    description:
      - a json string for selecting additiona features
  ami_version:
    description:
      - Amazon EMR AMI versions for 3.x and 2.x, EMR releases 4.0 and later this is defined by release_label
  auto_scaling_role:
    description:
      - IAM Role for scaling policies, default is EMR_AutoScaling_DefaultRole
  custom_ami_id:
    description:
      - available only in Amazon EMR 5.7.0 and later
  kerberos_attributes:
    description:
      - attributes for Kerberos configuration. For more information see
        https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-kerberos.html
  new_supported_products:
    description:
      - a list with third-party software to use, see boto3 documentation for more information.
  repo_upgrade_on_boot:
    description:
      - applies when custom_ami_id is used, specified the types of udpates that are applied from the Amazon Linux
  scale_down_behavior:
    description:
      - basically define if scale in occours based in INSTANCE_HOURS or TASK_COMPLETION
  security_configuration:
    description:
      - name of security configuration
  supported_products:
    description:
      - a list set by third-party when job is launched.
  ec2_tags:
    description:
      - a dict with tags that will be associate with a cluster
  visible_to_all_users:
    description:
      - define if cluster will be visible to all IAM users, default is True
author:
  - Wellington Moreira Ramos (@wmaramos)
extends_documentation_fragment:
  - aws
  - ec2
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
    configurations:
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
            - "--dest=hdfs://aggregate"
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
# For more information see http://boto3.readthedocs.io/en/latest/reference/services/emr.html#EMR.Client.describe_cluster
---
cluster:
  description: dictionary containing informations about EMR Cluster
  returned: success
  type: complex
  contains:
    id:
      description: the unique id for the cluster
      type: str
      sample: j-2JNVMF38MZVHT
    name:
      description: the name of the cluster
      type: str
      sample: emr-jobs
    status:
      description: the current status defailts about the cluster
      type: dict
    ec2_instaces_attributes:
      description: provides information about ec2
      type: dict
    log_uri:
      description: path for logs location in S3
      type: str
    release_label:
      description: the release label for the Amazon EMR
      type: str
    auto_terminate:
      description: if true cluster should terminate after completing all step
      type: boolean
    applications:
      description: list of the applications installed on this cluster
      type: list
    ec2_tags:
      description: list of tags
      type: dict
    service_role:
      description: IAM role that will be assumed by the Amazon AEMR service
      type: str
    master_public_dns_name:
      description: the dns name of the master node
      type: str
    configurations:
      description: the list of configurations supplied to EMR cluster
      type: dict
'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (
    camel_dict_to_snake_dict,
    snake_dict_to_camel_dict,
    ansible_dict_to_boto3_tag_list
)

import re

try:
    from botocore.exceptions import BotoCoreError, ClientError, WaiterError
except ImportError:
    pass  # handled by AnsibleAWSModule


class ElasticMapReduceError(Exception):
    def __init__(self, msg, exception=None):
        self.msg = msg
        self.exception = exception


def check_emr_cluster(client, module):
    name = module.params.get('name')

    if not name:
        module.fail_json(msg='name is required')

    try:
        emr_clusters = client.list_clusters(ClusterStates=['STARTING',
                                                           'BOOTSTRAPPING',
                                                           'RUNNING',
                                                           'WAITING'])
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e)

    response = [emr for emr in emr_clusters['Clusters'] if re.compile(name).match(emr['Name'])]

    if response:
        changed = False

        if len(response) > 1:
            module.warn(warning='More than one Cluster match with name {} just only the first will be describe'.format(emr['Name']))

        try:
            resource = client.describe_cluster(ClusterId=response[0]['Id'])
        except (ClientError, BotoCoreError) as e:
            module.fail_json_aws(e)

        return changed, camel_dict_to_snake_dict(resource)

    else:
        return create_emr_cluster(client, module)


def terminate_emr_cluster(client, module):
    cluster_id = module.params.get('cluster_id')
    wait = module.params.get('wait')

    if not cluster_id:
        module.fail_json(msg='cluster_id required for state absent')

    try:
        client.terminate_job_flows(JobFlowIds=[cluster_id])
        resource = client.describe_cluster(ClusterId=cluster_id)['Cluster']
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e)

    if wait:
        waiter = client.get_waiter('cluster_terminated')
        wait_delay = module.params.get('wait_delay')
        wait_max_attempts = module.params.get('wait_max_attempts')

        try:
            waiter.wait(ClusterId=job_flow_id, WaiterConfig={'Delay': wait_delay, 'MaxAttempts': wait_max_attempts})
            resource = client.describe_cluster(ClusterId=job_flow_id)['Cluster']
        except (ClientError, BotoCoreError, WaiterError) as e:
            module.fail_json_aws(e)

    changed = True
    return changed, camel_dict_to_snake_dict(resource)


def create_emr_cluster(client, module):
    params = {}
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')

    for p in ['name', 'instances', 'log_uri', 'additional_info', 'ami_version', 'release_label',
              'steps', 'bootstrap_actions', 'supported_products', 'new_supported_products',
              'applications', 'visible_to_all_users', 'service_role', 'job_flow_role',
              'security_configuration', 'auto_scaling_role', 'scale_down_behavior', 'custom_ami_id',
              'repo_upgrade_on_boot', 'ebs_root_volume_size', 'cluster_id', 'kerberos_attributes']:

        if p in module.params and module.params.get(p):
            params[p] = module.params.get(p)

    if 'ec2_tags' in module.params and module.params.get('ec2_tags'):
        params['tags'] = ansible_dict_to_boto3_tag_list(module.params.get('ec2_tags'))

    if not params['name']:
        module.fail_json(msg="name required for the state create")

    params = snake_dict_to_camel_dict(params, capitalize_first=True)

    if 'configurations' in module.params and module.params.get('configurations'):
        c = module.params.get('configurations')
        params['Configurations'] = []

        for k in c.keys():
            params['Configurations'].append({'Classification': k, 'Properties': c[k]})

    if 'ebs_volumes' in module.params and module.params.get('ebs_volumes'):
        volumes = module.params.get('ebs_volumes')

        device_configs = {'EbsBlockDeviceConfigs': []}

        for v in volumes:
            spec = {'VolumeSpecification': {}, 'VolumesPerInstance': 1}

            if 'iops' in v:
                spec['VolumeSpecification']['Iops'] = v['iops']

            spec['VolumeSpecification']['SizeInGB'] = v['size']
            spec['VolumeSpecification']['VolumeType'] = v['type']

            device_configs['EbsBlockDeviceConfigs'].append(spec)

        if 'InstanceGroups' in params['Instances']:
            for i in params['Instances']['InstanceGroups']:
                i['EbsConfiguration'] = device_configs

            if 'ebs_optimized' in module.params and module.params.get('ebs_volumes'):
                i['EbsConfiguration']['EbsOptimized'] = module.params.get('ebs_optimized')

        elif 'InstanceFleets' in params['Instances']:
            for i in params['Instances']['InstanceFleets']:
                for t in i['InstanceTypeConfigs']:
                    t['EbsConfiguration'] = device_configs

                    if 'ebs_optimized' in module.params and module.params.get('ebs_optimized'):
                        t['EbsConfiguration']['EbsOptimized'] = module.params.get('ebs_optimized')

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
            waiter.wait(ClusterId=job_flow_id, WaiterConfig={'Delay': wait_delay, 'MaxAttempts': wait_max_attempts})
            resource = client.describe_cluster(ClusterId=job_flow_id)['Cluster']
        except (ClientError, BotoCoreError, WaiterError) as e:
            module.fail_json_aws(e)

    changed = True
    return changed, camel_dict_to_snake_dict(resource)


def main():
    argument_spec = dict(
        dict(
            name=dict(required=False),
            instances=dict(required=False, type='dict'),
            log_uri=dict(required=False),
            additional_info=dict(required=False),
            ami_version=dict(required=False),
            release_label=dict(required=False, default='emr-5.11.0'),
            steps=dict(required=False, type='list'),
            bootstrap_actions=dict(required=False, type='list'),
            supported_products=dict(required=False, type='list'),
            new_supported_products=dict(required=False, type='list'),
            applications=dict(required=False, type='list'),
            configurations=dict(required=False, type='dict'),
            visible_to_all_users=dict(required=False, type='bool', default=True),
            service_role=dict(required=False, default='EMR_DefaultRole'),
            job_flow_role=dict(required=False, default='EMR_EC2_DefaultRole'),
            security_configuration=dict(required=False),
            auto_scaling_role=dict(required=False),
            scale_down_behavior=dict(required=False, choices=['instance_hour', 'task_completion']),
            custom_ami_id=dict(required=False),
            repo_upgrade_on_boot=dict(required=False),
            ebs_root_volume_size=dict(required=False, type='int'),
            state=dict(required=False, choices=['present', 'create', 'absent'], default='present'),
            cluster_id=dict(required=False),
            ec2_tags=dict(required=False, type='dict'),
            kerberos_attributes=dict(required=False, type='dict'),
            ebs_volumes=dict(required=False, type='list'),
            ebs_optimized=dict(required=False, type='bool'),
            wait=dict(required=False, type='bool', default=False),
            wait_delay=dict(required=False, type='int', default=30),
            wait_max_attempts=dict(required=False, type='int', default=60)
        )
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              supports_check_mode=True)

    case = {
        'present': check_emr_cluster,
        'absent': terminate_emr_cluster,
        'create': create_emr_cluster
    }

    state = module.params.get('state')
    try:
        client = module.client('emr')
        changed, response = case.get(state)(client, module)
    except ElasticMapReduceError as e:
        module.fail_json(e.exception, msg=e.msg)

    module.exit_json(changed=changed, **response)

if __name__ == '__main__':
    main()
