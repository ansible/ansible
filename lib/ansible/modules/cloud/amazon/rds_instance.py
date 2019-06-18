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
module: rds_instance
version_added: "2.7"
short_description: Manage RDS instances
description:
    - Create, modify, and delete RDS instances.

requirements:
    - botocore
    - boto3 >= 1.5.0
extends_documentation_fragment:
    - aws
    - ec2
author:
    - Sloane Hertel (@s-hertel)

options:
  # General module options
    state:
        description:
          - Whether the snapshot should exist or not. I(rebooted) is not idempotent and will leave the DB instance in a running state
            and start it prior to rebooting if it was stopped. I(present) will leave the DB instance in the current running/stopped state,
            (running if creating the DB instance).
          - I(state=running) and I(state=started) are synonyms, as are I(state=rebooted) and I(state=restarted). Note - rebooting the instance
            is not idempotent.
        choices: ['present', 'absent', 'terminated', 'running', 'started', 'stopped', 'rebooted', 'restarted']
        default: 'present'
    creation_source:
        description: Which source to use if restoring from a template (an existing instance, S3 bucket, or snapshot).
        choices: ['snapshot', 's3', 'instance']
    force_update_password:
        description:
          - Set to True to update your cluster password with I(master_user_password). Since comparing passwords to determine
            if it needs to be updated is not possible this is set to False by default to allow idempotence.
        type: bool
        default: False
    purge_cloudwatch_logs_exports:
        description: Set to False to retain any enabled cloudwatch logs that aren't specified in the task and are associated with the instance.
        type: bool
        default: True
    purge_tags:
        description: Set to False to retain any tags that aren't specified in task and are associated with the instance.
        type: bool
        default: True
    read_replica:
        description:
          - Set to False to promote a read replica cluster or true to create one. When creating a read replica C(creation_source) should
            be set to 'instance' or not provided. C(source_db_instance_identifier) must be provided with this option.
        type: bool
    wait:
        description:
          - Whether to wait for the cluster to be available, stopped, or deleted. At a later time a wait_timeout option may be added.
            Following each API call to create/modify/delete the instance a waiter is used with a 60 second delay 30 times until the instance reaches
            the expected state (available/stopped/deleted). The total task time may also be influenced by AWSRetry which helps stabilize if the
            instance is in an invalid state to operate on to begin with (such as if you try to stop it when it is in the process of rebooting).
            If setting this to False task retries and delays may make your playbook execution better handle timeouts for major modifications.
        type: bool
        default: True

    # Options that have a corresponding boto3 parameter
    allocated_storage:
        description:
          - The amount of storage (in gibibytes) to allocate for the DB instance.
    allow_major_version_upgrade:
        description:
          - Whether to allow major version upgrades.
        type: bool
    apply_immediately:
        description:
          - A value that specifies whether modifying a cluster with I(new_db_instance_identifier) and I(master_user_password)
            should be applied as soon as possible, regardless of the I(preferred_maintenance_window) setting. If false, changes
            are applied during the next maintenance window.
        type: bool
        default: False
    auto_minor_version_upgrade:
        description:
          - Whether minor version upgrades are applied automatically to the DB instance during the maintenance window.
        type: bool
    availability_zone:
        description:
          - A list of EC2 Availability Zones that instances in the DB cluster can be created in.
            May be used when creating a cluster or when restoring from S3 or a snapshot. Mutually exclusive with I(multi_az).
        aliases:
          - az
          - zone
    backup_retention_period:
        description:
          - The number of days for which automated backups are retained (must be greater or equal to 1).
            May be used when creating a new cluster, when restoring from S3, or when modifying a cluster.
    ca_certificate_identifier:
        description:
          - The identifier of the CA certificate for the DB instance.
    character_set_name:
        description:
          - The character set to associate with the DB cluster.
    copy_tags_to_snapshot:
        description:
          - Whether or not to copy all tags from the DB instance to snapshots of the instance. When initially creating
            a DB instance the RDS API defaults this to false if unspecified.
        type: bool
    db_cluster_identifier:
        description:
          - The DB cluster (lowercase) identifier to add the aurora DB instance to. The identifier must contain from 1 to
            63 letters, numbers, or hyphens and the first character must be a letter and may not end in a hyphen or
            contain consecutive hyphens.
        aliases:
          - cluster_id
    db_instance_class:
        description:
          - The compute and memory capacity of the DB instance, for example db.t2.micro.
        aliases:
          - class
          - instance_type
    db_instance_identifier:
        description:
          - The DB instance (lowercase) identifier. The identifier must contain from 1 to 63 letters, numbers, or
            hyphens and the first character must be a letter and may not end in a hyphen or contain consecutive hyphens.
        aliases:
          - instance_id
          - id
        required: True
    db_name:
        description:
          - The name for your database. If a name is not provided Amazon RDS will not create a database.
    db_parameter_group_name:
        description:
          - The name of the DB parameter group to associate with this DB instance. When creating the DB instance if this
            argument is omitted the default DBParameterGroup for the specified engine is used.
    db_security_groups:
        description:
          - (EC2-Classic platform) A list of DB security groups to associate with this DB instance.
        type: list
    db_snapshot_identifier:
        description:
          - The identifier for the DB snapshot to restore from if using I(creation_source=snapshot).
    db_subnet_group_name:
        description:
          - The DB subnet group name to use for the DB instance.
        aliases:
          - subnet_group
    domain:
        description:
          - The Active Directory Domain to restore the instance in.
    domain_iam_role_name:
        description:
          - The name of the IAM role to be used when making API calls to the Directory Service.
    enable_cloudwatch_logs_exports:
        description:
          - A list of log types that need to be enabled for exporting to CloudWatch Logs.
        aliases:
          - cloudwatch_log_exports
        type: list
    enable_iam_database_authentication:
        description:
          - Enable mapping of AWS Identity and Access Management (IAM) accounts to database accounts.
            If this option is omitted when creating the cluster, Amazon RDS sets this to False.
        type: bool
    enable_performance_insights:
        description:
          - Whether to enable Performance Insights for the DB instance.
        type: bool
    engine:
        description:
          - The name of the database engine to be used for this DB instance. This is required to create an instance.
            Valid choices are aurora | aurora-mysql | aurora-postgresql | mariadb | mysql | oracle-ee | oracle-se |
            oracle-se1 | oracle-se2 | postgres | sqlserver-ee | sqlserver-ex | sqlserver-se | sqlserver-web
    engine_version:
        description:
          - The version number of the database engine to use. For Aurora MySQL that could be 5.6.10a , 5.7.12.
            Aurora PostgreSQL example, 9.6.3
    final_db_snapshot_identifier:
        description:
          - The DB instance snapshot identifier of the new DB instance snapshot created when I(skip_final_snapshot) is false.
        aliases:
          - final_snapshot_identifier
    force_failover:
        description:
          - Set to true to conduct the reboot through a MultiAZ failover.
        type: bool
    iops:
        description:
          - The Provisioned IOPS (I/O operations per second) value. Is only set when using I(storage_type) is set to io1.
        type: int
    kms_key_id:
        description:
          - The ARN of the AWS KMS key identifier for an encrypted DB instance. If you are creating a DB instance with the
            same AWS account that owns the KMS encryption key used to encrypt the new DB instance, then you can use the KMS key
            alias instead of the ARN for the KM encryption key.
          - If I(storage_encrypted) is true and and this option is not provided, the default encryption key is used.
    license_model:
        description:
          - The license model for the DB instance.
        choices:
          - license-included
          - bring-your-own-license
          - general-public-license
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
    monitoring_interval:
        description:
          - The interval, in seconds, when Enhanced Monitoring metrics are collected for the DB instance. To disable collecting
            metrics, specify 0. Amazon RDS defaults this to 0 if omitted when initially creating a DB instance.
    monitoring_role_arn:
        description:
          - The ARN for the IAM role that permits RDS to send enhanced monitoring metrics to Amazon CloudWatch Logs.
    multi_az:
        description:
          - Specifies if the DB instance is a Multi-AZ deployment. Mutually exclusive with I(availability_zone).
        type: bool
    new_db_instance_identifier:
        description:
          - The new DB cluster (lowercase) identifier for the DB cluster when renaming a DB instance. The identifier must contain
            from 1 to 63 letters, numbers, or hyphens and the first character must be a letter and may not end in a hyphen or
            contain consecutive hyphens. Use I(apply_immediately) to rename immediately, otherwise it is updated during the
            next maintenance window.
        aliases:
          - new_instance_id
          - new_id
    option_group_name:
        description:
          - The option group to associate with the DB instance.
    performance_insights_kms_key_id:
        description:
          - The AWS KMS key identifier (ARN, name, or alias) for encryption of Performance Insights data.
    performance_insights_retention_period:
        description:
          - The amount of time, in days, to retain Performance Insights data. Valid values are 7 or 731.
    port:
        description:
          - The port number on which the instances accept connections.
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
    processor_features:
        description:
          - A dictionary of Name, Value pairs to indicate the number of CPU cores and the number of threads per core for the
            DB instance class of the DB instance. Names are threadsPerCore and coreCount.
            Set this option to an empty dictionary to use the default processor features.
        suboptions:
          threadsPerCore:
            description: The number of threads per core
          coreCount:
            description: The number of CPU cores
    promotion_tier:
        description:
          - An integer that specifies the order in which an Aurora Replica is promoted to the primary instance after a failure of
            the existing primary instance.
    publicly_accessible:
        description:
          - Specifies the accessibility options for the DB instance. A value of true specifies an Internet-facing instance with
            a publicly resolvable DNS name, which resolves to a public IP address. A value of false specifies an internal
            instance with a DNS name that resolves to a private IP address.
        type: bool
    restore_time:
        description:
          - If using I(creation_source=instance) this indicates the UTC date and time to restore from the source instance.
            For example, "2009-09-07T23:45:00Z". May alternatively set c(use_latest_restore_time) to True.
    s3_bucket_name:
        description:
          - The name of the Amazon S3 bucket that contains the data used to create the Amazon DB instance.
    s3_ingestion_role_arn:
        description:
          - The Amazon Resource Name (ARN) of the AWS Identity and Access Management (IAM) role that authorizes Amazon RDS to access
            the Amazon S3 bucket on your behalf.
    s3_prefix:
        description:
          - The prefix for all of the file names that contain the data used to create the Amazon DB instance. If you do not
            specify a SourceS3Prefix value, then the Amazon DB instance is created by using all of the files in the Amazon S3 bucket.
    skip_final_snapshot:
        description:
          - Whether a final DB cluster snapshot is created before the DB cluster is deleted. If this is false I(final_db_snapshot_identifier)
            must be provided.
        type: bool
        default: false
    snapshot_identifier:
        description:
          - The ARN of the DB snapshot to restore from when using I(creation_source=snapshot).
    source_db_instance_identifier:
        description:
          - The identifier or ARN of the source DB instance from which to restore when creating a read replica or spinning up a point-in-time
            DB instance using I(creation_source=instance). If the source DB is not in the same region this should be an ARN.
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
          - The region of the DB instance from which the replica is created.
    storage_encrypted:
        description:
          - Whether the DB instance is encrypted.
        type: bool
    storage_type:
        description:
          - The storage type to be associated with the DB instance. I(storage_type) does not apply to Aurora DB instances.
        choices:
          - standard
          - gp2
          - io1
    tags:
        description:
          - A dictionary of key value pairs to assign the DB cluster.
    tde_credential_arn:
        description:
          - The ARN from the key store with which to associate the instance for Transparent Data Encryption. This is
            supported by Oracle or SQL Server DB instances and may be used in conjunction with C(storage_encrypted)
            though it might slightly affect the performance of your database.
        aliases:
          - transparent_data_encryption_arn
    tde_credential_password:
        description:
          - The password for the given ARN from the key store in order to access the device.
        aliases:
          - transparent_data_encryption_password
    timezone:
        description:
          - The time zone of the DB instance.
    use_latest_restorable_time:
        description:
          - Whether to restore the DB instance to the latest restorable backup time. Only one of I(use_latest_restorable_time)
            and I(restore_to_time) may be provided.
        type: bool
        aliases:
          - restore_from_latest
    vpc_security_group_ids:
        description:
          - A list of EC2 VPC security groups to associate with the DB cluster.
        type: list
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.
- name: create minimal aurora instance in default VPC and default subnet group
  rds_instance:
    engine: aurora
    db_instance_identifier: ansible-test-aurora-db-instance
    instance_type: db.t2.small
    password: "{{ password }}"
    username: "{{ username }}"
    cluster_id: ansible-test-cluster  # This cluster must exist - see rds_cluster to manage it

