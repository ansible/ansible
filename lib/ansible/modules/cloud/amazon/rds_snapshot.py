#!/usr/bin/python
# Copyright (c) 2014 Ansible Project
# Copyright (c) 2017, 2018, 2019 Will Thames
# Copyright (c) 2017, 2018 Michael De La Rue
# Copyright (c) 2019 Joel Stuedle
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}
DOCUMENTATION = '''
---
module: rds_snapshot
version_added: "2.9"
short_description: manage Amazon RDS/Aurora snapshots.
description:
     - Creates or deletes RDS snapshots.
options:
  snapshot_type:
    description:
      - Specify cluster or instance snapshot.
    default: instance
    choices: ['instance', 'aurora']
    type: str
  state:
    description:
      - Specify the desired state of the snapshot.
    default: present
    choices: ['present', 'absent']
    type: str
  db_snapshot_identifier:
    description:
      - The snapshot to manage.
    required: true
    aliases:
      - id
      - snapshot_id
    type: str
  db_instance_identifier:
    description:
      - Database instance identifier. Required when state is present.
    aliases:
      - instance_id
    type: str
  db_cluster_identifier:
    description:
      - Database cluster identifier (Aurora). Required when snapshot_type is aurora.
    aliases:
      - cluster_id
    type: str
  wait:
    description:
      - Whether or not to wait for snapshot creation or deletion.
    type: bool
    default: False
  wait_timeout:
    description:
      - how long before wait gives up, in seconds.
    default: 300
    type: int
  tags:
    description:
      - tags dict to apply to a snapshot.
    type: dict
  purge_tags:
    description:
      - whether to remove tags not present in the C(tags) parameter.
    default: True
    type: bool
  fail_on_not_exists:
    description:
      - whether to fail if trying to delete a non-existent snapshot.
    default: False
    type: bool
requirements:
    - "python >= 2.6"
    - "boto3"
author:
    - "Will Thames (@willthames)"
    - "Michael De La Rue (@mikedlr)"
    - "Joel Stuedle (@jtstuedle)"
extends_documentation_fragment:
    - aws
    - ec2
'''
EXAMPLES = '''
# Create snapshot
- name: Create RDS snapshot
  rds_snapshot:
    db_instance_identifier: new-database
    db_snapshot_identifier: new-database-snapshot

# Delete snapshot
- name: Delete RDS snapshot
- rds_snapshot:
    db_snapshot_identifier: new-database-snapshot
    state: absent
    
# Create Aurora cluster snapshot
- name: Create Aurora cluster snapshot
  rds_snapshot:
    type: aurora
    db_cluster_identifier: default-cluster
    db_snapshot_identifier: new-cluster-snapshot

# Delete Aurora cluster snapshot
- name: Delete Aurora cluster snapshot
  rds_snapshot:
    type: aurora
    state: absent
    db_snapshot_identifier: new-cluster-snapshot
'''
RETURN = '''
allocated_storage:
  description: How much storage is allocated in GB.
  returned: always
  type: int
  sample: 20
availability_zone:
  description: Availability zone of the database from which the snapshot was created.
  returned: always
  type: str
  sample: us-west-2a
availability_zones:
  description: Provides the list of Availability Zones (AZs) where instances in the DB cluster snapshot can be restored.
  returned: always
  type: list
  sample: [ 'us-east-2a', 'us-east-2b', 'us-east-2c' ]
cluster_create_time:
  description: Specifies the time when the DB cluster was created, in Universal Coordinated Time (UTC).
  returned: always
  type: str
db_cluster_identifier:
  description: Specifies the DB cluster identifier of the DB cluster that this DB cluster snapshot was created from.
  returned: always
  type: str
  sample: test-cluster
db_cluster_snapshot:
  description: Contains the details for an Amazon RDS DB cluster snapshot
  returned: always
  type: dict
  sample: example-cluster-snapshot
db_cluster_snapshot_identifier:
  description: Specifies the identifier for the DB cluster snapshot.
  returned: always
  type: str
  sample: example-snapshot-identifier
db_cluster_snapshot_arn:
  description: The Amazon Resource Name (ARN) for the DB cluster snapshot.
  returned: always
  type: str
  sample: arn:aws:rds:us-west-2:123456789012:snapshot:ansible-test-16638696-test-snapshot
db_instance_identifier:
  description: Database from which the snapshot was created.
  returned: always
  type: str
  sample: ansible-test-16638696
db_snapshot_arn:
  description: Amazon Resource Name for the snapshot.
  returned: always
  type: str
  sample: arn:aws:rds:us-west-2:123456789012:snapshot:ansible-test-16638696-test-snapshot
db_snapshot_identifier:
  description: Name of the snapshot.
  returned: always
  type: str
  sample: ansible-test-16638696-test-snapshot
dbi_resource_id:
  description: The identifier for the source DB instance, which can't be changed and which is unique to an AWS Region.
  returned: always
  type: str
  sample: db-MM4P2U35RQRAMWD3QDOXWPZP4U
encrypted:
  description: Whether the snapshot is encrypted.
  returned: always
  type: bool
  sample: false
engine:
  description: Engine of the database from which the snapshot was created.
  returned: always
  type: str
  sample: mariadb
engine_version:
  description: Version of the database from which the snapshot was created.
  returned: always
  type: str
  sample: 10.2.21
iam_database_authentication_enabled:
  description: Whether IAM database authentication is enabled.
  returned: always
  type: bool
  sample: false
instance_create_time:
  description: Creation time of the instance from which the snapshot was created.
  returned: always
  type: str
  sample: '2019-06-15T10:15:56.221000+00:00'
license_model:
  description: License model of the database.
  returned: always
  type: str
  sample: general-public-license
kms_key_id:
  description: If StorageEncrypted is true, the AWS KMS key identifier for the encrypted DB cluster snapshot.
  returned: always
  type: str
master_username:
  description: Master username of the database.
  returned: always
  type: str
  sample: test
option_group_name:
  description: Option group of the database.
  returned: always
  type: str
  sample: default:mariadb-10-2
percent_progress:
  description: How much progress has been made taking the snapshot. Will be 100 for an available snapshot.
  returned: always
  type: int
  sample: 100
port:
  description: Port on which the database is listening.
  returned: always
  type: int
  sample: 3306
processor_features:
  description: List of processor features of the database.
  returned: always
  type: list
  sample: []
snapshot_create_time:
  description: Creation time of the snapshot.
  returned: always
  type: str
  sample: '2019-06-15T10:46:23.776000+00:00'
snapshot_type:
  description: How the snapshot was created (always manual for this module!).
  returned: always
  type: str
  sample: manual
status:
  description: Status of the snapshot.
  returned: always
  type: str
  sample: available
storage_encrypted:
  description: Specifies whether the DB cluster snapshot is encrypted.
  returned: always
  type: bool
storage_type:
  description: Storage type of the database.
  returned: always
  type: str
  sample: gp2
tags:
  description: Tags applied to the snapshot.
  returned: always
  type: complex
  contains: {}
vpc_id:
  description: ID of the VPC in which the DB lives.
  returned: always
  type: str
  sample: vpc-09ff232e222710ae0
'''

