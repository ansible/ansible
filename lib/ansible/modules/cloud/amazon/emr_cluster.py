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
  - because the name is not a unique field in AWS this module can't ensure the state
    from a cluster, so if you runs this module 10 times, 10 cluster will be created
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
      - list of specific configuratins that will be pass for applications and Amazon EMR
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
  state:
    description:
      - ensure cluster is create or terminate
      - default create
  wait:
    description:
      - wait until EMR is RUNNING
      - default false
  wait_timeout:
    description:
      - how log before wait gives up, in seconds
      - default 600
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
  tags:
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
    applications:
      - name: Hadoop
      - name: Spark
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
      configurations:
        - classification: spark
          properties:
            maximizeResourceAllication: true
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
    tags:
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

try:
    from botocore.exception import ClientError
except ImportError:
    pass  # will be picked up from imported HAS_BOTO3

import re
import traceback
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, boto3_conn, get_aws_connection_info
from ansible.module_utils.ec2 import HAS_BOTO3, camel_dict_to_snake_dict, snake_dict_to_camel_dict, ansible_dict_to_boto3_tag_list


def terminate_emr_cluster(client, module):
    cluster_id = module.params.get('cluster_id')
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')

    if not cluster_id:
        module.fail_json(msg='cluster_id required for state absent')

    client.terminate_job_flows(JobFlowIds=[cluster_id])

    resource = client.describe_cluster(ClusterId=cluster_id)['Cluster']

    if wait:
        wait_timeout = time.time() + wait_timeout
        time.sleep(5)

        while wait_timeout > time.time() and resource['Status']['State'] != 'TERMINATED':
            time.sleep(5)

            if wait_timeout <= time.time():
                module.exit_json(msg="Timeout waiting for resource %s" % resource['Id'])

            resource = client.describe_cluster(ClusterId=cluster_id)['Cluster']

    return camel_dict_to_snake_dict(resource)


def create_emr_cluster(client, module):
    params = {}
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')

    for p in ['name', 'instances', 'log_uri', 'additional_info', 'ami_version', 'release_label',
              'steps', 'bootstrap_actions', 'supported_products', 'new_supported_products',
              'applications', 'configurations', 'visible_to_all_users', 'service_role', 'job_flow_role',
              'security_configuration', 'auto_scaling_role', 'scale_down_behavior', 'custom_ami_id',
              'repo_upgrade_on_boot', 'ebs_root_volume_size', 'cluster_id', 'kerberos_attributes']:

        if p in module.params and module.params.get(p):
            params[p] = module.params.get(p)

    if 'tags' in module.params and module.params.get('tags'):
        params['tags'] = ansible_dict_to_boto3_tag_list(module.params.get('tags'))

    if not params['name']:
        module.fail_json(msg="name required for the state create")

    params = snake_dict_to_camel_dict(params, capitalize_first=True)

    job_flow_id = client.run_job_flow(**params)['JobFlowId']

    resource = client.describe_cluster(ClusterId=job_flow_id)['Cluster']

    if wait:
        wait_timeout = time.time() + wait_timeout
        time.sleep(5)

        while wait_timeout > time.time() and resource['Status']['State'] != 'RUNNING':
            time.sleep(5)

            if wait_timeout <= time.time():
                module.exit_json(msg="Timeout waiting for resource %s" % resource['Id'])

            resource = client.describe_cluster(ClusterId=job_flow_id)['Cluster']

    return camel_dict_to_snake_dict(resource)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
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
            configurations=dict(required=False, type='list'),
            visible_to_all_users=dict(required=False, type='bool', default=True),
            service_role=dict(required=False, default='EMR_DefaultRole'),
            job_flow_role=dict(required=False, default='EMR_EC2_DefaultRole'),
            security_configuration=dict(required=False),
            auto_scaling_role=dict(required=False),
            scale_down_behavior=dict(required=False, choices=['instance_hour', 'task_completion']),
            custom_ami_id=dict(required=False),
            repo_upgrade_on_boot=dict(required=False),
            ebs_root_volume_size=dict(required=False, type='int'),
            state=dict(required=False, choices=['create', 'absent'], default='create'),
            wait=dict(required=False, type='bool', default=False),
            cluster_id=dict(required=False),
            tags=dict(required=False, type='dict'),
            kerberos_attributes=dict(required=False, type='dict'),
            wait_timeout=dict(required=False, type='int', default=600)
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    state = module.params.get('state')

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        client = boto3_conn(module, conn_type='client', resource='emr', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    if state == 'create':
        cluster = create_emr_cluster(client, module)
    elif state == 'absent':
        cluster = terminate_emr_cluster(client, module)

    module.exit_json(changed=True, cluster=cluster)

if __name__ == '__main__':
    main()