- name: Create a DB instance using the default AWS KMS encryption key
  rds_instance:
    id: test-encrypted-db
    state: present
    engine: mariadb
    storage_encrypted: True
    db_instance_class: db.t2.medium
    username: "{{ username }}"
    password: "{{ password }}"
    allocated_storage: "{{ allocated_storage }}"

- name: remove the DB instance without a final snapshot
  rds_instance:
    id: "{{ instance_id }}"
    state: absent
    skip_final_snapshot: True

- name: remove the DB instance with a final snapshot
  rds_instance:
    id: "{{ instance_id }}"
    state: absent
    final_snapshot_identifier: "{{ snapshot_id }}"
'''

RETURN = '''
allocated_storage:
  description: The allocated storage size in gibibytes. This is always 1 for aurora database engines.
  returned: always
  type: int
  sample: 20
auto_minor_version_upgrade:
  description: Whether minor engine upgrades are applied automatically to the DB instance during the maintenance window.
  returned: always
  type: bool
  sample: true
availability_zone:
  description: The availability zone for the DB instance.
  returned: always
  type: str
  sample: us-east-1f
backup_retention_period:
  description: The number of days for which automated backups are retained.
  returned: always
  type: int
  sample: 1
ca_certificate_identifier:
  description: The identifier of the CA certificate for the DB instance.
  returned: always
  type: str
  sample: rds-ca-2015
