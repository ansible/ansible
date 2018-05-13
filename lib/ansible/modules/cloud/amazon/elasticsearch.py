#!/usr/bin/python
#
# Copyright (c) 2017 Ansible Project
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: elasticsearch
short_description: Manage hosted Elasticsearch in Amazon Web Services.
description:
  - Manage hosted Elasticsearch in Amazon Web Services.
  - Returns information about the hosted Elasticsearch.
version_added: "2.6"
requirements: [ boto3 ]
author: "Zach Steindler (@steiza)"
options:
  domain:
    description:
      - Domain name for cluster.
    required: true
  state:
    description:
      - Create or destroy cluster
    choices: [ "present", "absent" ]
    required: true
  version:
    description:
      - Version of Elasticsearch to use.
    required: false
    default: 5.1
  instance_count:
    description:
      - Number of non-master nodes in the cluster.
    required: false
    default: 1
  instance_type:
    description:
      - Instance type of non-master nodes in the cluster.
    required: true
  zone_awareness:
    description:
      - Should cluster be aware of AWS availability zones.
    type: bool
    required: false
    default: true
  dedicated_master_enabled:
    description:
      - If cluster have dedicated master nodes.
    type: bool
    required: false
    default: false
  dedicated_master_type:
    description:
      - Instance type of dedicated master nodes. Ignored if dedicated_master_enabled is False.
    required: false
  dedicated_master_count:
    description:
      - Number of dedicated master nodes. Ignored if dedicated_master_enabled is False.
    required: false
  ebs_volume_type:
    description:
      - What type of EBS volume should nodes have.
    choices: [ "standard", "gp2", "io1" ]
    required: false
    default: gp2
  ebs_volume_size:
    description:
      - What size EBS volume each node should have.
    required: true
  access_policies:
    description:
      - JSON string describing the access policy of the cluster.
    required: true
  wait:
    description:
      - Wait for cluster creation to finish
    type: bool
  tags:
    description:
      - Dictionary of tags to ensure are present on resource. Will not remove other tags.
    required: false

extends_documentation_fragment:
    - aws
    - ec2
"""

EXAMPLES = """
# Note: None of these examples set aws_access_key, aws_secret_key, or region.
# It is assumed that their matching environment variables are set.

# Basic example
- elasticsearch:
    domain: testing
    state: present
    instance_count: 1
    zone_awareness: false
    instance_type: "t2.medium.elasticsearch"
    ebs_volume_size: 10
    access_policies: '{"Statement": [{"Action": "*", "Principal": {"AWS": "arn:aws:iam::0000000000000:user/you"}, "Effect": "Allow"}]}'
    region: us-west-1
"""

RETURN = """
arn:
    description: ARN of Elasticsearch cluster.
    returned: always
    type: string
    sample: "arn:aws:es:us-west-1:000000000000:domain/testing"
endpoint:
    description: When cluster is finished being created, endpoint to submit requests to.
    returned: always
    type: string
    sample: "search-testing-asdfqwerty.us-west-1.es.amazonaws.com"
processing:
    description: Is the cluster processing config changes.
    returned: always
    type: bool
elasticsearch_version:
    description: Which version of Elasticsearch cluster is running.
    returned: always
    type: string
    sample: "5.1"
instance_type:
    description: Instance type of non-master nodes in the cluster.
    returned: always
    type: string
    sample: "t2.medium.elasticsearch"
instance_count:
    description: Number of non-master nodes in the cluster.
    returned: always
    type: int
dedicated_master_enabled:
    description: Does cluster have dedicated master nodes.
    returned: always
    type: bool
zone_awareness:
    description: Is cluster aware of AWS availability zones.
    returned: always
    type: bool
dedicated_master_type:
    description: Instance type of dedicated master nodes.
    returned: always
    type: string
    sample: "t2.medium.elasticsearch"
dedicated_master_count:
    description: Number of dedicated master nodes.
    returned: always
    type: int
