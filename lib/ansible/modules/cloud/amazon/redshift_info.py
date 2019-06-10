#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: redshift_info
author: "Jens Carl (@j-carl)"
short_description: Gather information about Redshift cluster(s)
description:
  - Gather information about Redshift cluster(s)
  - This module was called C(redshift_facts) before Ansible 2.9. The usage did not change.
version_added: "2.4"
requirements: [ boto3 ]
options:
  cluster_identifier:
    description:
      - The prefix of cluster identifier of the Redshift cluster you are searching for.
      - "This is a regular expression match with implicit '^'. Append '$' for a complete match."
    required: false
    aliases: ['name', 'identifier']
  tags:
    description:
      - "A dictionary/hash of tags in the format { tag1_name: 'tag1_value', tag2_name: 'tag2_value' }
       to match against the security group(s) you are searching for."
    required: false
extends_documentation_fragment:
    - ec2
    - aws
'''

EXAMPLES = '''
# Note: These examples do net set authentication details, see the AWS guide for details.

# Find all clusters
- redshift_info:
  register: redshift

# Find cluster(s) with matching tags
- redshift_info:
    tags:
      env: prd
      stack: monitoring
  register: redshift_tags

# Find cluster(s) with matching name/prefix and tags
- redshift_info:
    tags:
      env: dev
      stack: web
    name: user-
  register: redshift_web

# Fail if no cluster(s) is/are found
- redshift_info:
    tags:
      env: stg
      stack: db
  register: redshift_user
  failed_when: "{{ redshift_user.results | length == 0 }}"
'''

RETURN = '''
# For more information see U(http://boto3.readthedocs.io/en/latest/reference/services/redshift.html#Redshift.Client.describe_clusters)
---
cluster_identifier:
    description: Unique key to identify the cluster.
    returned: success
    type: str
    sample: "redshift-identifier"
node_type:
    description: The node type for nodes in the cluster.
    returned: success
    type: str
    sample: "ds2.xlarge"
cluster_status:
    description: Current state of the cluster.
    returned: success
    type: str
    sample: "available"
modify_status:
    description: The status of a modify operation.
    returned: optional
    type: str
    sample: ""
master_username:
    description: The master user name for the cluster.
    returned: success
    type: str
    sample: "admin"
db_name:
    description: The name of the initial database that was created when the cluster was created.
    returned: success
    type: str
    sample: "dev"
endpoint:
    description: The connection endpoint.
    returned: success
    type: str
    sample: {
        "address": "cluster-ds2.ocmugla0rf.us-east-1.redshift.amazonaws.com",
        "port": 5439
    }
cluster_create_time:
    description: The date and time that the cluster was created.
    returned: success
    type: str
    sample: "2016-05-10T08:33:16.629000+00:00"
automated_snapshot_retention_period:
    description: The number of days that automatic cluster snapshots are retained.
    returned: success
    type: int
    sample: 1
cluster_security_groups:
    description: A list of cluster security groups that are associated with the cluster.
    returned: success
    type: list
    sample: []
vpc_security_groups:
    description: A list of VPC security groups the are associated with the cluster.
    returned: success
    type: list
    sample: [
        {
            "status": "active",
            "vpc_security_group_id": "sg-12cghhg"
        }
    ]
cluster_paramater_groups:
    description: The list of cluster parameters that are associated with this cluster.
    returned: success
    type: list
    sample: [
        {
            "cluster_parameter_status_list": [
                {
                    "parameter_apply_status": "in-sync",
                    "parameter_name": "statement_timeout"
                },
                {
                    "parameter_apply_status": "in-sync",
                    "parameter_name": "require_ssl"
                }
            ],
            "parameter_apply_status": "in-sync",
            "parameter_group_name": "tuba"
        }
    ]
cluster_subnet_group_name:
    description: The name of the subnet group that is associated with the cluster.
    returned: success
    type: str
    sample: "redshift-subnet"
vpc_id:
    description: The identifier of the VPC the cluster is in, if the cluster is in a VPC.
    returned: success
    type: str
    sample: "vpc-1234567"
availability_zone:
    description: The name of the Availability Zone in which the cluster is located.
    returned: success
    type: str
    sample: "us-east-1b"
preferred_maintenance_window:
    description: The weekly time range, in Universal Coordinated Time (UTC), during which system maintenance can occur.
    returned: success
    type: str
    sample: "tue:07:30-tue:08:00"
pending_modified_values:
    description: A value that, if present, indicates that changes to the cluster are pending.
    returned: success
    type: dict
    sample: {}