copy_tags_to_snapshot:
  description: Whether tags are copied from the DB instance to snapshots of the DB instance.
  returned: always
  type: bool
  sample: false
db_instance_arn:
  description: The Amazon Resource Name (ARN) for the DB instance.
  returned: always
  type: str
  sample: arn:aws:rds:us-east-1:123456789012:db:ansible-test
db_instance_class:
  description: The name of the compute and memory capacity class of the DB instance.
  returned: always
  type: str
  sample: db.m4.large
db_instance_identifier:
  description: The identifier of the DB instance
  returned: always
  type: str
  sample: ansible-test
db_instance_port:
  description: The port that the DB instance listens on.
  returned: always
  type: int
  sample: 0
db_instance_status:
  description: The current state of this database.
  returned: always
  type: str
  sample: stopped
db_parameter_groups:
  description: The list of DB parameter groups applied to this DB instance.
  returned: always
  type: complex
  contains:
    db_parameter_group_name:
      description: The name of the DP parameter group.
      returned: always
      type: str
      sample: default.mariadb10.0
    parameter_apply_status:
      description: The status of parameter updates.
      returned: always
      type: str
      sample: in-sync
db_security_groups:
  description: A list of DB security groups associated with this DB instance.
  returned: always
  type: list
  sample: []
db_subnet_group:
  description: The subnet group associated with the DB instance.
  returned: always
  type: complex
  contains:
    db_subnet_group_description:
      description: The description of the DB subnet group.
      returned: always
      type: str
      sample: default
    db_subnet_group_name:
      description: The name of the DB subnet group.
      returned: always
      type: str
      sample: default
    subnet_group_status:
      description: The status of the DB subnet group.
      returned: always
      type: str
      sample: Complete
    subnets:
      description: A list of Subnet elements.
      returned: always
      type: complex
      contains:
        subnet_availability_zone:
          description: The availability zone of the subnet.
          returned: always
          type: complex
          contains:
            name:
              description: The name of the Availability Zone.
              returned: always
              type: str
              sample: us-east-1c
        subnet_identifier:
          description: The ID of the subnet.
          returned: always
          type: str
          sample: subnet-12345678
        subnet_status:
          description: The status of the subnet.
          returned: always
          type: str
          sample: Active
    vpc_id:
      description: The VpcId of the DB subnet group.
      returned: always
      type: str
      sample: vpc-12345678
