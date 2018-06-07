#!/usr/bin/python

# Copyright: (c) 2018, Aaron Smith <ajsmith10381@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: aws_neptune_cluster
short_description: Manage graph database clusters on AWS Neptune.
description:
    - Create, modify, and destroy graph database clusters on AWS Neptune
version_added: "2.7"
requirements: [ 'botocore>=1.10.30', 'boto3' ]
author:
    - "Aaron Smith (@slapula)"
options:
  name:
    description:
    - The DB cluster identifier.
    required: true
  state:
    description:
    - Whether the resource should be present or absent.
    default: present
    choices: ['present', 'absent']
  availability_zones:
    description:
    - A list of EC2 Availability Zones that instances in the DB cluster can be created in.
  retention_period:
    description:
    - The number of days for which automated backups are retained.
  character_set:
    description:
    - A value that indicates that the DB cluster should be associated with the specified CharacterSet.
  database_name:
    description:
    - The name for your database of up to 64 alpha-numeric characters.
    - If you do not provide a name, Amazon Neptune will not create a database in the DB cluster you are creating.
  parameter_group:
    description:
    - The name of the DB cluster parameter group to associate with this DB cluster.
    - If this argument is omitted, the default is used.
  vpc_security_groups:
    description:
    - A list of EC2 VPC security groups to associate with this DB cluster.
  db_subnet_group:
    description:
    - A DB subnet group to associate with this DB cluster.
  db_engine:
    description:
    - The name of the database engine to be used for this DB cluster.
    choices: ['neptune']
    default: 'neptune'
  db_engine_version:
    description:
    - The version number of the database engine to use.
    choices: ['1.0.1']
  port:
    description:
    - The port number on which the instances in the DB cluster accept connections.
    default: 8182
  master_username:
    description:
    - The name of the master user for the DB cluster.
  master_password:
    description:
    - The password of the master user for the DB cluster.
  option_group:
    description:
    - A value that indicates that the DB cluster should be associated with the specified option group.
  backup_window:
    description:
    - The daily time range during which automated backups are created if automated backups are enabled using
      the `retention_period` parameter.
  maintenance_window:
    description:
    - The weekly time range during which system maintenance can occur, in Universal Coordinated Time (UTC).
  replication_source:
    description:
    - The Amazon Resource Name (ARN) of the source DB instance or DB cluster if this DB cluster is created as a Read Replica.
  encrypted:
    description:
    - Specifies whether the DB cluster is encrypted.
    type: bool
    default: false
  kms_key_id:
    description:
    - The AWS KMS key identifier for an encrypted DB cluster.
  pre_signed_url:
    description:
    - A URL that contains a Signature Version 4 signed request for the CreateDBCluster action to be called in the source AWS Region
      where the DB cluster is replicated from.
    - You only need to specify PreSignedUrl when you are performing cross-region replication from an encrypted DB cluster.
  enable_iam_auth:
    description:
    - True to enable mapping of AWS Identity and Access Management (IAM) accounts to database accounts, and otherwise false.
    type: bool
    default: false
  skip_final_snapshot:
    description:
    - Determines whether a final DB cluster snapshot is created before the DB cluster is deleted.
    type: bool
    default: false
  final_snapshot_id:
    description:
    - The DB cluster snapshot identifier of the new DB cluster snapshot created when `skip_final_snapshot` is set to false .
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = r'''
  - name: Create a new graph database custer
    aws_neptune_cluster:
      name: "example-cluster"
      state: present
      encrypted: true
      master_username: 'dbadmin'
      master_password: 'Test12345'
      retention_period: 7
      skip_final_snapshot: true
'''

RETURN = r'''
db_cluster_arn:
    description: The ARN of the graph database cluster you just created or updated.
    returned: always
    type: string
'''

try:
    import botocore
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.aws.waiters import get_waiter