cluster_version:
    description: The version ID of the Amazon Redshift engine that is running on the cluster.
    returned: success
    type: str
    sample: "1.0"
allow_version_upgrade:
    description: >
      A Boolean value that, if true, indicates that major version upgrades will be applied
      automatically to the cluster during the maintenance window.
    returned: success
    type: bool
    sample: true|false
number_of_nodes:
    description:  The number of compute nodes in the cluster.
    returned: success
    type: int
    sample: 12
publicly_accessible:
    description: A Boolean value that, if true , indicates that the cluster can be accessed from a public network.
    returned: success
    type: bool
    sample: true|false
encrypted:
    description: Boolean value that, if true , indicates that data in the cluster is encrypted at rest.
    returned: success
    type: bool
    sample: true|false
restore_status:
    description: A value that describes the status of a cluster restore action.
    returned: success
    type: dict
    sample: {}
hsm_status:
    description: >
      A value that reports whether the Amazon Redshift cluster has finished applying any hardware
      security module (HSM) settings changes specified in a modify cluster command.
    returned: success
    type: dict
    sample: {}
cluster_snapshot_copy_status:
    description: A value that returns the destination region and retention period that are configured for cross-region snapshot copy.
    returned: success
    type: dict
    sample: {}
cluster_public_keys:
    description: The public key for the cluster.
    returned: success
    type: str
    sample: "ssh-rsa anjigfam Amazon-Redshift\n"
cluster_nodes:
    description: The nodes in the cluster.
    returned: success
    type: list
    sample: [
        {
            "node_role": "LEADER",
            "private_ip_address": "10.0.0.1",
            "public_ip_address": "x.x.x.x"
        },
        {
            "node_role": "COMPUTE-1",
            "private_ip_address": "10.0.0.3",
            "public_ip_address": "x.x.x.x"
        }
    ]
elastic_ip_status:
    description: The status of the elastic IP (EIP) address.
    returned: success
    type: dict
    sample: {}
cluster_revision_number:
    description: The specific revision number of the database in the cluster.
    returned: success
    type: str
    sample: "1231"
tags:
    description: The list of tags for the cluster.
    returned: success
    type: list
    sample: []
kms_key_id:
    description: The AWS Key Management Service (AWS KMS) key ID of the encryption key used to encrypt data in the cluster.
    returned: success
    type: str
    sample: ""
enhanced_vpc_routing:
    description: An option that specifies whether to create the cluster with enhanced VPC routing enabled.
    returned: success
    type: bool
    sample: true|false
iam_roles:
    description: List of IAM roles attached to the cluster.
    returned: success
    type: list
    sample: []
'''

import re
import traceback

try:
    from botocore.exception import ClientError
except ImportError:
    pass  # will be picked up from imported HAS_BOTO3

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, boto3_conn, get_aws_connection_info
from ansible.module_utils.ec2 import HAS_BOTO3, camel_dict_to_snake_dict


def match_tags(tags_to_match, cluster):
    for key, value in tags_to_match.items():
        for tag in cluster['Tags']:
            if key == tag['Key'] and value == tag['Value']:
                return True

    return False


def find_clusters(conn, module, identifier=None, tags=None):

    try:
        cluster_paginator = conn.get_paginator('describe_clusters')
        clusters = cluster_paginator.paginate().build_full_result()
    except ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    matched_clusters = []

    if identifier is not None:
        identifier_prog = re.compile('^' + identifier)

    for cluster in clusters['Clusters']:

        matched_identifier = True
        if identifier:
            matched_identifier = identifier_prog.search(cluster['ClusterIdentifier'])

        matched_tags = True
        if tags:
            matched_tags = match_tags(tags, cluster)

        if matched_identifier and matched_tags:
            matched_clusters.append(camel_dict_to_snake_dict(cluster))

    return matched_clusters


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            cluster_identifier=dict(type='str', aliases=['identifier', 'name']),
            tags=dict(type='dict')
        )
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )
    if module._name == 'redshift_facts':
        module.deprecate("The 'redshift_facts' module has been renamed to 'redshift_info'", version='2.13')

    cluster_identifier = module.params.get('cluster_identifier')
    cluster_tags = module.params.get('tags')

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        redshift = boto3_conn(module, conn_type='client', resource='redshift', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except ClientError as e:
        module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    results = find_clusters(redshift, module, identifier=cluster_identifier, tags=cluster_tags)
    module.exit_json(results=results)


if __name__ == '__main__':
    main()
