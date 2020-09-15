#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: elasticache_snapshot
short_description: Manage cache snapshots in Amazon Elasticache.
description:
  - Manage cache snapshots in Amazon Elasticache.
  - Returns information about the specified snapshot.
version_added: "2.3"
author: "Sloane Hertel (@s-hertel)"
extends_documentation_fragment:
  - aws
  - ec2
requirements: [ boto3, botocore ]
options:
  name:
    description:
      - The name of the snapshot we want to create, copy, delete
    required: yes
  state:
    description:
      - Actions that will create, destroy, or copy a snapshot.
    choices: ['present', 'absent', 'copy']
  replication_id:
    description:
      - The name of the existing replication group to make the snapshot.
  cluster_id:
    description:
      - The name of an existing cache cluster in the replication group to make the snapshot.
  target:
    description:
      - The name of a snapshot copy
  bucket:
    description:
      - The s3 bucket to which the snapshot is exported
"""

EXAMPLES = """
# Note: None of these examples set aws_access_key, aws_secret_key, or region.
# It is assumed that their matching environment variables are set.
---
- hosts: localhost
  connection: local
  tasks:
    - name: 'Create a snapshot'
      elasticache_snapshot:
        name: 'test-snapshot'
        state: 'present'
        cluster_id: '{{ cluster }}'
        replication_id: '{{ replication }}'
"""

RETURN = """
response_metadata:
  description: response metadata about the snapshot
  returned: always
  type: dict
  sample:
    http_headers:
      content-length: 1490
      content-type: text/xml
      date: Tue, 07 Feb 2017 16:43:04 GMT
      x-amzn-requestid: 7f436dea-ed54-11e6-a04c-ab2372a1f14d
    http_status_code: 200
    request_id: 7f436dea-ed54-11e6-a04c-ab2372a1f14d
    retry_attempts: 0
snapshot:
  description: snapshot data
  returned: always
  type: dict
  sample:
    auto_minor_version_upgrade: true
    cache_cluster_create_time: '2017-02-01T17:43:58.261000+00:00'
    cache_cluster_id: test-please-delete
    cache_node_type: cache.m1.small
    cache_parameter_group_name: default.redis3.2
    cache_subnet_group_name: default
    engine: redis
    engine_version: 3.2.4
    node_snapshots:
      cache_node_create_time: '2017-02-01T17:43:58.261000+00:00'
      cache_node_id: 0001
      cache_size:
    num_cache_nodes: 1
    port: 11211
    preferred_availability_zone: us-east-1d
    preferred_maintenance_window: wed:03:00-wed:04:00
    snapshot_name: deletesnapshot
    snapshot_retention_limit: 0
    snapshot_source: manual
    snapshot_status: creating
    snapshot_window: 10:00-11:00
    vpc_id: vpc-c248fda4
changed:
  description: if a snapshot has been created, deleted, or copied
  returned: always
  type: bool
  sample:
    changed: true
"""

import traceback

try:
    import boto3
    import botocore
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, ec2_argument_spec, camel_dict_to_snake_dict


def create(module, connection, replication_id, cluster_id, name):
    """ Create an Elasticache backup. """
    try:
        response = connection.create_snapshot(ReplicationGroupId=replication_id,
                                              CacheClusterId=cluster_id,
                                              SnapshotName=name)
        changed = True
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "SnapshotAlreadyExistsFault":
            response = {}
            changed = False
        else:
            module.fail_json(msg="Unable to create the snapshot.", exception=traceback.format_exc())
    return response, changed


def copy(module, connection, name, target, bucket):
    """ Copy an Elasticache backup. """
    try:
        response = connection.copy_snapshot(SourceSnapshotName=name,
                                            TargetSnapshotName=target,
                                            TargetBucket=bucket)
        changed = True
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Unable to copy the snapshot.", exception=traceback.format_exc())
    return response, changed


def delete(module, connection, name):
    """ Delete an Elasticache backup. """
    try:
        response = connection.delete_snapshot(SnapshotName=name)
        changed = True
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "SnapshotNotFoundFault":
            response = {}
            changed = False
        elif e.response['Error']['Code'] == "InvalidSnapshotState":
            module.fail_json(msg="Error: InvalidSnapshotState. The snapshot is not in an available state or failed state to allow deletion."
                             "You may need to wait a few minutes.")
        else:
            module.fail_json(msg="Unable to delete the snapshot.", exception=traceback.format_exc())
    return response, changed


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True, type='str'),
            state=dict(required=True, type='str', choices=['present', 'absent', 'copy']),
            replication_id=dict(type='str'),
            cluster_id=dict(type='str'),
            target=dict(type='str'),
            bucket=dict(type='str'),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='boto required for this module')

    name = module.params.get('name')
    state = module.params.get('state')
    replication_id = module.params.get('replication_id')
    cluster_id = module.params.get('cluster_id')
    target = module.params.get('target')
    bucket = module.params.get('bucket')

    # Retrieve any AWS settings from the environment.
    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    if not region:
        module.fail_json(msg=str("Either region or AWS_REGION or EC2_REGION environment variable or boto config aws_region or ec2_region must be set."))

    connection = boto3_conn(module, conn_type='client',
                            resource='elasticache', region=region,
                            endpoint=ec2_url, **aws_connect_kwargs)

    changed = False
    response = {}

    if state == 'present':
        if not all((replication_id, cluster_id)):
            module.fail_json(msg="The state 'present' requires options: 'replication_id' and 'cluster_id'")
        response, changed = create(module, connection, replication_id, cluster_id, name)
    elif state == 'absent':
        response, changed = delete(module, connection, name)
    elif state == 'copy':
        if not all((target, bucket)):
            module.fail_json(msg="The state 'copy' requires options: 'target' and 'bucket'.")
        response, changed = copy(module, connection, name, target, bucket)

    facts_result = dict(changed=changed, **camel_dict_to_snake_dict(response))

    module.exit_json(**facts_result)


if __name__ == '__main__':
    main()