try:
    import botocore
except ImportError:
    pass  # protected by AnsibleAWSModule

# import module snippets
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, AWSRetry, compare_aws_tags
from ansible.module_utils.ec2 import boto3_tag_list_to_ansible_dict, ansible_dict_to_boto3_tag_list

def get_snapshot(client, module):
  snapshot_id = module.params.get('db_snapshot_identifier')
  try:
    if module.params.get('snapshot_type') == 'aurora':
      db_cluster_identifier = module.params.get('db_cluster_identifier')
      response = client.describe_db_cluster_snapshots(DBClusterIdentifier=db_cluster_identifier,
                                                        DBClusterSnapshotIdentifier=snapshot_id)
      return response['DBClusterSnapshots']
    else:
      response = client.describe_db_snapshots(DBSnapshotIdentifier=snapshot_id)
      return response['DBSnapshots']
  except client.exceptions.DBSnapshotNotFoundFault:
    return None
  except client.exceptions.DBClusterSnapshotNotFoundFault:
    return None
  except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
    module.fail_json_aws(e, msg="Couldn't get snapshot {0}".format(snapshot_id))
  return response

def snapshot_to_facts(client, module, snapshot):
    try:
        if module.params.get('snapshot_type') == 'aurora':
            snapshot['Tags'] = boto3_tag_list_to_ansible_dict(client.list_tags_for_resource(ResourceName=snapshot['DBClusterSnapshotArn'],
                                                                                            aws_retry=True)['TagList'])
        else:
            snapshot['Tags'] = boto3_tag_list_to_ansible_dict(client.list_tags_for_resource(ResourceName=snapshot['DBSnapshotArn'],
                                                                                        aws_retry=True)['TagList'])
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, "Couldn't get tags for snapshot %s" % snapshot['DBSnapshotIdentifier'])
    except KeyError:
        module.fail_json(msg=str(snapshot))

    return camel_dict_to_snake_dict(snapshot, ignore_list=['Tags'])