dbi_resource_id:
  description: The AWS Region-unique, immutable identifier for the DB instance.
  returned: always
  type: str
  sample: db-UHV3QRNWX4KB6GALCIGRML6QFA
domain_memberships:
  description: The Active Directory Domain membership records associated with the DB instance.
  returned: always
  type: list
  sample: []
endpoint:
  description: The connection endpoint.
  returned: always
  type: complex
  contains:
    address:
      description: The DNS address of the DB instance.
      returned: always
      type: str
      sample: ansible-test.cvlrtwiennww.us-east-1.rds.amazonaws.com
    hosted_zone_id:
      description: The ID that Amazon Route 53 assigns when you create a hosted zone.
      returned: always
      type: str
      sample: ZTR2ITUGPA61AM
    port:
      description: The port that the database engine is listening on.
      returned: always
      type: int
      sample: 3306
engine:
  description: The database engine version.
  returned: always
  type: str
  sample: mariadb
engine_version:
  description: The database engine version.
  returned: always
  type: str
  sample: 10.0.35
iam_database_authentication_enabled:
  description: Whether mapping of AWS Identity and Access Management (IAM) accounts to database accounts is enabled.
  returned: always
  type: bool
  sample: false
instance_create_time:
  description: The date and time the DB instance was created.
  returned: always
  type: str
  sample: '2018-07-04T16:48:35.332000+00:00'
kms_key_id:
  description: The AWS KMS key identifier for the encrypted DB instance when storage_encrypted is true.
  returned: When storage_encrypted is true
  type: str
  sample: arn:aws:kms:us-east-1:123456789012:key/70c45553-ad2e-4a85-9f14-cfeb47555c33
latest_restorable_time:
  description: The latest time to which a database can be restored with point-in-time restore.
  returned: always
  type: str
  sample: '2018-07-04T16:50:50.642000+00:00'
license_model:
  description: The License model information for this DB instance.
  returned: always
  type: str
  sample: general-public-license
master_username:
  description: The master username for the DB instance.
  returned: always
  type: str
  sample: test
monitoring_interval:
  description:
    - The interval, in seconds, between points when Enhanced Monitoring metrics are collected for the DB instance.
      0 means collecting Enhanced Monitoring metrics is disabled.
  returned: always
  type: int
  sample: 0
multi_az:
  description: Whether the DB instance is a Multi-AZ deployment.
  returned: always
  type: bool
  sample: false
option_group_memberships:
  description: The list of option group memberships for this DB instance.
  returned: always
  type: complex
  contains:
    option_group_name:
      description: The name of the option group that the instance belongs to.
      returned: always
      type: str
      sample: default:mariadb-10-0
    status:
      description: The status of the DB instance's option group membership.
      returned: always
      type: str
      sample: in-sync
pending_modified_values:
  description: The changes to the DB instance that are pending.
  returned: always
  type: complex
  contains: {}
performance_insights_enabled:
  description: True if Performance Insights is enabled for the DB instance, and otherwise false.
  returned: always
  type: bool
  sample: false
preferred_backup_window:
  description: The daily time range during which automated backups are created if automated backups are enabled.
  returned: always
  type: str
  sample: 07:01-07:31
preferred_maintenance_window:
  description: The weekly time range (in UTC) during which system maintenance can occur.
  returned: always
  type: str
  sample: sun:09:31-sun:10:01
publicly_accessible:
  description:
    - True for an Internet-facing instance with a publicly resolvable DNS name, False to indicate an
      internal instance with a DNS name that resolves to a private IP address.
  returned: always
  type: bool
  sample: true
read_replica_db_instance_identifiers:
  description: Identifiers of the Read Replicas associated with this DB instance.
  returned: always
  type: list
  sample: []
storage_encrypted:
  description: Whether the DB instance is encrypted.
  returned: always
  type: bool
  sample: false
storage_type:
  description: The storage type to be associated with the DB instance.
  returned: always
  type: str
  sample: standard
tags:
  description: A dictionary of tags associated with the DB instance.
  returned: always
  type: complex
  contains: {}
vpc_security_groups:
  description: A list of VPC security group elements that the DB instance belongs to.
  returned: always
  type: complex
  contains:
    status:
      description: The status of the VPC security group.
      returned: always
      type: str
      sample: active
    vpc_security_group_id:
      description: The name of the VPC security group.
      returned: always
      type: str
      sample: sg-12345678