def cluster_exists(client, module, params):
    try:
        response = client.describe_db_clusters(
            DBClusterIdentifier=params['DBClusterIdentifier']
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'DBClusterNotFoundFault':
            return {'exists': False}
        else:
            module.fail_json_aws(e, msg="Couldn't verify existence of graph database cluster")
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json_aws(e, msg="Couldn't verify existence of graph database cluster")

    return {'current_config': response['DBClusters'][0], 'exists': True}


def create_cluster(client, module, params):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.create_db_cluster(**params)
        get_waiter(
            client, 'cluster_available'
        ).wait(
            DBClusterIdentifier=params['DBClusterIdentifier']
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't create graph database cluster")

    return {'db_cluster_arn': response['DBCluster']['DBClusterArn'], 'changed': True}


def update_cluster(client, module, params, cluster_status):
    if module.check_mode:
        module.exit_json(changed=True)
    param_changed = []
    param_keys = list(params.keys())
    current_keys = list(cluster_status['current_config'].keys())
    common_keys = set(param_keys) - (set(param_keys) - set(current_keys))
    for key in common_keys:
        if (params[key] != cluster_status['current_config'][key]):
            param_changed.append(True)
        else:
            param_changed.append(False)

    if 'AvailabilityZones' in params:
        del params['AvailabilityZones']
    if 'CharacterSetName' in params:
        del params['CharacterSetName']
    if 'DatabaseName' in params:
        del params['DatabaseName']
    if 'DBSubnetGroupName' in params:
        del params['DBSubnetGroupName']
    if 'Engine' in params:
        del params['Engine']
    if 'MasterUsername' in params:
        del params['MasterUsername']
    if 'ReplicationSourceIdentifier' in params:
        del params['ReplicationSourceIdentifier']
    if 'StorageEncrypted' in params:
        del params['StorageEncrypted']
    if 'KmsKeyId' in params:
        del params['KmsKeyId']
    if 'PreSignedUrl' in params:
        del params['PreSignedUrl']

    if any(param_changed):
        try:
            response = client.modify_db_cluster(**params)
            get_waiter(
                client, 'cluster_available'
            ).wait(
                DBClusterIdentifier=params['DBClusterIdentifier']
            )
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't update graph database cluster")
        return {'db_cluster_arn': response['DBCluster']['DBClusterArn'], 'changed': True}
    else:
        return {'db_cluster_arn': cluster_status['current_config']['DBClusterArn'], 'changed': False}


def delete_cluster(client, module):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        params = {}
        params['DBClusterIdentifier'] = module.params.get('name')
        if module.params.get('skip_final_snapshot'):
            params['SkipFinalSnapshot'] = module.params.get('skip_final_snapshot')
        if module.params.get('final_snapshot_id'):
            params['FinalDBSnapshotIdentifier'] = module.params.get('final_snapshot_id')
        response = client.delete_db_cluster(**params)
        get_waiter(
            client, 'cluster_deleted'
        ).wait(
            DBClusterIdentifier=params['DBClusterIdentifier']
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't delete graph database cluster")

    return {'db_cluster_arn': '', 'changed': True}


def main():
    module = AnsibleAWSModule(
        argument_spec={
            'name': dict(type='str', required=True),
            'state': dict(type='str', choices=['present', 'absent'], default='present'),
            'availability_zones': dict(type='list'),
            'retention_period': dict(type='int'),
            'character_set': dict(type='str'),
            'database_name': dict(type='str'),
            'parameter_group': dict(type='str'),
            'vpc_security_groups': dict(type='list'),
            'db_subnet_group': dict(type='str'),
            'db_engine': dict(type='str', choices=['neptune'], default='neptune'),
            'db_engine_version': dict(type='str', choices=['1.0.1']),
            'port': dict(type='int', default=8182),
            'master_username': dict(type='str'),
            'master_password': dict(type='str'),
            'option_group': dict(type='str'),
            'backup_window': dict(type='str'),
            'maintenance_window': dict(type='str'),
            'replication_source': dict(type='str'),
            'encrypted': dict(type='bool', default=False),
            'kms_key_id': dict(type='str'),
            'pre_signed_url': dict(type='str'),
            'enable_iam_auth': dict(type='bool', default=False),
            'skip_final_snapshot': dict(type='bool', default=False),
            'final_snapshot_id': dict(type='str'),
        },
        supports_check_mode=True,
    )

    if not module.botocore_at_least('1.10.30'):
        module.fail_json(msg="This module requires botocore >= 1.10.30")

    result = {
        'changed': False,
        'db_cluster_arn': ''
    }

    desired_state = module.params.get('state')

    params = {}
    if module.params.get('availability_zones'):
        params['AvailabilityZones'] = module.params.get('availability_zones')
    if module.params.get('retention_period'):
        params['BackupRetentionPeriod'] = module.params.get('retention_period')
    if module.params.get('character_set'):
        params['CharacterSet'] = module.params.get('character_set')
    if module.params.get('database_name'):
        params['DatabaseName'] = module.params.get('database_name')
    params['DBClusterIdentifier'] = module.params.get('name')
    if module.params.get('parameter_group'):
        params['DBClusterParameterGroupName'] = module.params.get('parameter_group')
    if module.params.get('vpc_security_groups'):
        params['VpcSecurityGroupIds'] = module.params.get('vpc_security_groups')
    if module.params.get('db_subnet_group'):
        params['DBSubnetGroupName'] = module.params.get('db_subnet_group')
    params['Engine'] = module.params.get('db_engine')
    if module.params.get('db_engine_version'):
        params['EngineVersion'] = module.params.get('db_engine_version')
    if module.params.get('port'):
        params['Port'] = module.params.get('port')
    if module.params.get('master_username'):
        params['MasterUsername'] = module.params.get('master_username')
    if module.params.get('master_password'):
        params['MasterUserPassword'] = module.params.get('master_password')
    if module.params.get('option_group'):
        params['OptionGroupName'] = module.params.get('option_group')
    if module.params.get('backup_window'):
        params['PreferredBackupWindow'] = module.params.get('backup_window')
    if module.params.get('maintenance_window'):
        params['PreferredMaintenanceWindow'] = module.params.get('maintenance_window')
    if module.params.get('replication_source'):
        params['ReplicationSourceIdentifier'] = module.params.get('replication_source')
    if module.params.get('encrypted'):
        params['StorageEncrypted'] = module.params.get('encrypted')
    if module.params.get('kms_key_id'):
        params['KmsKeyId'] = module.params.get('kms_key_id')
    if module.params.get('pre_signed_url'):
        params['PreSignedUrl'] = module.params.get('pre_signed_url')
    if module.params.get('enable_iam_auth'):
        params['EnableIAMDatabaseAuthentication'] = module.params.get('enable_iam_auth')

    client = module.client('neptune')

    cluster_status = cluster_exists(client, module, params)

    if desired_state == 'present':
        if not cluster_status['exists']:
            result = create_cluster(client, module, params)
        if cluster_status['exists']:
            result = update_cluster(client, module, params, cluster_status)

    if desired_state == 'absent':
        if cluster_status['exists']:
            result = delete_cluster(client, module)

    module.exit_json(changed=result['changed'], db_cluster_arn=result['db_cluster_arn'])


if __name__ == '__main__':
    main()