def wait_for_snapshot_status(client, module, db_snapshot_id, waiter_name):
    if not module.params['wait']:
        return
    timeout = module.params['wait_timeout']
    try:
      if module.params['snapshot_type'] == 'aurora':
        db_cluster_identifier = module.params['db_cluster_identifier']
        client.get_waiter(waiter_name).wait(DBClusterIdentifier=db_cluster_identifier, DBClusterSnapshotIdentifier=db_snapshot_id,
                                            WaiterConfig=dict(
                                                Delay=5,
                                                MaxAttempts=int((timeout + 2.5) / 5)
                                            ))
      else:
        client.get_waiter(waiter_name).wait(DBSnapshotIdentifier=db_snapshot_id,
                                            WaiterConfig=dict(
                                                Delay=5,
                                                MaxAttempts=int((timeout + 2.5) / 5)
                                            ))
    except botocore.exceptions.WaiterError as e:
      if waiter_name == 'db_snapshot_deleted' or waiter_name == 'db_cluster_snapshot_deleted':
        msg = "Failed to wait for DB snapshot {0} to be deleted".format(db_snapshot_id)
      else:
        msg = "Failed to wait for DB snapshot {0} to be available".format(db_snapshot_id)
      module.fail_json_aws(e, msg=msg)
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        module.fail_json_aws(e, msg="Failed with an unexpected error while waiting for the DB cluster {0}".format(db_snapshot_id))

def ensure_snapshot_absent(client, module):
  fn_args = dict()
  if module.params.get('snapshot_type') == 'aurora':
    fn_args['DBClusterSnapshotIdentifier'] = module.params.get('db_snapshot_identifier')
  else:
    fn_args['DBSnapshotIdentifier'] = module.params.get('db_snapshot_identifier')
  changed = False

  snapshot = get_snapshot(client, module)
  
  if snapshot:
    if module.params.get('snapshot_type') == 'aurora':
      if snapshot[0].get('Status') != 'deleting':
        try:
          client.delete_db_cluster_snapshot(**fn_args)
          changed = True
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
          module.fail_json_aws(e, msg="trying to delete cluster snapshot")
    else:
      try:
        client.delete_db_snapshot(**fn_args)
        changed = True
      except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
          module.fail_json_aws(e, msg="trying to delete snapshot")

  elif not snapshot and module.params.get('fail_on_not_exists'):
    module.fail_json_aws(snapshot, msg="cannot delete nonexistent snapshot")

  # If we're not waiting for a delete to complete then we're all done
  # so just return
  elif not snapshot or not module.params.get('wait'):
    return dict(changed=changed)

  try:
    if module.params.get('snapshot_type') == 'aurora':
      wait_for_snapshot_status(client, module, module.params.get('db_snapshot_identifier'), 'db_cluster_snapshot_deleted')
      return dict(changed=changed)
    else:
      wait_for_snapshot_status(client, module, module.params.get('db_snapshot_identifier'), 'db_snapshot_deleted')
      return dict(changed=changed)
  except client.exceptions.DBSnapshotNotFoundFault:
    return dict(changed=changed)
  except client.exceptions.DBClusterSnapshotNotFoundFault:
    return dict(changed=changed)
  except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
    module.fail_json_aws(e, "awaiting snapshot deletion")
        