'''

from ansible.module_utils._text import to_text
from ansible.module_utils.aws.core import AnsibleAWSModule, is_boto3_error_code, get_boto3_client_method_parameters
from ansible.module_utils.aws.rds import ensure_tags, arg_spec_to_rds_params, call_method, get_rds_method_attribute, get_tags, get_final_identifier
from ansible.module_utils.aws.waiters import get_waiter
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.ec2 import ansible_dict_to_boto3_tag_list, AWSRetry
from ansible.module_utils.six import string_types

from time import sleep

try:
    from botocore.exceptions import ClientError, BotoCoreError, WaiterError
except ImportError:
    pass  # caught by AnsibleAWSModule


def get_rds_method_attribute_name(instance, state, creation_source, read_replica):
    method_name = None
    if state == 'absent' or state == 'terminated':
        if instance and instance['DBInstanceStatus'] not in ['deleting', 'deleted']:
            method_name = 'delete_db_instance'
    else:
        if instance:
            method_name = 'modify_db_instance'
        elif read_replica is True:
            method_name = 'create_db_instance_read_replica'
        elif creation_source == 'snapshot':
            method_name = 'restore_db_instance_from_db_snapshot'
        elif creation_source == 's3':
            method_name = 'restore_db_instance_from_s3'
        elif creation_source == 'instance':
            method_name = 'restore_db_instance_to_point_in_time'
        else:
            method_name = 'create_db_instance'
    return method_name


def get_instance(client, module, db_instance_id):
    try:
        for i in range(3):
            try:
                instance = client.describe_db_instances(DBInstanceIdentifier=db_instance_id)['DBInstances'][0]
                instance['Tags'] = get_tags(client, module, instance['DBInstanceArn'])
                if instance.get('ProcessorFeatures'):
                    instance['ProcessorFeatures'] = dict((feature['Name'], feature['Value']) for feature in instance['ProcessorFeatures'])
                if instance.get('PendingModifiedValues', {}).get('ProcessorFeatures'):
                    instance['PendingModifiedValues']['ProcessorFeatures'] = dict(
                        (feature['Name'], feature['Value'])
                        for feature in instance['PendingModifiedValues']['ProcessorFeatures']
                    )
                break
            except is_boto3_error_code('DBInstanceNotFound'):
                sleep(3)
        else:
            instance = {}
    except (BotoCoreError, ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg='Failed to describe DB instances')
    return instance


def get_final_snapshot(client, module, snapshot_identifier):
    try:
        snapshots = AWSRetry.jittered_backoff()(client.describe_db_snapshots)(DBSnapshotIdentifier=snapshot_identifier)
        if len(snapshots.get('DBSnapshots', [])) == 1:
            return snapshots['DBSnapshots'][0]
        return {}
    except is_boto3_error_code('DBSnapshotNotFound') as e:  # May not be using wait: True
        return {}
    except (BotoCoreError, ClientError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, msg='Failed to retrieve information about the final snapshot')


def get_parameters(client, module, parameters, method_name):
    if method_name == 'restore_db_instance_to_point_in_time':
        parameters['TargetDBInstanceIdentifier'] = module.params['db_instance_identifier']

    required_options = get_boto3_client_method_parameters(client, method_name, required=True)
    if any([parameters.get(k) is None for k in required_options]):
        module.fail_json(msg='To {0} requires the parameters: {1}'.format(
            get_rds_method_attribute(method_name, module).operation_description, required_options))
    options = get_boto3_client_method_parameters(client, method_name)
    parameters = dict((k, v) for k, v in parameters.items() if k in options and v is not None)

    if parameters.get('ProcessorFeatures') is not None:
        parameters['ProcessorFeatures'] = [{'Name': k, 'Value': to_text(v)} for k, v in parameters['ProcessorFeatures'].items()]

    # If this parameter is an empty list it can only be used with modify_db_instance (as the parameter UseDefaultProcessorFeatures)
    if parameters.get('ProcessorFeatures') == [] and not method_name == 'modify_db_instance':
        parameters.pop('ProcessorFeatures')

    if method_name == 'create_db_instance' and parameters.get('Tags'):
        parameters['Tags'] = ansible_dict_to_boto3_tag_list(parameters['Tags'])
    if method_name == 'modify_db_instance':
        parameters = get_options_with_changing_values(client, module, parameters)

    return parameters


def get_options_with_changing_values(client, module, parameters):
    instance_id = module.params['db_instance_identifier']
    purge_cloudwatch_logs = module.params['purge_cloudwatch_logs_exports']
    force_update_password = module.params['force_update_password']
    port = module.params['port']
    apply_immediately = parameters.pop('ApplyImmediately', None)
    cloudwatch_logs_enabled = module.params['enable_cloudwatch_logs_exports']

    if port:
        parameters['DBPortNumber'] = port
    if not force_update_password:
        parameters.pop('MasterUserPassword', None)
    if cloudwatch_logs_enabled:
        parameters['CloudwatchLogsExportConfiguration'] = cloudwatch_logs_enabled
    if not module.params['storage_type']:
        parameters.pop('Iops', None)

    instance = get_instance(client, module, instance_id)
    updated_parameters = get_changing_options_with_inconsistent_keys(parameters, instance, purge_cloudwatch_logs)
    updated_parameters.update(get_changing_options_with_consistent_keys(parameters, instance))
    parameters = updated_parameters

    if parameters.get('NewDBInstanceIdentifier') and instance.get('PendingModifiedValues', {}).get('DBInstanceIdentifier'):
        if parameters['NewDBInstanceIdentifier'] == instance['PendingModifiedValues']['DBInstanceIdentifier'] and not apply_immediately:
            parameters.pop('NewDBInstanceIdentifier')

    if parameters:
        parameters['DBInstanceIdentifier'] = instance_id
        if apply_immediately is not None:
            parameters['ApplyImmediately'] = apply_immediately

    return parameters


def get_current_attributes_with_inconsistent_keys(instance):
    options = {}
    if instance.get('PendingModifiedValues', {}).get('PendingCloudwatchLogsExports', {}).get('LogTypesToEnable', []):
        current_enabled = instance['PendingModifiedValues']['PendingCloudwatchLogsExports']['LogTypesToEnable']
        current_disabled = instance['PendingModifiedValues']['PendingCloudwatchLogsExports']['LogTypesToDisable']
        options['CloudwatchLogsExportConfiguration'] = {'LogTypesToEnable': current_enabled, 'LogTypesToDisable': current_disabled}
    else:
        options['CloudwatchLogsExportConfiguration'] = {'LogTypesToEnable': instance.get('EnabledCloudwatchLogsExports', []), 'LogTypesToDisable': []}
    if instance.get('PendingModifiedValues', {}).get('Port'):
        options['DBPortNumber'] = instance['PendingModifiedValues']['Port']
    else:
        options['DBPortNumber'] = instance['Endpoint']['Port']
    if instance.get('PendingModifiedValues', {}).get('DBSubnetGroupName'):
        options['DBSubnetGroupName'] = instance['PendingModifiedValues']['DBSubnetGroupName']
    else:
        options['DBSubnetGroupName'] = instance['DBSubnetGroup']['DBSubnetGroupName']
    if instance.get('PendingModifiedValues', {}).get('ProcessorFeatures'):
        options['ProcessorFeatures'] = instance['PendingModifiedValues']['ProcessorFeatures']
    else:
        options['ProcessorFeatures'] = instance.get('ProcessorFeatures', {})
    options['OptionGroupName'] = [g['OptionGroupName'] for g in instance['OptionGroupMemberships']]
    options['DBSecurityGroups'] = [sg['DBSecurityGroupName'] for sg in instance['DBSecurityGroups'] if sg['Status'] in ['adding', 'active']]
    options['VpcSecurityGroupIds'] = [sg['VpcSecurityGroupId'] for sg in instance['VpcSecurityGroups'] if sg['Status'] in ['adding', 'active']]
    options['DBParameterGroupName'] = [parameter_group['DBParameterGroupName'] for parameter_group in instance['DBParameterGroups']]
    options['AllowMajorVersionUpgrade'] = None
    options['EnableIAMDatabaseAuthentication'] = instance['IAMDatabaseAuthenticationEnabled']
    # PerformanceInsightsEnabled is not returned on older RDS instances it seems
    options['EnablePerformanceInsights'] = instance.get('PerformanceInsightsEnabled', False)
    options['MasterUserPassword'] = None
    options['NewDBInstanceIdentifier'] = instance['DBInstanceIdentifier']

    return options


def get_changing_options_with_inconsistent_keys(modify_params, instance, purge_cloudwatch_logs):
    changing_params = {}
    current_options = get_current_attributes_with_inconsistent_keys(instance)

    for option in current_options:
        current_option = current_options[option]
        desired_option = modify_params.pop(option, None)
        if desired_option is None:
            continue

        # TODO: allow other purge_option module parameters rather than just checking for things to add
        if isinstance(current_option, list):
            if isinstance(desired_option, list):
                if set(desired_option) <= set(current_option):
                    continue
            elif isinstance(desired_option, string_types):
                if desired_option in current_option:
                    continue

        if current_option == desired_option:
            continue

        if option == 'ProcessorFeatures' and desired_option == []:
            changing_params['UseDefaultProcessorFeatures'] = True
        elif option == 'CloudwatchLogsExportConfiguration':
            current_option = set(current_option.get('LogTypesToEnable', []))
            desired_option = set(desired_option)
            format_option = {'EnableLogTypes': [], 'DisableLogTypes': []}
            format_option['EnableLogTypes'] = list(desired_option.difference(current_option))
            if purge_cloudwatch_logs:
                format_option['DisableLogTypes'] = list(current_option.difference(desired_option))
            if format_option['EnableLogTypes'] or format_option['DisableLogTypes']:
                changing_params[option] = format_option
        else:
            changing_params[option] = desired_option

    return changing_params


def get_changing_options_with_consistent_keys(modify_params, instance):
    inconsistent_parameters = list(modify_params.keys())
    changing_params = {}

    for param in modify_params:
        current_option = instance.get('PendingModifiedValues', {}).get(param)
        if current_option is None:
            current_option = instance[param]
        if modify_params[param] != current_option:
            changing_params[param] = modify_params[param]

    return changing_params


def validate_options(client, module, instance):
    state = module.params['state']
    skip_final_snapshot = module.params['skip_final_snapshot']
    snapshot_id = module.params['final_db_snapshot_identifier']
    modified_id = module.params['new_db_instance_identifier']
    engine = module.params['engine']
    tde_options = bool(module.params['tde_credential_password'] or module.params['tde_credential_arn'])
    read_replica = module.params['read_replica']
    creation_source = module.params['creation_source']
    source_instance = module.params['source_db_instance_identifier']
    if module.params['source_region'] is not None:
        same_region = bool(module.params['source_region'] == module.params['region'])
    else:
        same_region = True

    if modified_id:
        modified_instance = get_instance(client, module, modified_id)
    else:
        modified_instance = {}

    if modified_id and instance and modified_instance:
        module.fail_json(msg='A new instance ID {0} was provided but it already exists'.format(modified_id))
    if modified_id and not instance and modified_instance:
        module.fail_json(msg='A new instance ID {0} was provided but the instance to be renamed does not exist'.format(modified_id))
    if state in ('absent', 'terminated') and instance and not skip_final_snapshot and snapshot_id is None:
        module.fail_json(msg='skip_final_snapshot is false but all of the following are missing: final_db_snapshot_identifier')
    if engine is not None and not (engine.startswith('mysql') or engine.startswith('oracle')) and tde_options:
        module.fail_json(msg='TDE is available for MySQL and Oracle DB instances')
    if read_replica is True and not instance and creation_source not in [None, 'instance']:
        module.fail_json(msg='Cannot create a read replica from {0}. You must use a source DB instance'.format(creation_source))
    if read_replica is True and not instance and not source_instance:
        module.fail_json(msg='read_replica is true and the instance does not exist yet but all of the following are missing: source_db_instance_identifier')


def update_instance(client, module, instance, instance_id):
    changed = False

    # Get newly created DB instance
    if not instance:
        instance = get_instance(client, module, instance_id)

    # Check tagging/promoting/rebooting/starting/stopping instance
    changed |= ensure_tags(
        client, module, instance['DBInstanceArn'], instance['Tags'], module.params['tags'], module.params['purge_tags']
    )
    changed |= promote_replication_instance(client, module, instance, module.params['read_replica'])
    changed |= update_instance_state(client, module, instance, module.params['state'])

    return changed


def promote_replication_instance(client, module, instance, read_replica):
    changed = False
    if read_replica is False:
        changed = bool(instance.get('ReadReplicaSourceDBInstanceIdentifier') or instance.get('StatusInfos'))
    if changed:
        try:
            call_method(client, module, method_name='promote_read_replica', parameters={'DBInstanceIdentifier': instance['DBInstanceIdentifier']})
            changed = True
        except is_boto3_error_code('InvalidDBInstanceState') as e:
            if 'DB Instance is not a read replica' in e.response['Error']['Message']:
                pass
            else:
                raise e
    return changed


def update_instance_state(client, module, instance, state):
    changed = False
    if state in ['rebooted', 'restarted']:
        changed |= reboot_running_db_instance(client, module, instance)
    if state in ['started', 'running', 'stopped']:
        changed |= start_or_stop_instance(client, module, instance, state)
    return changed


def reboot_running_db_instance(client, module, instance):
    parameters = {'DBInstanceIdentifier': instance['DBInstanceIdentifier']}
    if instance['DBInstanceStatus'] in ['stopped', 'stopping']:
        call_method(client, module, 'start_db_instance', parameters)
    if module.params.get('force_failover') is not None:
        parameters['ForceFailover'] = module.params['force_failover']
    results, changed = call_method(client, module, 'reboot_db_instance', parameters)
    return changed


def start_or_stop_instance(client, module, instance, state):
    changed = False
    parameters = {'DBInstanceIdentifier': instance['DBInstanceIdentifier']}
    if state == 'stopped' and instance['DBInstanceStatus'] not in ['stopping', 'stopped']:
        if module.params['db_snapshot_identifier']:
            parameters['DBSnapshotIdentifier'] = module.params['db_snapshot_identifier']
        result, changed = call_method(client, module, 'stop_db_instance', parameters)
    elif state == 'started' and instance['DBInstanceStatus'] not in ['available', 'starting', 'restarting']:
        result, changed = call_method(client, module, 'start_db_instance', parameters)
    return changed


def main():
    arg_spec = dict(
        state=dict(choices=['present', 'absent', 'terminated', 'running', 'started', 'stopped', 'rebooted', 'restarted'], default='present'),
        creation_source=dict(choices=['snapshot', 's3', 'instance']),
        force_update_password=dict(type='bool', default=False),
        purge_cloudwatch_logs_exports=dict(type='bool', default=True),
        purge_tags=dict(type='bool', default=True),
        read_replica=dict(type='bool'),
        wait=dict(type='bool', default=True),
    )

    parameter_options = dict(
        allocated_storage=dict(type='int'),
        allow_major_version_upgrade=dict(type='bool'),
        apply_immediately=dict(type='bool', default=False),
        auto_minor_version_upgrade=dict(type='bool'),
        availability_zone=dict(aliases=['az', 'zone']),
        backup_retention_period=dict(type='int'),
        ca_certificate_identifier=dict(),
        character_set_name=dict(),
        copy_tags_to_snapshot=dict(type='bool'),
        db_cluster_identifier=dict(aliases=['cluster_id']),
        db_instance_class=dict(aliases=['class', 'instance_type']),
        db_instance_identifier=dict(required=True, aliases=['instance_id', 'id']),
        db_name=dict(),
        db_parameter_group_name=dict(),
        db_security_groups=dict(type='list'),
        db_snapshot_identifier=dict(),
        db_subnet_group_name=dict(aliases=['subnet_group']),
        domain=dict(),
        domain_iam_role_name=dict(),
        enable_cloudwatch_logs_exports=dict(type='list', aliases=['cloudwatch_log_exports']),
        enable_iam_database_authentication=dict(type='bool'),
        enable_performance_insights=dict(type='bool'),
        engine=dict(),
        engine_version=dict(),
        final_db_snapshot_identifier=dict(aliases=['final_snapshot_identifier']),
        force_failover=dict(type='bool'),
        iops=dict(type='int'),
        kms_key_id=dict(),
        license_model=dict(choices=['license-included', 'bring-your-own-license', 'general-public-license']),
        master_user_password=dict(aliases=['password'], no_log=True),
        master_username=dict(aliases=['username']),
        monitoring_interval=dict(type='int'),
        monitoring_role_arn=dict(),
        multi_az=dict(type='bool'),
        new_db_instance_identifier=dict(aliases=['new_instance_id', 'new_id']),
        option_group_name=dict(),
        performance_insights_kms_key_id=dict(),
        performance_insights_retention_period=dict(type='int'),
        port=dict(type='int'),
        preferred_backup_window=dict(aliases=['backup_window']),
        preferred_maintenance_window=dict(aliases=['maintenance_window']),
        processor_features=dict(type='dict'),
        promotion_tier=dict(),
        publicly_accessible=dict(type='bool'),
        restore_time=dict(),
        s3_bucket_name=dict(),
        s3_ingestion_role_arn=dict(),
        s3_prefix=dict(),
        skip_final_snapshot=dict(type='bool', default=False),
        snapshot_identifier=dict(),
        source_db_instance_identifier=dict(),
        source_engine=dict(choices=['mysql']),
        source_engine_version=dict(),
        source_region=dict(),
        storage_encrypted=dict(type='bool'),
        storage_type=dict(choices=['standard', 'gp2', 'io1']),
        tags=dict(type='dict'),
        tde_credential_arn=dict(aliases=['transparent_data_encryption_arn']),
        tde_credential_password=dict(no_log=True, aliases=['transparent_data_encryption_password']),
        timezone=dict(),
        use_latest_restorable_time=dict(type='bool', aliases=['restore_from_latest']),
        vpc_security_group_ids=dict(type='list')
    )
    arg_spec.update(parameter_options)

    required_if = [
        ('engine', 'aurora', ('db_cluster_identifier',)),
        ('engine', 'aurora-mysql', ('db_cluster_identifier',)),
        ('engine', 'aurora-postresql', ('db_cluster_identifier',)),
        ('creation_source', 'snapshot', ('snapshot_identifier', 'engine')),
        ('creation_source', 's3', (
            's3_bucket_name', 'engine', 'master_username', 'master_user_password',
            'source_engine', 'source_engine_version', 's3_ingestion_role_arn')),
    ]
    mutually_exclusive = [
        ('s3_bucket_name', 'source_db_instance_identifier', 'snapshot_identifier'),
        ('use_latest_restorable_time', 'restore_to_time'),
        ('availability_zone', 'multi_az'),
    ]

    module = AnsibleAWSModule(
        argument_spec=arg_spec,
        required_if=required_if,
        mutually_exclusive=mutually_exclusive,
        supports_check_mode=True
    )

    if not module.boto3_at_least('1.5.0'):
        module.fail_json(msg="rds_instance requires boto3 > 1.5.0")

    # Sanitize instance identifiers
    module.params['db_instance_identifier'] = module.params['db_instance_identifier'].lower()
    if module.params['new_db_instance_identifier']:
        module.params['new_db_instance_identifier'] = module.params['new_db_instance_identifier'].lower()

    # Sanitize processor features
    if module.params['processor_features'] is not None:
        module.params['processor_features'] = dict((k, to_text(v)) for k, v in module.params['processor_features'].items())

    client = module.client('rds')
    changed = False
    state = module.params['state']
    instance_id = module.params['db_instance_identifier']
    instance = get_instance(client, module, instance_id)
    validate_options(client, module, instance)
    method_name = get_rds_method_attribute_name(instance, state, module.params['creation_source'], module.params['read_replica'])

    if method_name:
        raw_parameters = arg_spec_to_rds_params(dict((k, module.params[k]) for k in module.params if k in parameter_options))
        parameters = get_parameters(client, module, raw_parameters, method_name)

        if parameters:
            result, changed = call_method(client, module, method_name, parameters)

        instance_id = get_final_identifier(method_name, module)

        # Check tagging/promoting/rebooting/starting/stopping instance
        if state != 'absent' and (not module.check_mode or instance):
            changed |= update_instance(client, module, instance, instance_id)

        if changed:
            instance = get_instance(client, module, instance_id)
            if state != 'absent' and (instance or not module.check_mode):
                for attempt_to_wait in range(0, 10):
                    instance = get_instance(client, module, instance_id)
                    if instance:
                        break
                    else:
                        sleep(5)

        if state == 'absent' and changed and not module.params['skip_final_snapshot']:
            instance.update(FinalSnapshot=get_final_snapshot(client, module, module.params['final_db_snapshot_identifier']))

    pending_processor_features = None
    if instance.get('PendingModifiedValues', {}).get('ProcessorFeatures'):
        pending_processor_features = instance['PendingModifiedValues'].pop('ProcessorFeatures')
    instance = camel_dict_to_snake_dict(instance, ignore_list=['Tags', 'ProcessorFeatures'])
    if pending_processor_features is not None:
        instance['pending_modified_values']['processor_features'] = pending_processor_features

    module.exit_json(changed=changed, **instance)


if __name__ == '__main__':
    main()
