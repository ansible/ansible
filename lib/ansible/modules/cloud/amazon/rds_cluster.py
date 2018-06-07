#!/usr/bin/python
# Copyright (c) 2018 Ansible Project
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
module: rds_cluster
version_added: "2.7"
short_description: Manage RDS clusters
description:
    - Create, modify, and delete RDS clusters.

requirements:
    - botocore
    - boto3
extends_documentation_fragment:
    - aws
    - ec2
author:
    - Sloane Hertel (@s-hertel)

options:
  # General module options
    state:
        description: Whether the snapshot should exist or not.
        choices: ['present', 'absent']
        default: 'present'
    creation_source:
        description: Which source to use if creating from a template (an existing cluster, S3 bucket, or snapshot).
        choices: ['snapshot', 's3', 'cluster']
    force_update_password:
        description:
          - Set to True to update your cluster password with I(master_user_password). Since comparing passwords to determine
            if it needs to be updated is not possible this is set to False by default to allow idempotence.
        type: bool
        default: False
    promote:
        description: Set to True to promote a read replica cluster.
        type: bool
        default: False
    wait:
        description: Whether to wait for the cluster to be available or deleted.
        type: bool
        default: True

    # Options that have a corresponding boto3 parameter
    apply_immediately:
        description:
          - A value that specifies whether modifying a cluster with I(new_db_cluster_identifier) and I(master_user_password)
            should be applied as soon as possible, regardless of the I(preferred_maintenance_window) setting. If false, changes
            are applied during the next maintenance window.
        type: bool
        default: False
    availability_zones:
        description:
          - A list of EC2 Availability Zones that instances in the DB cluster can be created in.
            May be used when creating a cluster or when restoring from S3 or a snapshot.
        aliases:
          - zones
          - az
    backtrack_to:
        description:
          - The timestamp of the time to backtrack the DB cluster to in ISO 8601 format, such as "2017-07-08T18:00Z".
    backtrack_window:
        description:
          - The target backtrack window, in seconds. To disable backtracking, set this value to 0.
    backup_retention_period:
        description:
          - The number of days for which automated backups are retained (must be greater or equal to 1).
            May be used when creating a new cluster, when restoring from S3, or when modifying a cluster.
    character_set_name:
        description:
          - The character set to associate with the DB cluster.
    database_name:
        description:
          - The name for your database. If a name is not provided Amazon RDS will not create a database.
        aliases:
          - db_name
    db_cluster_identifier:
        description:
          - The DB cluster (lowercase) identifier. The identifier must contain from 1 to 63 letters, numbers, or
            hyphens and the first character must be a letter and may not end in a hyphen or contain consecutive hyphens.
        aliases:
          - cluster_id
          - id
        required: True
    db_cluster_parameter_group_name:
        description:
          - The name of the DB cluster parameter group to associate with this DB cluster.
            If this argument is omitted when creating a cluster, default.aurora5.6 is used.
    db_subnet_group_name:
        description:
          - A DB subnet group to associate with this DB cluster if not using the default.
    enable_cloudwatch_logs_exports:
        description:
          - A list of log types that need to be enabled for exporting to CloudWatch Logs.
    enable_iam_database_authentication:
        description:
          - Enable mapping of AWS Identity and Access Management (IAM) accounts to database accounts.
            If this option is omitted when creating the cluster, Amazon RDS sets this to False.
        type: bool
    engine:
        description:
          - The name of the database engine to be used for this DB cluster. This is required to create a cluster.
        choices:
          - aurora
          - aurora-mysql
          - aurora-postgresql
    engine_version:
        description:
          - The version number of the database engine to use. For Aurora MySQL that could be 5.6.10a , 5.7.12.
            Aurora PostgreSQL example, 9.6.3
    final_snapshot_identifier:
        description:
          - The DB cluster snapshot identifier of the new DB cluster snapshot created when I(skip_final_snapshot) is false.
    force_backtrack:
        description:
          - A boolean to indicate if the DB cluster should be forced to backtrack when binary logging is enabled.
            Otherwise, an error occurs when binary logging is enabled.
        type: bool
    kms_key_id:
        description:
          - The AWS KMS key identifier (the ARN, unless you are creating a cluster in the same account that owns the
            KMS key, in which case the KMS key alias may be used).
          - If I(replication_source_identifier) specifies an encrypted source Amazon RDS will use the key used toe encrypt the source.
          - If I(storage_encrypted) is true and and I(replication_source_identifier) is not provided, the default encryption key is used.
    master_user_password:
        description:
          - An 8-41 character password for the master database user. The password can contain any printable ASCII character
            except "/", """, or "@". To modify the password use I(force_password_update). Use I(apply immediately) to change
            the password immediately, otherwise it is updated during the next maintenance window.
        aliases:
          - password
    master_username:
        description:
          - The name of the master user for the DB cluster. Must be 1-16 letters or numbers and begin with a letter.
        aliases:
          - username
    new_db_cluster_identifier:
        description:
          - The new DB cluster (lowercase) identifier for the DB cluster when renaming a DB cluster. The identifier must contain
            from 1 to 63 letters, numbers, or hyphens and the first character must be a letter and may not end in a hyphen or
            contain consecutive hyphens. Use I(apply_immediately) to rename immediately, otherwise it is updated during the
            next maintenance window.
        aliases:
          - new_cluster_id
    option_group_name:
        description:
          - The option group to associate with the DB cluster.
    port:
        description:
          - The port number on which the instances in the DB cluster accept connections. If not specified, Amazon RDS
            defaults this to 3306 if the engine is aurora and 5432 if the engine is aurora-postgresql.
    preferred_backup_window:
        description:
          - The daily time range (in UTC) of at least 30 minutes, during which automated backups are created if automated backups are
            enabled using I(backup_retention_period). The option must be in the format of "hh24:mi-hh24:mi" and not conflict with
            I(preferred_maintenance_window).
        aliases:
          - backup_window
    preferred_maintenance_window:
        description:
          - The weekly time range (in UTC) of at least 30 minutes, during which system maintenance can occur. The option must
            be in the format "ddd:hh24:mi-ddd:hh24:mi" where ddd is one of Mon, Tue, Wed, Thu, Fri, Sat, Sun.
        aliases:
          - maintenance_window
    purge_cloudwatch_logs_exports:
        description:
          - Whether or not to disable Cloudwatch logs enabled for the DB cluster that are not provided in I(enable_cloudwatch_logs_exports).
            Set I(enable_cloudwatch_logs_exports) to an empty list to disable all.
        type: bool
        default: true
    purge_tags:
        description:
          - Whether or not to remove tags assigned to the DB cluster if not specified in the playbook. To remove all tags
            set I(tags) to an empty dictionary in conjunction with this.
        type: bool
        default: true
    replication_source_identifier:
        description:
          - The Amazon Resource Name (ARN) of the source DB instance or DB cluster if this DB cluster is created as a Read Replica.
        aliases:
          - replication_src_id
    restore_to_time:
        description:
          - The UTC date and time to restore the DB cluster to. Must be in the format "2015-03-07T23:45:00Z". If this is not provided while
            restoring a cluster, I(use_latest_restorable_time) must be. May not be specified if I(restore_type) is copy-on-write.
    restore_type:
        description:
          - The type of restore to be performed. If not provided, Amazon RDS uses full-copy.
        choices:
          - full-copy
          - copy-on-write
    role_arn:
        description:
          - The Amazon Resource Name (ARN) of the IAM role to associate with the Aurora DB cluster, for example
            "arn:aws:iam::123456789012:role/AuroraAccessRole"
    s3_bucket_name:
        description:
          - The name of the Amazon S3 bucket that contains the data used to create the Amazon Aurora DB cluster.
    s3_ingestion_role_arn:
        description:
          - The Amazon Resource Name (ARN) of the AWS Identity and Access Management (IAM) role that authorizes Amazon RDS to access
            the Amazon S3 bucket on your behalf.
    s3_prefix:
        description:
          - The prefix for all of the file names that contain the data used to create the Amazon Aurora DB cluster. If you do not
            specify a SourceS3Prefix value, then the Amazon Aurora DB cluster is created by using all of the files in the Amazon S3 bucket.
    skip_final_snapshot:
        description:
          - Whether a final DB cluster snapshot is created before the DB cluster is deleted. If this is false I(final_snapshot_identifier)
            must be provided.
        type: bool
        default: false
    snapshot_identifier:
        description:
          - The identifier for the DB snapshot or DB cluster snapshot to restore from. You can use either the name or the ARN to specify
            a DB cluster snapshot. However, you can use only the ARN to specify a DB snapshot.
    source_db_cluster_identifier:
        description:
          - The identifier of the source DB cluster from which to restore.
    source_engine:
        description:
          - The identifier for the database engine that was backed up to create the files stored in the Amazon S3 bucket.
        choices:
          - mysql
    source_engine_version:
        description:
          - The version of the database that the backup files were created from.
    source_region:
        description:
          - The ID of the region that contains the source for the DB cluster.
    storage_encrypted:
        description:
          - Whether the DB cluster is encrypted.
        type: bool
    tags:
        description:
          - A dictionary of key value pairs to assign the DB cluster.
    use_earliest_time_on_point_in_time_unavailable:
        description:
          - If I(backtrack_to) is set to a timestamp earlier than the earliest backtrack time, this value backtracks the DB cluster to
            the earliest possible backtrack time. Otherwise, an error occurs.
        type: bool
    use_latest_restorable_time:
        description:
          - Whether to restore the DB cluster to the latest restorable backup time. Only one of I(use_latest_restorable_time)
            and I(restore_to_time) may be provided.
        type: bool
    vpc_security_group_ids:
        description:
          - A list of EC2 VPC security groups to associate with the DB cluster.

'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.
- name: create minimal aurora cluster in default VPC and default subnet group
  rds_cluster:
    engine: aurora
    cluster_id: ansible-test-cluster

'''

RETURN = '''
allocated_storage:
  description:
    - The allocated storage size in gibibytes. Since aurora storage size is not fixed this is
      always 1 for aurora database engines
  returned: always
  type: int
  sample: 1
associated_roles:
  description:
    - A list of dictionaries of the AWS Identity and Access Management (IAM) roles that are associated
      with the DB cluster. Each dictionary contains the role_arn and the status of the role.
  returned: always
  type: list
  sample: []
availability_zones:
  description: The list of availability zones that instances in the DB cluster can be created in
  returned: always
  type: list
  sample:
  - us-east-1c
  - us-east-1a
  - us-east-1e
backup_retention_period:
  description: The number of days for which automatic DB snapshots are retained
  returned: always
  type: int
  sample: 1
cluster_create_time:
  description: The time in UTC when the DB cluster was created
  returned: always
  type: string
  sample: '2018-06-29T14:08:58.491000+00:00'
db_cluster_arn:
  description: The Amazon Resource Name (ARN) for the DB cluster
  returned: always
  type: string
  sample: arn:aws:rds:us-east-1:123456789012:cluster:rds-cluster-demo
db_cluster_identifier:
  description: The lowercase user-supplied DB cluster identifier
  returned: always
  type: string
  sample: rds-cluster-demo
db_cluster_members:
  description:
    - A list of dictionaries containing information about the instances in the cluster.
      Each dictionary contains the db_instance_identifier, is_cluster_writer (bool),
      db_cluster_parameter_group_status, and promotion_tier (int).
  returned: always
  type: list
  sample: []
db_cluster_parameter_group:
  description: The parameter group associated with the DB cluster
  returned: always
  type: string
  sample: default.aurora5.6
db_cluster_resource_id:
  description: The AWS Region-unique, immutable identifier for the DB cluster
  returned: always
  type: string
  sample: cluster-D2MEQDN3BQNXDF74K6DQJTHASU
db_subnet_group:
  description: The name of the subnet group associated with the DB Cluster
  returned: always
  type: string
  sample: default
earliest_restorable_time:
  description: The earliest time to which a database can be restored with point-in-time restore
  returned: always
  type: string
  sample: '2018-06-29T14:09:34.797000+00:00'
endpoint:
  description: The connection endpoint for the primary instance of the DB cluster
  returned: always
  type: string
  sample: rds-cluster-demo.cluster-cvlrtwiennww.us-east-1.rds.amazonaws.com
engine:
  description: The database engine of the DB cluster
  returned: always
  type: string
  sample: aurora
engine_version:
  description: The database engine version
  returned: always
  type: string
  sample: 5.6.10a
hosted_zone_id:
  description: The ID that Amazon Route 53 assigns when you create a hosted zone
  returned: always
  type: string
  sample: Z2R2ITUGPM61AM
iam_database_authentication_enabled:
  description: Whether IAM accounts may be mapped to database accounts
  returned: always
  type: bool
  sample: false
latest_restorable_time:
  description: The latest time to which a database can be restored with point-in-time restore
  returned: always
  type: string
  sample: '2018-06-29T14:09:34.797000+00:00'
master_username:
  description: The master username for the DB cluster
  returned: always
  type: string
  sample: username
multi_az:
  description: Whether the DB cluster has instances in multiple availability zones
  returned: always
  type: bool
  sample: false
port:
  description: The port that the database engine is listening on
  returned: always
  type: int
  sample: 3306
preferred_backup_window:
  description: The UTC weekly time range during which system maintenance can occur
  returned: always
  type: string
  sample: 10:18-10:48
preferred_maintenance_window:
  description: The UTC weekly time range during which system maintenance can occur
  returned: always
  type: string
  sample: tue:03:23-tue:03:53
read_replica_identifiers:
  description: A list of read replica ID strings associated with the DB cluster
  returned: always
  type: list
  sample: []
reader_endpoint:
  description: The reader endpoint for the DB cluster
  returned: always
  type: string
  sample: rds-cluster-demo.cluster-ro-cvlrtwiennww.us-east-1.rds.amazonaws.com
status:
  description: The status of the DB cluster
  returned: always
  type: string
  sample: available
storage_encrypted:
  description: Whether the DB cluster is storage encrypted
  returned: always
  type: bool
  sample: false
tags:
  description: A dictionary of key value pairs
  returned: always
  sample:
    Name: rds-cluster-demo
  type: dict
vpc_security_groups:
  description: A list of the DB cluster's security groups and their status
  returned: always
  type: complex
  contains:
    status:
      description: status of the security group
      returned: always
      type: string
      sample: active
    vpc_security_group_id:
      description: security group of the cluster
      returned: always
      type: string
      sample: sg-12345678

'''

from ansible.module_utils._text import to_text
from ansible.module_utils.aws.core import AnsibleAWSModule, is_boto3_error_code
from ansible.module_utils.aws.waiters import get_waiter
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict
from ansible.module_utils.ec2 import compare_aws_tags, boto3_tag_list_to_ansible_dict, ansible_dict_to_boto3_tag_list, camel_dict_to_snake_dict

try:
    from botocore.exceptions import ClientError, BotoCoreError, WaiterError
except ImportError:
    pass  # caught by AnsibleAWSModule


def get_add_role_options(params_dict, cluster):
    current_role_arns = [role['RoleArn'] for role in cluster.get('AssociatedRoles', [])]
    role = params_dict['RoleArn']
    if role is not None and role not in current_role_arns:
        return {'RoleArn': role, 'DBClusterIdentifier': params_dict['DBClusterIdentifier']}
    return {}


def get_backtrack_options(params_dict):
    options = ['BacktrackTo', 'DBClusterIdentifier', 'UseEarliestTimeOnPointInTimeUnavailable']
    if params_dict['BacktrackTo'] is not None:
        options = dict((k, params_dict[k]) for k in options if params_dict[k] is not None)
        if 'ForceBacktrack' in params_dict:
            options['Force'] = params_dict['ForceBacktrack']
        return options
    return {}


def get_create_options(params_dict):
    options = [
        'AvailabilityZones', 'BacktrackWindow', 'BackupRetentionPeriod', 'PreferredBackupWindow', 'CharacterSetName',
        'DBClusterIdentifier', 'DBClusterParameterGroupName', 'DBSubnetGroupName', 'DatabaseName',
        'EnableCloudwatchLogsExports', 'EnableIAMDatabaseAuthentication', 'KmsKeyId', 'Engine',
        'EngineVersion', 'PreferredMaintenanceWindow', 'MasterUserPassword', 'MasterUsername', 'OptionGroupName',
        'Port', 'ReplicationSourceIdentifier', 'SourceRegion', 'StorageEncrypted', 'Tags', 'VpcSecurityGroupIds'
    ]
    return dict((k, v) for k, v in params_dict.items() if k in options and v is not None)


def get_modify_options(params_dict, force_update_password):
    options = [
        'ApplyImmediately', 'BacktrackWindow', 'BackupRetentionPeriod', 'PreferredBackupWindow', 'EnableCloudwatchLogsExports',
        'DBClusterIdentifier', 'DBClusterParameterGroupName', 'EnableIAMDatabaseAuthentication', 'EngineVersion',
        'PreferredMaintenanceWindow', 'MasterUserPassword', 'NewDBClusterIdentifier', 'OptionGroupName', 'Port', 'VpcSecurityGroupIds'
    ]
    modify_options = dict((k, v) for k, v in params_dict.items() if k in options and v is not None)
    if not force_update_password:
        modify_options.pop('MasterUserPassword', None)
    return modify_options


def get_delete_options(params_dict):
    options = ['DBClusterIdentifier', 'FinalSnapshotIdentifier', 'SkipFinalSnapshot']
    return dict((k, params_dict[k]) for k in options if params_dict[k] is not None)


def get_restore_s3_options(params_dict):
    options = [
        'AvailabilityZones', 'BacktrackWindow', 'BackupRetentionPeriod', 'CharacterSetName', 'DBClusterIdentifier',
        'DBClusterParameterGroupName', 'DBSubnetGroupName', 'DatabaseName', 'EnableCloudwatchLogsExports',
        'EnableIAMDatabaseAuthentication', 'Engine', 'EngineVersion', 'KmsKeyId', 'MasterUserPassword',
        'MasterUsername', 'OptionGroupName', 'Port', 'PreferredBackupWindow', 'PreferredMaintenanceWindow',
        'S3BucketName', 'S3IngestionRoleArn', 'S3Prefix', 'SourceEngine', 'SourceEngineVersion', 'StorageEncrypted',
        'Tags', 'VpcSecurityGroupIds'
    ]
    return dict((k, v) for k, v in params_dict.items() if k in options and v is not None)


def get_restore_snapshot_options(params_dict):
    options = [
        'AvailabilityZones', 'BacktrackWindow', 'DBClusterIdentifier', 'DBSubnetGroupName', 'DatabaseName',
        'EnableCloudwatchLogsExports', 'EnableIAMDatabaseAuthentication', 'Engine', 'EngineVersion', 'KmsKeyId',
        'OptionGroupName', 'Port', 'SnapshotIdentifier', 'Tags', 'VpcSecurityGroupIds'
    ]
    return dict((k, v) for k, v in params_dict.items() if k in options and v is not None)


def get_restore_cluster_options(params_dict):
    options = [
        'BacktrackWindow', 'DBClusterIdentifier', 'DBSubnetGroupName', 'EnableCloudwatchLogsExports',
        'EnableIAMDatabaseAuthentication', 'KmsKeyId', 'OptionGroupName', 'Port', 'RestoreToTime', 'RestoreType',
        'SourceDBClusterIdentifier', 'Tags', 'UseLatestRestorableTime', 'VpcSecurityGroupIds'
    ]
    return dict((k, v) for k, v in params_dict.items() if k in restore_time_cluster and v is not None)


def wait_for_available(client, module, db_cluster_id):
    if not module.params['wait']:
        return
    try:
        get_waiter(client, 'cluster_available').wait(DBClusterIdentifier=db_cluster_id)
    except WaiterError as e:
        module.fail_json_aws(e, msg="Failed to wait for DB cluster {0} to reach an available state".format(db_cluster_id))
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed with an unexpected error while waiting for the DB cluster {0} to reach an "
            "available state".format(db_cluster_id))


def add_role(client, module, params):
    if not module.check_mode:
        try:
            client.add_role_to_db_cluster(**params)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Unable to add role {0} to cluster {0}".format(params['RoleArn'], params['DBClusterIdentifier']))
        wait_for_available(client, module, params['DBClusterIdentifier'])


def restore_s3_cluster(client, module, params):
    cluster = {}
    if not module.check_mode:
        try:
            cluster = client.restore_db_cluster_from_s3(**params)['DBCluster']
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Unable to create cluster {0} from S3 bucket {1}".format(
                params['DBClusterIdentifier'], params['S3BucketName']))
        wait_for_available(client, module, params['DBClusterIdentifier'])
    return cluster


def restore_snapshot_cluster(client, module, params):
    cluster = {}
    if module.check_mode:
        try:
            cluster = client.restore_db_cluster_from_snapshot(**params)['DBCluster']
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Unable to create cluster {0} from snapshot {1}".format(
                params['DBClusterIdentifier'], params['SnapshotIdentifier']))
        wait_for_available(client, module, params['DBClusterIdentifier'])
    return cluster


def restore_cluster(client, module, params):
    cluster = {}
    if not module.check_mode:
        try:
            cluster = client.restore_db_cluster_to_point_in_time(**params)['DBCluster']
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Unable to create cluster {0} from source cluster {1}".format(
                params['DBClusterIdentifier'], params['SourceDBClusterIdentifier']))
        wait_for_available(client, module, params['DBClusterIdentifier'])
    return cluster


def backtrack_cluster(client, module, params):
    if not module.check_mode:
        try:
            client.backtrack_db_cluster(**params)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Unable to backtrack cluster {0}".format(params['DBClusterIdentifier']))
        wait_for_available(client, module, params['DBClusterIdentifier'])


def promote_cluster(client, module, db_cluster_id):
    if not module.check_mode:
        try:
            client.promote_read_replica_db_cluster(DBClusterIdentifier=db_cluster_id)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Unable to promote cluster {0}".format(params['DBClusterIdentifier']))
        wait_for_available(client, module, params['DBClusterIdentifier'])


def get_cluster(client, module, db_cluster_id):
    try:
        return client.describe_db_clusters(DBClusterIdentifier=db_cluster_id)['DBClusters'][0]
    except is_boto3_error_code('DBClusterNotFoundFault'):
        return {}
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to describe DB clusters")


def create_cluster(client, module, params):
    cluster = {}
    if not module.check_mode:
        try:
            cluster = client.create_db_cluster(**params)['DBCluster']
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Failed to create DB cluster {0}".format(params['DBClusterIdentifier']))
        wait_for_available(client, module, params['DBClusterIdentifier'])
    return cluster


def modify_cluster(client, module, params):
    if module.check_mode:
        return get_cluster(client, module, params['DBClusterIdentifier'])
    try:
        cluster = client.modify_db_cluster(**params)['DBCluster']
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to modify DB cluster {0}".format(params['DBClusterIdentifier']))

    if 'NewDBClusterIdentifier' in params and params['ApplyImmediately']:
        cluster_id = params['NewDBClusterIdentifier']
    else:
        cluster_id = params['DBClusterIdentifier']
    wait_for_available(client, module, cluster_id)

    return cluster


def delete_cluster(client, module, params):
    if not module.check_mode:
        try:
            client.delete_db_cluster(**params)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Failed to delete DB cluster {0}".format(params['DBClusterIdentifier']))

        try:
            if module.params['wait']:
                get_waiter(client, 'cluster_deleted').wait(DBClusterIdentifier=params['DBClusterIdentifier'])
        except WaiterError as e:
            module.fail_json_aws(e, msg="Failed to wait for DB cluster {0} to be deleted".format(params['DBClusterIdentifier']))
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Failed with an unexpected error while waiting for the DB cluster {0} to be "
                "deleted".format(params['DBClusterIdentifier']))


def changing_cluster_options(modify_params, current_cluster, purge_cloudwatch_logs):
    changing_params = {}
    apply_immediately = modify_params.pop('ApplyImmediately')
    db_cluster_id = modify_params.pop('DBClusterIdentifier')

    enable_cloudwatch_logs_export = modify_params.pop('EnableCloudwatchLogsExports', None)
    if enable_cloudwatch_logs_export is not None:
        desired_cloudwatch_logs_configuration = {'EnableLogTypes': [], 'DisableLogTypes': []}
        provided_cloudwatch_logs = set(enable_cloudwatch_logs_export)
        current_cloudwatch_logs_export = set(current_cluster['EnabledCloudwatchLogsExports'])

        desired_cloudwatch_logs_configuration['EnableLogTypes'] = list(provided_cloudwatch_logs.difference(current_cloudwatch_logs_export))
        if purge_cloudwatch_logs:
            desired_cloudwatch_logs_configuration['DisableLogTypes'] = list(current_cloudwatch_logs_export.difference(provided_cloudwatch_logs))
        changing_params['CloudwatchLogsExportConfiguration'] = desired_cloudwatch_logs_configuration

    password = modify_params.pop('MasterUserPassword', None)
    if password:
        changing_params['MasterUserPassword'] = password

    new_cluster_id = modify_params.pop('NewDBClusterIdentifier', None)
    if new_cluster_id and new_cluster_id != current_cluster['DBClusterIdentifier']:
        changing_params['NewDBClusterIdentifier'] = new_cluster_id

    option_group = modify_params.pop('OptionGroupName', None)
    if option_group and option_group not in [g['DBClusterOptionGroupName'] for g in current_cluster['DBClusterOptionGroupMemberships']]:
        changing_params['OptionGroupName'] = option_group

    vpc_sgs = modify_params.pop('VpcSecurityGroupIds', None)
    if vpc_sgs and vpc_sgs not in [sg['VpcSecurityGroupId'] for sg in current_cluster['VpcSecurityGroups']]:
        changing_params['VpcSecurityGroupIds'] = vpc_sgs

    for param in modify_params:
        if modify_params[param] != current_cluster[param]:
            changing_params[param] = modify_params[param]

    if changing_params:
        changing_params['DBClusterIdentifier'] = db_cluster_id
        if apply_immediately is not None:
            changing_params['ApplyImmediately'] = apply_immediately

    return changing_params


def ensure_present(client, module, cluster, parameters):
    changed = False
    if not cluster:
        changed = True
        if parameters.get('Tags') is not None:
            parameters['Tags'] = ansible_dict_to_boto3_tag_list(parameters['Tags'])
        if module.params['creation_source'] is None:
            cluster = create_cluster(client, module, get_create_options(parameters))
        elif module.params['creation_source'] == 's3':
            cluster = restore_s3_cluster(client, module, get_restore_s3_options(parameters))
        elif module.params['creation_source'] == 'snapshot':
            cluster = restore_snapshot_cluster(client, module, get_restore_snapshot_options(parameters))
        else:
            cluster = restore_cluster(client, module, get_restore_cluster_options(parameters))
    else:
        if get_backtrack_options(parameters):
            changed = True
            backtrack_cluster(client, module, get_backtrack_options(parameters))
        else:
            modifiable_options = get_modify_options(parameters, force_update_password=module.params['force_update_password'])
            modify_options = changing_cluster_options(modifiable_options, cluster, module.params['purge_cloudwatch_logs_exports'])
            if modify_options:
                changed = True
                cluster = modify_cluster(client, module, modify_options)
            if module.params['tags'] is not None:
                changed |= ensure_tags(client, module, cluster, module.params['tags'], module.params['purge_tags'])

    add_role_params = get_add_role_options(parameters, cluster)
    if add_role_params:
        changed = True
        add_role(client, module, add_role_params)

    if module.params['promote'] and cluster.get('ReplicationSourceIdentifier'):
        changed = True
        promote_cluster(client, module, module.params['db_cluster_identifier'])

    return changed


def ensure_tags(client, module, cluster, tags, purge_tags):
    existing_tags = get_tags(client, module, cluster['DBClusterArn'])
    tags_to_add, tags_to_remove = compare_aws_tags(existing_tags, tags, purge_tags)
    changed = bool(tags_to_add or tags_to_remove)

    if not module.check_mode and changed:
        if tags_to_add:
            try:
                client.add_tags_to_resource(
                    ResourceName=cluster['DBClusterArn'],
                    Tags=ansible_dict_to_boto3_tag_list(tags_to_add)
                )
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg="Failed to add tags {0} to DB cluster {1}".format(
                    tags_to_add, cluster['DBClusterIdentifier']))
        if tags_to_remove:
            try:
                client.remove_tags_from_resource(ResourceName=cluster['DBClusterArn'], TagKeys=tags_to_remove)
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg="Failed to remove tags {0} from DB cluster {1}".format(tags_to_remove,
                    cluster['DBClusterIdentifier']))
        get_waiter(client, 'cluster_available').wait(DBClusterIdentifier=cluster['DBClusterIdentifier'])

    return changed


def get_tags(client, module, cluster_arn):
    try:
        return boto3_tag_list_to_ansible_dict(
            client.list_tags_for_resource(ResourceName=cluster_arn)['TagList']
        )
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Unable to describe tags")


def arg_spec_to_rds_params(options_dict):
    tags = options_dict.pop('tags')
    camel_options = snake_dict_to_camel_dict(options_dict, capitalize_first=True)
    for key, value in camel_options.items():
        if 'Db' in key:
            del camel_options[key]
            key = key.replace('Db', 'DB')
            camel_options[key] = value
        if 'Iam' in key:
            del camel_options[key]
            key = key.replace('Iam', 'IAM')
            camel_options[key] = value
    camel_options['Tags'] = tags
    return camel_options


def main():
    arg_spec = dict(
        state=dict(choices=['present', 'absent'], default='present'),
        creation_source=dict(choices=['snapshot', 's3', 'cluster']),
        force_update_password=dict(type='bool', default=False),
        promote=dict(type='bool', default=False),
        purge_cloudwatch_logs_exports=dict(type='bool', default=True),
        purge_tags=dict(type='bool', default=True),
        wait=dict(type='bool', default=True),
    )

    parameter_options = dict(
        apply_immediately=dict(type='bool', default=False),
        availability_zones=dict(type='list', aliases=['zones', 'az']),
        backtrack_to=dict(),
        backtrack_window=dict(type='int'),
        backup_retention_period=dict(type='int'),
        character_set_name=dict(),
        database_name=dict(aliases=['db_name']),
        db_cluster_identifier=dict(required=True, aliases=['cluster_id', 'id']),
        db_cluster_parameter_group_name=dict(),
        db_subnet_group_name=dict(),
        enable_cloudwatch_logs_exports=dict(type='list'),
        enable_iam_database_authentication=dict(type='bool'),
        engine=dict(choices=["aurora", "aurora-mysql", "aurora-postgresql"]),
        engine_version=dict(),
        final_snapshot_identifier=dict(),
        force_backtrack=dict(type='bool'),
        kms_key_id=dict(),
        master_user_password=dict(aliases=['password'], no_log=True),
        master_username=dict(aliases=['username']),
        new_db_cluster_identifier=dict(aliases=['new_cluster_id']),
        option_group_name=dict(),
        port=dict(type='int'),
        preferred_backup_window=dict(aliases=['backup_window']),
        preferred_maintenance_window=dict(aliases=['maintenance_window']),
        replication_source_identifier=dict(aliases=['replication_src_id']),
        restore_to_time=dict(),
        restore_type=dict(choices=['full-copy', 'copy-on-write']),
        role_arn=dict(),
        s3_bucket_name=dict(),
        s3_ingestion_role_arn=dict(),
        s3_prefix=dict(),
        skip_final_snapshot=dict(type='bool', default=False),
        snapshot_identifier=dict(),
        source_db_cluster_identifier=dict(),
        source_engine=dict(choices=['mysql']),
        source_engine_version=dict(),
        source_region=dict(),
        storage_encrypted=dict(),
        tags=dict(type='dict'),
        use_earliest_time_on_point_in_time_unavailable=dict(type='bool'),
        use_latest_restorable_time=dict(type='bool'),
        vpc_security_group_ids=dict(type='list')

    )
    arg_spec.update(parameter_options)

    module = AnsibleAWSModule(
        argument_spec=arg_spec,
        required_if=[
            ('creation_source', 'snapshot', ('snapshot_identifier', 'engine')),
            ('creation_source', 's3', (
                's3_bucket_name', 'engine', 'master_username', 'master_user_password',
                'source_engine', 'source_engine_version', 's3_ingestion_role_arn')
            ),
        ],
        mutually_exclusive=[
            ('s3_bucket_name', 'source_db_cluster_identifier', 'snapshot_identifier'),
            ('use_latest_restorable_time', 'restore_to_time'),
        ],
        supports_check_mode=True
    )

    client = module.client('rds')

    module.params['db_cluster_identifier'] = module.params['db_cluster_identifier'].lower()
    cluster = get_cluster(client, module, module.params['db_cluster_identifier'])

    if module.params['new_db_cluster_identifier']:
        module.params['new_db_cluster_identifier'] = module.params['new_db_cluster_identifier'].lower()

        if get_cluster(client, module, module.params['new_db_cluster_identifier']):
            module.fail_json("A new cluster ID '{0}' was provided but it already exists".format(module.params['new_db_cluster_identifier']))
        if not cluster:
            module.fail_json("A new cluster ID '{0}' was provided but the cluster to be renamed does not exist".format(module.params['new_db_cluster_identifier']))

    if module.params['state'] == 'absent' and module.params['skip_final_snapshot'] is False and module.params['final_snapshot_identifier'] is None:
        module.fail_json(msg='skip_final_snapshot is False but all of the following are missing: final_snapshot_identifier')

    parameters = arg_spec_to_rds_params(
        dict((k, module.params[k]) for k in module.params if k in parameter_options)
    )

    changed = False
    if module.params['state'] == 'present':
        changed |= ensure_present(client, module, cluster, parameters)
    elif module.params['state'] == 'absent' and cluster:
        changed = True
        delete_cluster(client, module, get_delete_options(parameters))

    if not module.check_mode and module.params['new_db_cluster_identifier'] and module.params['apply_immediately']:
        cluster_id = module.params['new_db_cluster_identifier']
    else:
        cluster_id = module.params['db_cluster_identifier']
    result = camel_dict_to_snake_dict(get_cluster(client, module, cluster_id))
    if result:
        result['tags'] = get_tags(client, module, result['db_cluster_arn'])

    module.exit_json(changed=changed, **result)


if __name__ == '__main__':
    main()