def ensure_tags(client, module, snapshot, existing_tags, tags, purge_tags):
  if tags is None:
    return False

  if module.params.get('snapshot_type') == 'aurora':
    resource_arn = snapshot[0].get('DBClusterSnapshotArn')
  else:
    resource_arn = snapshot[0].get('DBSnapshotArn')

  tags_to_add, tags_to_remove = compare_aws_tags(existing_tags, tags, purge_tags)
  changed = bool(tags_to_add or tags_to_remove)
  if tags_to_add:
    try:
      client.add_tags_to_resource(ResourceName=resource_arn, Tags=ansible_dict_to_boto3_tag_list(tags_to_add))
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
      module.fail_json_aws(e, "Couldn't add tags to snapshot {0}".format(resource_arn))
  if tags_to_remove:
    try:
      client.remove_tags_from_resource(ResourceName=resource_arn, TagKeys=tags_to_remove)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
      module.fail_json_aws(e, "Couldn't remove tags from snapshot {0}".format(resource_arn))
  return changed

def ensure_snapshot_present(client, module):
  fn_args= dict()
  if module.params.get('snapshot_type') == 'aurora':
    fn_args['DBClusterSnapshotIdentifier'] = module.params.get('db_snapshot_identifier')
    fn_args['DBClusterIdentifier'] = module.params.get('db_cluster_identifier')
  else:
    fn_args['DBSnapshotIdentifier'] = module.params.get('db_snapshot_identifier')
    fn_args['DBInstanceIdentifier'] = module.params.get('db_instance_identifier')


  if module.params['tags'] and module.params['tags'] is not None:
    fn_args['Tags'] = ansible_dict_to_boto3_tag_list(module.params['tags'])
  changed = False

  try:
    if module.params.get('snapshot_type') == 'aurora':
      response = client.create_db_cluster_snapshot(**fn_args)
    else:
      response = client.create_db_snapshot(**fn_args)
  except client.exceptions.DBClusterSnapshotAlreadyExistsFault as e:
    module.fail_json_aws(e, msg="Failed to create cluster snapshot. A cluster snapshot with this snapshot_identifier already exists")
  except client.exceptions.DBSnapshotAlreadyExistsFault as e:
    module.fail_json_aws(e, msg="Failed to create cluster snapshot. A cluster snapshot with this snapshot_identifier already exists")
  except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
    module.fail_json_aws(e, msg="Failed to create cluster or instance snapshot")

  snapshot = get_snapshot(client, module)
  if module.params.get('snapshot_type') == 'aurora':
    existing_tags = boto3_tag_list_to_ansible_dict(client.list_tags_for_resource(ResourceName=snapshot[0].get('DBClusterSnapshotArn'),
                                                                                 aws_retry=True)['TagList'])
  else:
    existing_tags = boto3_tag_list_to_ansible_dict(client.list_tags_for_resource(ResourceName=snapshot[0].get('DBSnapshotArn'),
                                                                                 aws_retry=True)['TagList'])                                                                                 
  desired_tags = module.params.get('tags')
  purge_tags = module.params.get('purge_tags')
  changed |= ensure_tags(client, module, snapshot, existing_tags, desired_tags, purge_tags)

  snapshot = get_snapshot(client, module)  

  relevant_response = dict(rds=snapshot)

  return relevant_response

def main():
    module = AnsibleAWSModule(
        argument_spec=dict(
            snapshot_type=dict(choices=['instance', 'aurora'], default='instance'),
            state=dict(choices=['present', 'absent'], default='present'),
            db_snapshot_identifier=dict(type='str', aliases=['id', 'snapshot_id'], required=True),
            db_instance_identifier=dict(type='str', aliases=['instance_id']),
            db_cluster_identifier=dict(type='str', aliases=['cluster_id']),
            wait=dict(type='bool', default=False),
            wait_timeout=dict(type='int', default=300),
            tags=dict(type='dict'),
            purge_tags=dict(type='bool', default=True),
            fail_on_not_exists=dict(type='bool', default=False)
        ),
        required_if=[
          ['snapshot_type', 'aurora', ["db_cluster_identifier"]],
          ['snapshot_type', 'instance', ["db_instance_identifier"]]
        ],
        mutually_exclusive=[
         ['db_cluster_identifier', 'db_instance_identifier']
         ]
    )
    client = module.client('rds', retry_decorator=AWSRetry.jittered_backoff(retries=10))

    if module.params['state'] == 'absent':
      ret_dict = ensure_snapshot_absent(client, module)
    else:
      ret_dict = ensure_snapshot_present(client, module)

    module.exit_json(**ret_dict)

if __name__ == '__main__':
  main()
