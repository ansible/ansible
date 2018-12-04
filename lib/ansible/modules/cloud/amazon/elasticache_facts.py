#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: elasticache_facts
short_description: Retrieve facts for AWS Elasticache clusters
description:
  - Retrieve facts from AWS Elasticache clusters
version_added: "2.5"
options:
  name:
    description:
      - The name of an Elasticache cluster

author:
  - Will Thames (@willthames)
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
- name: obtain all Elasticache facts
  elasticache_facts:

- name: obtain all facts for a single Elasticache cluster
  elasticache_facts:
    name: test_elasticache
'''

RETURN = '''
elasticache_clusters:
  description: List of elasticache clusters
  returned: always
  type: complex
  contains:
    auto_minor_version_upgrade:
      description: Whether to automatically upgrade to minor versions
      returned: always
      type: bool
      sample: true
    cache_cluster_create_time:
      description: Date and time cluster was created
      returned: always
      type: string
      sample: '2017-09-15T05:43:46.038000+00:00'
    cache_cluster_id:
      description: ID of the cache cluster
      returned: always
      type: string
      sample: abcd-1234-001
    cache_cluster_status:
      description: Status of Elasticache cluster
      returned: always
      type: string
      sample: available
    cache_node_type:
      description: Instance type of Elasticache nodes
      returned: always
      type: string
      sample: cache.t2.micro
    cache_nodes:
      description: List of Elasticache nodes in the cluster
      returned: always
      type: complex
      contains:
        cache_node_create_time:
          description: Date and time node was created
          returned: always
          type: string
          sample: '2017-09-15T05:43:46.038000+00:00'
        cache_node_id:
          description: ID of the cache node
          returned: always
          type: string
          sample: '0001'
        cache_node_status:
          description: Status of the cache node
          returned: always
          type: string
          sample: available
        customer_availability_zone:
          description: Availability Zone in which the cache node was created
          returned: always
          type: string
          sample: ap-southeast-2b
        endpoint:
          description: Connection details for the cache node
          returned: always
          type: complex
          contains:
            address:
              description: URL of the cache node endpoint
              returned: always
              type: string
              sample: abcd-1234-001.bgiz2p.0001.apse2.cache.amazonaws.com
            port:
              description: Port of the cache node endpoint
              returned: always
              type: int
              sample: 6379
        parameter_grou_status:
          description: Status of the Cache Parameter Group
          returned: always
          type: string
          sample: in-sync
    cache_parameter_group:
      description: Contents of the Cache Parameter GGroup
      returned: always
      type: complex
      contains:
        cache_node_ids_to_reboot:
          description: Cache nodes which need to be rebooted for parameter changes to be applied
          returned: always
          type: list
          sample: []
        cache_parameter_group_name:
          description: Name of the cache parameter group
          returned: always
          type: string
          sample: default.redis3.2
        parameter_apply_status:
          description: Status of parameter updates
          returned: always
          type: string
          sample: in-sync
    cache_security_groups:
      description: Security Groups used by the cache
      returned: always
      type: list
      sample:
        - 'sg-abcd1234'
    cache_subnet_group_name:
      description: Elasticache Subnet Group used by the cache
      returned: always
      type: string
      sample: abcd-subnet-group
    client_download_landing_page:
      description: URL of client download web page
      returned: always
      type: string
      sample: 'https://console.aws.amazon.com/elasticache/home#client-download:'
    engine:
      description: Engine used by elasticache
      returned: always
      type: string
      sample: redis
    engine_version:
      description: Version of elasticache engine
      returned: always
      type: string
      sample: 3.2.4
    notification_configuration:
      description: Configuration of notifications
      returned: if notifications are enabled
      type: complex
      contains:
        topic_arn:
          description: ARN of notification destination topic
          returned: if notifications are enabled
          type: string
          sample: arn:aws:sns:*:123456789012:my_topic
        topic_name:
          description: Name of notification destination topic
          returned: if notifications are enabled
          type: string
          sample: MyTopic
    num_cache_nodes:
      description: Number of Cache Nodes
      returned: always
      type: int
      sample: 1
    pending_modified_values:
      description: Values that are pending modification
      returned: always
      type: complex
      contains: {}
    preferred_availability_zone:
      description: Preferred Availability Zone
      returned: always
      type: string
      sample: ap-southeast-2b
    preferred_maintenance_window:
      description: Time slot for preferred maintenance window
      returned: always
      type: string
      sample: sat:12:00-sat:13:00
    replication_group_id:
      description: Replication Group Id
      returned: always
      type: string
      sample: replication-001
    security_groups:
      description: List of Security Groups associated with Elasticache
      returned: always
      type: complex
      contains:
        security_group_id:
          description: Security Group ID
          returned: always
          type: string
          sample: sg-abcd1234
        status:
          description: Status of Security Group
          returned: always
          type: string
          sample: active
    tags:
      description: Tags applied to the elasticache cluster
      returned: always
      type: complex
      sample:
        Application: web
        Environment: test
'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, ec2_argument_spec, get_aws_connection_info
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, AWSRetry
from ansible.module_utils.ec2 import boto3_tag_list_to_ansible_dict


try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule


@AWSRetry.exponential_backoff()
def describe_cache_clusters_with_backoff(client, cluster_id=None):
    paginator = client.get_paginator('describe_cache_clusters')
    params = dict(ShowCacheNodeInfo=True)
    if cluster_id:
        params['CacheClusterId'] = cluster_id
    try:
        response = paginator.paginate(**params).build_full_result()
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'CacheClusterNotFound':
            return []
        raise
    except botocore.exceptions.BotoCoreError:
        raise
    return response['CacheClusters']


@AWSRetry.exponential_backoff()
def get_elasticache_tags_with_backoff(client, cluster_id):
    return client.list_tags_for_resource(ResourceName=cluster_id)['TagList']


def get_aws_account_id(module):
    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        client = boto3_conn(module, conn_type='client', resource='sts',
                            region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Can't authorize connection")

    try:
        return client.get_caller_identity()['Account']
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't obtain AWS account id")


def get_elasticache_clusters(client, module, region):
    try:
        clusters = describe_cache_clusters_with_backoff(client, cluster_id=module.params.get('name'))
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't obtain cache cluster info")

    account_id = get_aws_account_id(module)
    results = []
    for cluster in clusters:

        cluster = camel_dict_to_snake_dict(cluster)
        arn = "arn:aws:elasticache:%s:%s:cluster:%s" % (region, account_id, cluster['cache_cluster_id'])
        try:
            tags = get_elasticache_tags_with_backoff(client, arn)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't get tags for cluster %s")

        cluster['tags'] = boto3_tag_list_to_ansible_dict(tags)
        results.append(cluster)
    return results


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=False),
        )
    )
    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    client = boto3_conn(module, conn_type='client', resource='elasticache',
                        region=region, endpoint=ec2_url, **aws_connect_kwargs)

    module.exit_json(elasticache_clusters=get_elasticache_clusters(client, module, region))


if __name__ == '__main__':
    main()