ebs_volume_type:
    description: What EBS volume type nodes have.
    returned: always
    type: string
    sample: "gp2"
ebs_volume_size:
    description: What size EBS volume each node has.
    returned: always
    type: int
access_policies:
    description: JSON string of the access policy of the cluster.
    returned: always
    type: string
    sample: '{"Statement": [{"Action": "*", "Resource": "arn:aws:iam::0000000000000:user/you", "Effect": "Allow"}]}'
"""

from collections import defaultdict
import json
import time
import traceback

from ansible.module_utils._text import to_native
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, compare_policies, ec2_argument_spec, get_aws_connection_info

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # boto3_conn will handle missing dependencies


def _create_elasticsearch_domain(connection, module):
    elasticsearch_cluster_config = {
        'InstanceCount': module.params['instance_count'],
        'InstanceType': module.params['instance_type'],
        'ZoneAwarenessEnabled': module.params['zone_awareness'],
        'DedicatedMasterEnabled': module.params['dedicated_master_enabled'],
    }

    if module.params['dedicated_master_enabled']:
        elasticsearch_cluster_config['DedicatedMasterType'] = module.params['dedicated_master_type']
        elasticsearch_cluster_config['DedicatedMasterCount'] = module.params['dedicated_master_count']

    try:
        connection.create_elasticsearch_domain(
            DomainName=module.params['domain'],
            ElasticsearchVersion=module.params['version'],
            ElasticsearchClusterConfig=elasticsearch_cluster_config,
            EBSOptions={
                'EBSEnabled': True,
                'VolumeType': module.params['ebs_volume_type'],
                'VolumeSize': module.params['ebs_volume_size'],
            },
            AccessPolicies=module.params['access_policies'],
        )

    except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(
                e,
                msg='Unable to create elasticsearch domain: {0}'.format(
                    to_native(e))
            )

    return True


def ensure_present(connection, module):
    elasticserach_domain = is_present(connection, module)
    if elasticserach_domain:
        changed = False
    else:
        changed = True
        _create_elasticsearch_domain(connection, module)
        elasticserach_domain = is_present(connection, module)
    return changed, elasticserach_domain


def is_present(connection, module):
    """Get the current status of Elasticsearch domain"""
    name = module.params['domain']

    try:
        response = connection.describe_elasticsearch_domain(
            DomainName=name
        )

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return None
        else:
            module.fail_json_aws(
                e,
                msg='Unexpected error {0}'.format(to_native(e))
            )

    return response


def ensure_deleted(connection, module):
    try:
        connection.delete_elasticsearch_domain(
            DomainName=module.params['domain']
        )

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return False
        else:
            module.fail_json_aws(
                e,
                msg='Unexpected error {0}'.format(to_native(e))
            )

    return True


def check_existing_config(module, domain):
    modifications_needed = defaultdict(dict)

    existing_config = domain['DomainStatus']
    desired_config = module.params

    config_to_check = [
        (('ElasticsearchVersion',), desired_config['version']),
        (('ElasticsearchClusterConfig', 'InstanceCount'),
            desired_config['instance_count']),
        (('ElasticsearchClusterConfig', 'InstanceType'),
            desired_config['instance_type']),
        (('ElasticsearchClusterConfig', 'ZoneAwarenessEnabled'),
            desired_config['zone_awareness']),
        (('ElasticsearchClusterConfig', 'DedicatedMasterEnabled'),
            desired_config['dedicated_master_enabled']),
        (('EBSOptions', 'VolumeType'), desired_config['ebs_volume_type']),
        (('EBSOptions', 'VolumeSize'), desired_config['ebs_volume_size']),
    ]

    if desired_config['dedicated_master_enabled']:
        config_to_check.extend(
            [
                (('ElasticsearchClusterConfig', 'DedicatedMasterType'),
                    desired_config['dedicated_master_type']),
                (('ElasticsearchClusterConfig', 'DedicatedMasterCount'),
                    desired_config['dedicated_master_count']),
            ]
        )

    for key_path, desired_value in config_to_check:
        # Traverse key path to get existing value
        existing_value = existing_config
        for key in key_path:
            existing_value = existing_value.get(key)

        if existing_value != desired_value:
            # Traverse key path in modifications dictionary to submit to AWS
            modification = modifications_needed
            for key in key_path[:-1]:
                if key not in modification:
                    modification[key] = {}

                modification = modification[key]

            modification[key_path[-1]] = desired_value

    existing_access_json = json.loads(domain['DomainStatus']['AccessPolicies'])
    supplied_access_json = json.loads(module.params['access_policies'])

    if compare_policies(existing_access_json, supplied_access_json):
        modifications_needed['AccessPolicies'] = module.params['access_policies']

    return modifications_needed


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            domain={'required': True},
            state={'required': True, 'choices': ['present', 'absent']},
            version={'default': '5.1'},
            instance_count={'type': 'int', 'default': 1},
            instance_type={'required': True},
            zone_awareness={'type': 'bool', 'default': True},
            dedicated_master_enabled={
                'type': 'bool', 'default': False
            },
            dedicated_master_type={},
            dedicated_master_count={'type': 'int'},
            ebs_volume_type={
                'default': 'gp2', 'choices': ['standard', 'gp2', 'io1']
            },
            ebs_volume_size={'required': True, 'type': 'int'},
            access_policies={'required': True},
            wait={'type': 'bool'},
            tags={'type': 'dict'},
        )
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
    )

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(
        module, boto3=True
    )

    client = boto3_conn(
        module, conn_type='client', resource='es', region=region,
        endpoint=ec2_url, **aws_connect_kwargs
    )

    if module.params['state'] not in ['present', 'absent']:
        module.fail_json(msg='"state" must be "present" or "absent"')

    if module.params['state'] == 'absent':
        changed = ensure_deleted(client, module)
        module.exit_json(changed=changed)

    elif module.params['state'] == 'present':
        changed, domain = ensure_present(client, module)
        modifications_needed = check_existing_config(module, domain)

        if modifications_needed:
            changed = True
            modifications_needed['DomainName'] = module.params['domain']
            client.update_elasticsearch_domain_config(**modifications_needed)

            # Reload after modifying
            domain = is_present(client, module)

        if module.params['tags']:
            arn = domain['DomainStatus']['ARN']

            tag_list = []
            for each_key, each_value in module.params['tags'].items():
                tag_list.append({'Key': each_key, 'Value': each_value})

            client.add_tags(ARN=arn, TagList=tag_list)

        if module.params['wait']:
            while not domain['DomainStatus'].get('Endpoint'):
                time.sleep(10)
                domain = is_present(client, module)

        domain_status = domain['DomainStatus']
        cluster_config_status = domain_status['ElasticsearchClusterConfig']
        ebs_options = domain_status['EBSOptions']

        module.exit_json(
            changed=changed,
            arn=domain_status['ARN'],
            endpoint=domain_status.get('Endpoint'),
            processing=domain_status['Processing'],
            elasticsearch_version=domain_status['ElasticsearchVersion'],
            instance_type=cluster_config_status['InstanceType'],
            instance_count=cluster_config_status['InstanceCount'],
            dedicated_master_enabled=cluster_config_status['DedicatedMasterEnabled'],
            zone_awareness=cluster_config_status['ZoneAwarenessEnabled'],
            dedicated_master_type=cluster_config_status.get('DedicatedMasterType', ''),
            dedicated_master_count=cluster_config_status.get('DedicatedMasterCount', 0),
            ebs_volume_type=ebs_options['VolumeType'],
            ebs_volume_size=ebs_options['VolumeSize'],
            access_policies=domain_status['AccessPolicies']
        )


if __name__ == '__main__':
    main()
