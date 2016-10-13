#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
module: rds_v2
short_description: Create and delete AWS VPN Virtual Gateways.
description:
  - Creates RDS instances
  - Modifies RDS instances
  - Snapshots RDS instances
  - Restores RDS instances
  - Deletes RDS snapshots
  - Deletes RDS instances
  - Reboots RDS instances
version_added: "2.2"
requirements: [ boto3 ]
options:
  command:
    description:
        - specifies the action to take
        - absent to remove resource
    required: true
    default: None
    choices: [ 'create', 'delete', 'modify', 'snapshot', 'reboot', 'restore' ]
  db_instance_identifier:
    description:
      - Database instance identifier. Required except when using command=delete on just a snapshot.
    required: false
    default: null
  engine:
    description:
      - The name of the database engine to be used for this instance.  Used only when command=create or restore.
    required: false
    default: null
    choices: [ 'mariadb', 'MySQL', 'oracle-se1', 'oracle-se', 'oracle-ee', 'sqlserver-ee', 'sqlserver-se', 'sqlserver-ex', 'sqlserver-web', 'postgres', 'aurora']
  allocated_storage:
    description:
      - Size in gigabytes of the initial storage for the DB instance. Used only when command=create or modify.
    required: false
    default: null
  db_instance_class:
    description:
      - The compute and memory capacity of the DB instance.  Must be specified when command=create. Optional when command=modify, restore or replicate.
    required: false
    default: null
  master_username:
    description:
      - Master database username. Used only when command=create.
    required: false
    default: null
  master_user_password:
    description:
      - Password for the master database username. Used only when command=create modify.
    required: false
    default: null
  region:
    description:
      - The AWS region to use. If not specified then the value of the EC2_REGION environment variable, if any, is used.
    required: true
  db_name:
    description:
      - Name of a database to create within the instance.  If not specified then no database is created. Used when command=create or restore. 
    required: false
    default: null
  engine_version:
    description:
      - Version number of the database engine to use. Used only when command=create or modify. If not specified then the current Amazon RDS default engine version is used.
    required: false
    default: null
  db_parameter_group_name:
    description:
      - Name of the DB parameter group to associate with this instance.  If omitted then the RDS default DBParameterGroup will be used. Used only when command=create or modify.
    required: false
    default: null
  license_model:
    description:
      - The license model for this DB instance. Used when command=create, modify or restore. 
    required: false
    default: null
    choices:  [ 'license-included', 'bring-your-own-license', 'general-public-license', 'postgresql-license' ]
  multi_az:
    description:
      - Specifies if this is a Multi-availability-zone deployment. Can not be used in conjunction with availability_zone parameter. Used when command=create, modify or restore.
    required: false
    default: false
  iops:
    description:
      - Specifies the number of IOPS for the instance.  Used when command=create, modify, restore or replicate.
      - Must be a multiple between 3 and 10 of the storage amount for the DB instance.
    required: false
    default: null
  vpc_security_group_ids:
    description:
      - Comma separated list of one or more security groups.  Used only when command=create or modify.
    required: false
    default: null
  port:
    description:
      - Port number that the DB instance uses for connections. Used when command=create, modify, restore, replicate.
    required: false
    default: 3306 for mysql, 1521 for Oracle, 1433 for SQL Server, 5432 for PostgreSQL.
  auto_minor_version_upgrade:
    description:
      - Indicates that minor version upgrades should be applied automatically.  Used when command=create, modify, restore, replicate.
    required: false
    default: false
  allow_major_version_upgrade:
    description:
      - Indicates that major version upgrades should be applied automatically. Used only when command=modify
    required: false
    default: false
  option_group_name:
    description:
      - The name of the option group to use.  If not specified then the default option group is used. Used when command=create, modify, restore, replicate.
    required: false
    default: null
  preferred_maintenance_window:
    description:
      - "Maintenance window in format of ddd:hh24:mi-ddd:hh24:mi.  (Example: Mon:22:00-Mon:23:15) If not specified then a random maintenance window is assigned. Used only when command=create or modify."
    required: false
    default: null
  preferred_backup_window:
    description:
      - Backup window in format of hh24:mi-hh24:mi.  If not specified then a random backup window is assigned. Used when command=create, modify, promote.
    required: false
    default: null
  backup_retention_period:
    description:
      - "Number of days backups are retained.  Set to 0 to disable backups.  Default is 1 day.  Valid range: 0-35. Used when command=create, modify, promote."
    required: false
    default: null
  availability_zone:
    description:
      - availability zone in which to launch the instance. Used when command=create, modify, restore, replicate.
    required: false
    default: null
  db_subnet_group_name:
    description:
      - VPC subnet group.  If specified then a VPC instance is created. Used command=create, restore, replicate.
    required: false
    default: null
  db_snapshot_identifier:
    description:
      - Name of snapshot to take. When command=delete, if no snapshot name is provided then no snapshot is taken. Used with command=delete, snapshot, restore. 
    required: false
    default: null
  wait:
    description:
      - When command=create, modify or restore then wait for the database to enter the 'available' state.  When command=delete wait for the database to be terminated.
    required: false
    default: "no"
    choices: [ "yes", "no" ]
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 320
  apply_immediately:
    description:
      - If enabled, the modifications will be applied as soon as possible rather than waiting for the next preferred maintenance window.
      - Used only when command=modify.
    default: false
  force_failover:
    description:
      - If enabled, the reboot is done using a MultiAZ failover. Used only when command=reboot.
    required: false
    default: false
  new_db_instance_identifier:
    description:
      - Name to rename an instance to. Used only when command=modify.
    required: false
    default: null
  character_set_name:
    description:
      - Associate the DB instance with a specified character set. Used with command=create.
    required: false
    default: null
  publicly_accessible:
    description:
      - explicitly set whether the resource should be publicly accessible or not. Used with command=create, modify, restore, replicate. 
    required: false
    default: false
  storage_encrypted:
    description:
      - Specifies whether the DB instance is encrypted. Used only with command=create.
    required: false
    default: false
  kms_key_id:
    description:
      - The KMS key identifier for an encrypted DB instance. The KMS key identifier is the Amazon Resource Name (ARN) for the KMS encryption key.
      - Used only when command=create.
    required: false
    default: default encryption key for the account
  skip_final_snapshot:
    description:
      - Boolean value that determines whether a final DB snapshot is created before the DB instance is deleted. Used when commad=delete.
    required: false
    default: false
  final_db_snapshot_identifier:
    description:
      - The db_snapshot_identifier of the new DBSnapshot created when skip_final_snapshot is set to false. Used when commad=delete.
    required: false
  copy_tags_to_snapshot:
    description:
      - True to copy all tags from the DB instance to snapshots of the DB instance; otherwise false.
      - Used with command=create, modify, restore, replicate.
    required: false
    default: null
  storage_type:
    description:
      - Specifies the storage type to be associated with the DB instance. Used with command=create, modify, restore, replicate.
    required: false
    default: null
  monitoring_interval:
    description:
      - The interval, in seconds, between points when Enhanced Monitoring metrics are collected for the DB instance.
      - Used with command=create, modify, restore, replicate.
    required: false
    default: null
  db_cluster_identifier:
    description:
      - The identifier of the DB cluster that the instance will belong to. Used only when command=create.
    required: false
  source_db_instance_identifier:
    description:
      - The identifier of the DB instance that will act as the source for the Read Replica. Used only when command=replicate.
    required: false
    default: null
  tags:
    description:
      - "A dictionary of resource tags of the form: { tag1: value1, tag2: value2 }."
      - Used with command=create, modify, restore, replicate, snapshot.
    required: false
    default: null
author: Nick Aslanidis (@naslanidis)
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
# Create an RDS Instance
- name: Create an RDS instance
  rds_boto3:
    region: ap-southeast-2
    profile: production
    command: create
    db_instance_identifier: test-instance
    engine: MySQL 
    db_instance_class: db.t2.medium
    master_username: testuser
    master_user_password: password
    allocated_storage: 10
    db_parameter_group_name: test-param-group
    option_group_name: test-option-group
    vpc_security_group_ids: 
      - sg-d1881234
    db_subnet_group_name: test-subnet
    tags: 
      Role: Mysql
    wait: yes
    wait_timeout: 720
  register: new_rds_instance

# Create an RDS Aurora Instance
- name: Create an Aurora RDS instance with encryption enabled
  rds_boto3:
    region: ap-southeast-2
    profile: production
    command: create
    db_instance_identifier: test-aurora-instance-a
    db_cluster_identifier: test-aurora-cluster
    engine: aurora 
    engine_version: 5.6.10a
    db_instance_class: db.r3.large
    db_subnet_group_name: test-subnet
    availability_zone: ap-southeast-2a
    publicly_accessible:  false
    storage_encrypted: true
    tags: 
      Role: Aurora
    wait: yes
    wait_timeout: 720
  register: new_aurora_rds_instance

# Modify an RDS Instance
- name: Modify an RDS instance
  rds_boto3:
    region: ap-southeast-2
    profile: production
    command: modify
    db_instance_identifier: test-instance
    apply_immediately: True
    db_parameter_group_name: test-param-group
    option_group_name: test-option-group
    vpc_security_group_ids: 
      - sg-d1881234
    wait: yes
    wait_timeout: 720
  register: modified_rds_instance
   
# Snapshot an RDS Instance
- name: Snapshot an RDS instance
  rds_boto3:
    region: ap-southeast-2
    profile: production
    command: snapshot
    db_snapshot_identifier: test-instance-snapshot
    db_instance_identifier: test-instance
    tags: 
      Role: Mysql-snapshot
    wait: yes
    wait_timeout: 720
  register: new_rds_snapshot

# Delete an RDS Instance
- name: Delete an RDS instance
  rds_boto3:
    region: ap-southeast-2
    profile: production
    command: delete
    db_instance_identifier: test-instance
    skip_final_snapshot: True
    wait: yes
    wait_timeout: 720
  register: deleted_rds_instance

# Create an RDS Instance Read Replica
- name: create an RDS instance replica
  rds_boto3:
    region: ap-southeast-2
    profile: production
    command: replicate
    source_db_instance_identifier: test-instance    
    db_instance_identifier: test-instance-read-replica
    availability_zone: ap-southeast-2a
    db_instance_class: db.t2.medium
    option_group_name: test-option-group
    wait: yes
    wait_timeout: 720
  register: new_rds_replica
'''

RETURN = '''

DBInstance:
  AllocatedStorage:
    description: Specifies the allocated storage size specified in gigabytes.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: integer
    sample: 10
  AutoMinorVersionUpgrade:
    description: Indicates that minor version patches are applied automatically.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: boolean
    sample: true
  AvailabilityZone:
    description: Specifies the name of the Availability Zone the DB instance is located in.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "ap-southeast-2b"
  BackupRetentionPeriod:
    description: Specifies the number of days for which automatic DB snapshots are retained.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: integer
    sample: 1
  CACertificateIdentifier:
    description: The identifier of the CA certificate for this DB instance.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "rds-ca-2015"
  CopyTagsToSnapshot:
    description: Specifies whether tags are copied from the DB instance to snapshots of the DB instance.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: boolean
    sample: false
  DBInstanceClass:
    description: Contains the name of the compute and memory capacity class of the DB instance.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "db.t2.medium"
  DBInstanceIdentifier:
    description: Contains a user-supplied database identifier. This identifier is the unique key that identifies a DB instance.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "test-instance2"
  DBInstanceStatus:
    description: Specifies the current state of this database.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "available"
  DBName:
    description: Contains the name of the initial database of this instance that was provided at create time, if one was specified when the DB instance was created.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "null"
  DBParameterGroups:
    description: Provides the list of DB parameter groups applied to this DB instance.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "test-param-group"
  DBSubnetGroup:
    description: A DB subnet group to associate with this DB instance
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "abc-sbg-prod"
  DbInstancePort:
    description: Specifies the port that the DB instance listens on. If the DB instance is part of a DB cluster, this can be a different port than the DB cluster port.
    returned: when command=create, modify, reboot, restore, replicate
    type: integer
    sample: 0
  DbiResourceId:
    description: The region-unique, immutable identifier for the DB instance.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "db-C6IH24KNSUXIBDA2UNVO4BIIBY"
  Endpoint:
    description: Specifies the connection endpoint, including port, zone and hostedzoneid.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: dict
    sample: {"Address": "test-instance2.c4nb0jta2bug.ap-southeast-2.rds.amazonaws.com", "HostedZoneId": "Z32T0VXXXXXS0V", "Port": 3306"}
  Engine:
    description: Provides the name of the database engine to be used for this DB instance.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "mysql"
  EngineVersion:
    description: Indicates the database engine version.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "5.6.10a"
  InstanceCreateTime:
    description: Provides the date and time the DB instance was created.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: datetime
    sample: "2016-09-03T06:05:25.244000+00:00"
  LatestRestorableTime:
    description: Specifies the latest time to which a database can be restored with point-in-time restore.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: datetime
    sample: "2016-08-27T02:21:04.538000+00:00"
  LicenseModel:
    description: License model information for this DB instance.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "general-public-license"
  MasterUsername:
    description: Contains the master username for the DB instance.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "testuser"
  MonitoringInterval:
    description: The interval, in seconds, between points when Enhanced Monitoring metrics are collected for the DB instance.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: integer
    sample: 0
  MultiAZ:
    description: Specifies if the DB instance is a Multi-AZ deployment.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: boolean
    sample: false
  OptionGroupMemberships:
    description: Provides the list of option group memberships for this DB instance.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: list
    sample: [{"OptionGroupName": "test-option-group", "Status": "in-sync"}]
  PendingModifiedValues:
    description: Specifies that changes to the DB instance are pending.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: dict
    sample: {}
  PreferredBackupWindow:
    description: Specifies the daily time range during which automated backups are created if automated backups are enabled.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "18:14-18:44"
  PreferredMaintenanceWindow:
    description: Specifies the weekly time range during which system maintenance can occur, in Universal Coordinated Time (UTC).
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "tue:16:58-tue:17:28"
  PubliclyAccessible:
    description: Specifies the accessibility options for the DB instance
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: boolean
    sample: false
  ReadReplicaDBInstanceIdentifiers:
    description: Contains one or more identifiers of the Read Replicas associated with this DB instance.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: list
    sample: []
  ReadReplicaSourceDBInstanceIdentifier:
    description: Contains the identifier of the source DB instance if this DB instance is a Read Replica.
    returned: when command=replicate
    type: string
    sample: "test-instance"
  StorageEncrypted:
    description: Specifies whether the DB instance is encrypted.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: boolean
    sample: false
  StorageType:
    description: Specifies the storage type to be associated with the DB instance.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "standard"
  VpcSecurityGroups:
    description: Provides a list of VPC security groups that the DB instance belongs.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: list
    sample: [{"Status": "active", "VpcSecurityGroupId": "sg-d188c7b5"}]

DBSnapshots:
  AllocatedStorage:
    description: Specifies the allocated storage size specified in gigabytes.
    returned: when command=snapshot
    type: integer
    sample: 10
  AvailabilityZone:
    description: Specifies the name of the Availability Zone the DB instance was located in at the time of the DB snapshot.
    returned: when command=snapshot
    type: string
    sample: "ap-southeast-2b"
  DBInstanceIdentifier:
    description: Specifies the DB instance identifier of the DB instance this DB snapshot was created from.
    returned: when command=snapshot
    type: string
    sample: "test-instance"
  DBSnapshotIdentifier:
    description: Specifies the identifier for the DB snapshot.
    returned: when command=snapshot
    type: string
    sample: "test-instance-snapshot"
  Encrypted:
    description: Specifies whether the DB snapshot is encrypted.
    returned: when command=snapshot
    type: boolean
    sample: false
  Engine:
    description: Specifies the name of the database engine.
    returned: when command=snapshot
    type: string
    sample: "mysql"
  EngineVersion:
    description: Specifies the version of the database engine.
    returned: when command=snapshot
    type: string
    sample: "5.6.10a"
  InstanceCreateTime:
    description: Specifies the time when the snapshot was taken, in Universal Coordinated Time (UTC).
    returned: when command=snapshot
    type: datetime
    sample: "2016-09-03T06:05:25.244000+00:00"
  LicenseModel:
    description: License model information for the restored DB instance..
    returned: when command=snapshot
    type: string
    sample: "general-public-license"
  MasterUsername:
    description: Provides the master username for the DB snapshot.
    returned: when command=snapshot
    type: string
    sample: "testuser"
  OptionGroupName:
    description: Provides the option group name for the DB snapshot.
    returned: when command=snapshot
    type: string
    sample: "test-option-group"
  PercentProgress:
    description: The percentage of the estimated data that has been transferred.
    returned: when command=snapshot
    type: integer
    sample: 100
  Port:
    description: Specifies the port that the database engine was listening on at the time of the snapshot.
    returned: when command=snapshot
    type: integer
    sample: 3306
  SnapshotCreateTime:
    description: Provides the time when the snapshot was taken, in Universal Coordinated Time (UTC).
    returned: when command=snapshot
    type: datetime
    sample: "2016-09-04T00:38:01.669000+00:00"
  SnapshotType:
    description: Provides the type of the DB snapshot.
    returned: when command=snapshot
    type: string
    sample: "manual"
  Status:
    description: Specifies the status of this DB snapshot.
    returned: when command=snapshot
    type: string
    sample: "available"
  StorageType:
    description: Provides the type of the DB snapshot.
    returned: when command=snapshot
    type: string
    sample: "standard"
  VpcId:
    description: Provides the VPC ID associated with the DB snapshot.
    returned: when command=snapshot
    type: string
    sample: "vpc-aad24123"
'''

try:
    import time
    import botocore
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def wait_for_status(client, module, status):
    polling_increment_secs = 5
    max_retries = (module.params.get('wait_timeout') / polling_increment_secs)
    status_achieved = False

    for x in range(0, max_retries):
        if module.params.get('command') == 'snapshot':
            try:
                response = get_db_snapshot(client, module)
                if module.params.get('command') == 'delete' and response == None:
                    status_achieved = True
                    break
                else:
                    if response['DBSnapshots'][0]['Status'] == status:
                        status_achieved = True
                        break
                    else:
                        time.sleep(polling_increment_secs)
            except botocore.exceptions.ClientError as e:
                module.fail_json(msg=str(e))
        
        else:
            try:
                response = get_db_instance(client, module)
                if module.params.get('command') == 'delete' and response == None:
                    status_achieved = True
                    break
                else:
                    if response['DBInstances'][0]['DBInstanceStatus'] == status:
                        status_achieved = True
                        break
                    else:
                        time.sleep(polling_increment_secs)
            except botocore.exceptions.ClientError as e:
                module.fail_json(msg=str(e))

    result = response
    return status_achieved, result


def get_db_instance(client, module, instance_name=None):
    params = dict()
    if instance_name:
        params['DBInstanceIdentifier'] = instance_name
    else:
        params['DBInstanceIdentifier'] = module.params.get('db_instance_identifier')

    try:
        response = client.describe_db_instances(**params)

    except botocore.exceptions.ClientError as e:
        if 'DBInstanceNotFound' not in e.message:
            module.fail_json(msg=str(e))
        else:
            response = None

    return response


def get_db_snapshot(client, module, snapshot_name=None):
    params = dict()
    if module.params.get('db_instance_identifier'):
        params['DBInstanceIdentifier'] = module.params.get('db_instance_identifier')
    if snapshot_name:
        params['DBSnapshotIdentifier'] = snapshot_name
    else:
        params['DBSnapshotIdentifier'] = module.params.get('db_snapshot_identifier')

    try:
        response = client.describe_db_snapshots(**params)
    except botocore.exceptions.ClientError as e:
        if 'DBSnapshotNotFound' not in e.message:
            module.fail_json(msg=str(e))
        else:
            response = None

    return response


def create_db_instance(client, module):
    # DBClusterIdentifier is only for Aurora instances. If one is supplied, only a subset of params are supported.
    if module.params.get('db_cluster_identifier'): 
        required_vars = ['db_instance_identifier','db_instance_class', 'engine']
        valid_vars = ['db_cluster_identifier', 'availability_zone', 'db_subnet_group_name',
                  'preferred_maintenance_window', 'db_parameter_group_name',
                  'engine_version', 'auto_minor_version_upgrade', 'license_model', 'option_group_name',
                  'publicly_accessible', 'character_set_name', 'storage_encrypted', 'kms_key_id', 'tags']
    else:
        required_vars = ['db_instance_identifier', 'engine', 'db_instance_class', 'master_username', 'master_user_password']
        valid_vars = ['db_name', 'allocated_storage', 'vpc_security_group_ids', 'availability_zone', 'db_subnet_group_name',
                  'preferred_maintenance_window', 'db_parameter_group_name', 'backup_retention_period', 'preferred_backup_window',
                  'port', 'multi_az', 'engine_version', 'auto_minor_version_upgrade', 'license_model', 'iops',
                  'option_group_name', 'publicly_accessible', 'character_set_name', 'storage_encrypted', 'kms_key_id', 'tags',
                  'db_cluster_identifier', 'copy_tags_to_snapshot', 'monitoring_interval', 'storage_type']

    params = validate_parameters(required_vars, valid_vars, module)
    # Check if the db instance already exists
    db_instance = get_db_instance(client, module)
    if db_instance:
        response = db_instance
        changed=False
    else:
        try:
            response = client.create_db_instance(**params)
            changed = True
        except botocore.exceptions.ClientError as e:
            e = get_exception()
            module.fail_json(msg=str(e))

        if module.params.get('wait'):
            status_achieved, response = wait_for_status(client, module, 'available')
            if not status_achieved:
                module.fail_json(msg='Error waiting for RDS instance creation - please check the AWS console')

    result = response
    return changed, result


def modify_db_instance(client, module):
    changed = False
    required_vars = ['db_instance_identifier']
    valid_vars = ['allocated_storage', 'db_instance_class', 'vpc_security_group_ids', 'apply_immediately', 'master_user_password', 'preferred_maintenance_window',
                  'db_parameter_group_name', 'backup_retention_period', 'preferred_backup_window', 'port', 'multi_az', 'engine_version', 'auto_minor_version_upgrade',
                  'allow_major_version_upgrade', 'license_model', 'iops', 'option_group_name', 'publicly_accessible', 'new_db_instance_identifier', 'storage_type',
                  'copy_tags_to_snapshot', 'monitoring_interval']

    NewDBInstanceIdentifier = module.params.get('new_db_instance_identifier')
    params = validate_parameters(required_vars, valid_vars, module)

    # Change the Ports key to 'DBPortNumber'. For some reason this argument is different in the modify and create API action specs
    if module.params.get('port'):
        params.pop('Port')
        params['DBPortNumber'] = module.params.get('port')

    # Get current instance so we can see if anything was actually modified and set changed accordingly
    before_modify_instance = get_db_instance(client, module)

    try:
        response = client.modify_db_instance(**params)
    except botocore.exceptions.ClientError as e:
        e = get_exception()
        module.fail_json(msg=str(e))

    if params.get('apply_immediately'):
        if NewDBInstanceIdentifier:
            # Wait until the new instance name is valid
            new_instance = None
            while not new_instance:
                new_instance = get_db_instance(client, module, NewDBInstanceIdentifier)
                time.sleep(5)

    # Lookup instance again to see if anything was modified
    after_modify_instance = get_db_instance(client, module)
    if cmp(before_modify_instance['DBInstances'], after_modify_instance['DBInstances']) != 0:
        changed = True
    else:
        changed = False

    if module.params.get('wait'):
        if changed:
            # Wait for status modifying, then wait for status available.
            # Note: aurora doesn't transition modifying state
            if before_modify_instance['DBInstances'][0]['Engine'] == 'aurora':
                status_achieved, response = wait_for_status(client, module, 'available')
            else:
                status_achieved, response = wait_for_status(client, module, 'modifying')
                status_achieved, response = wait_for_status(client, module, 'available')

            if not status_achieved:
                module.fail_json(msg='Error modifying RDS instance  - please check the AWS console')
        else:
            response = get_db_instance(client, module)

    result = response
    return changed, result


def snapshot_db_instance(client, module):
    changed = False
    required_vars = ['db_snapshot_identifier','db_instance_identifier']
    valid_vars = ['tags']
    params = validate_parameters(required_vars, valid_vars, module)

    db_snapshot = get_db_snapshot(client, module)
    if db_snapshot['DBSnapshots']:
        response = db_snapshot
        changed=False
    else:
        try:
            response = client.create_db_snapshot(**params)
            changed = True
        except botocore.exceptions.ClientError as e:
            e = get_exception()
            module.fail_json(msg=str(e))

    if module.params.get('wait'):
        status_achieved, response = wait_for_status(client, module, 'available')
        if not status_achieved:
            module.fail_json(msg='Error waiting for RDS snapshot creation - please check the AWS console')

    result = response
    return changed, result


def delete_db_instance_or_snapshot(client, module):
    changed = False
    if module.params.get('db_snapshot_identifier'):
        required_vars =['db_snapshot_identifier']
        valid_vars = []
        params = validate_parameters(required_vars, valid_vars, module)
    else:
        required_vars =['db_instance_identifier']
        valid_vars = ['skip_final_snapshot','final_db_snapshot_identifier']
        params = validate_parameters(required_vars, valid_vars, module)

    if module.params.get('db_snapshot_identifier'):
        # Check if the db snapshot exists before attempting to delete it
        db_snapshot = get_db_snapshot(client, module, module.params.get('db_snapshot_identifier'))
        if not db_snapshot:
            response = None
            changed=False
        else:
            try:
                response = client.delete_db_snapshot(**params)
                changed = True
            except botocore.exceptions.ClientError as e:
                e = get_exception()
                module.fail_json(msg=str(e))

    else:
        # Check if the db instance exists before attempting to delete it
        db_instance = get_db_instance(client, module)
        if not db_instance:
            response = None
            changed=False
        else:
            try:
                response = client.delete_db_instance(**params)
                changed = True
            except botocore.exceptions.ClientError as e:
                e = get_exception()
                module.fail_json(msg=str(e))

            if module.params.get('wait'):
                #wait for status deleting, then wait for status deleted
                status_achieved, response = wait_for_status(client, module, 'deleting')
                status_achieved, response = wait_for_status(client, module, 'deleted')
                if not status_achieved:
                    module.fail_json(msg='Error deleting RDS instance  - please check the AWS console')

    result = response
    return changed, result    


def restore_db_instance_from_snapshot(client, module):
    changed = False
    required_vars = ['db_instance_identifier', 'db_snapshot_identifier']
    valid_vars = ['db_instance_class', 'port', 'availability_zone', 'db_subnet_group_name', 'multi_az', 'publicly_accessible',
                  'auto_minor_version_upgrade', 'db_name', 'engine', 'iops', 'option_group_name', 'tags', 'storage_type',
                  'license_model', 'copy_tags_to_snapshot']

    params = validate_parameters(required_vars, valid_vars, module)

    # Check if instance already exists. If so, do nothing and return the instance.
    db_instance = get_db_instance(client, module)
    if db_instance:
        response = db_instance
        changed=False
    else:
        try:
            response = client.restore_db_instance_from_db_snapshot(**params)
            changed = True
        except botocore.exceptions.ClientError as e:
            e = get_exception()
            module.fail_json(msg=str(e))

        if module.params.get('wait'):
            status_achieved, response = wait_for_status(client, module, 'available')
            if not status_achieved:
                module.fail_json(msg='Error waiting for RDS instance creation - please check the AWS console')

    result = response
    return changed, result


def reboot_db_instance(client, module):
    changed = False
    required_vars = ['db_instance_identifier']
    valid_vars = ['force_failover']

    params = validate_parameters(required_vars, valid_vars, module)

    # check if instance exists before attempting to reboot
    db_instance = get_db_instance(client, module)
    
    if db_instance:
        try:
            response = client.reboot_db_instance(**params)
            changed = True
        except botocore.exceptions.ClientError as e:
            e = get_exception()
            module.fail_json(msg=str(e))

        if module.params.get('wait'):
            status_achieved, response = wait_for_status(client, module, 'available')
            if not status_achieved:
                module.fail_json(msg='Error waiting for RDS instance creation - please check the AWS console')
    
    else:
        module.fail_json(msg='Error attempting to reboot an instance that doesnt exist')

    result = response
    return changed, result


def replicate_db_instance(client, module):
    changed = False
    required_vars = ['db_instance_identifier', 'source_db_instance_identifier']
    valid_vars = ['db_instance_class', 'availability_zone', 'port', 'auto_minor_version_upgrade', 'iops',
                  'option_group_name', 'publicly_accessible', 'tags', 'db_subnet_group_name', 'storage_type',
                  'copy_tags_to_snapshot', 'monitoring_interval']

    params = validate_parameters(required_vars, valid_vars, module)

    # Check if instance already exists. If so, do nothing and return the instance
    db_instance = get_db_instance(client, module)
    if db_instance:
        response = db_instance
        changed=False
    else:
        try:
            response = client.create_db_instance_read_replica(**params)
            changed = True
        except botocore.exceptions.ClientError as e:
            e = get_exception()
            module.fail_json(msg=str(e))

        if module.params.get('wait'):
            status_achieved, response = wait_for_status(client, module, 'available')
            if not status_achieved:
                module.fail_json(msg='Error waiting for RDS replica creation - please check the AWS console')

    result = response
    return changed, result


def promote_db_instance(client, module):
    changed = False
    required_vars = ['db_instance_identifier']
    valid_vars = ['backup_retention_period', 'preferred_backup_window']
    instance_name = module.params.get('db_instance_identifier')

    params = validate_parameters(required_vars, valid_vars, module)

    # check if instance already exists. If so, do nothing and return the instance
    db_instance = get_db_instance(client, module)
    if not db_instance:
        module.fail_json(msg="DB Instance %s does not exist" % instance_name)

    else:
        try:
            response = client.promote_read_replica(**params)
            changed = True
        except botocore.exceptions.ClientError as e:
            e = get_exception()
            module.fail_json(msg=str(e))

        if module.params.get('wait'):
            status_achieved, response = wait_for_status(client, module, 'available')
            if not status_achieved:
                module.fail_json(msg='Error waiting for RDS instance promotion - please check the AWS console')

    result = response
    return changed, result


def validate_parameters(required_vars, valid_vars, module):
    params = {}
    command = module.params.get('command')

    # Convert snek case args to camel case params required for API
    camel_params = {
        'availability_zone': 'AvailabilityZone',
        'backup_retention_period': 'BackupRetentionPeriod',
        'character_set_name': 'CharacterSetName',
        'db_name': 'DBName',
        'db_instance_identifier': 'DBInstanceIdentifier',
        'db_parameter_group_name': 'DBParameterGroupName',
        'db_snapshot_identifier': 'DBSnapshotIdentifier',
        'vpc_security_group_ids': 'VpcSecurityGroupIds',
        'new_db_instance_identifier': 'NewDBInstanceIdentifier',
        'db_subnet_group_name': 'DBSubnetGroupName',
        'engine': 'Engine',
        'engine_version': 'EngineVersion',
        'port': 'Port',
        'master_username': 'MasterUsername',
        'master_user_password': 'MasterUserPassword',
        'option_group_name': 'OptionGroupName',
        'preferred_maintenance_window': 'PreferredMaintenanceWindow',
        'preferred_backup_window': 'PreferredBackupWindow',
        'tags': 'Tags',
        'storage_encrypted': 'StorageEncrypted',
        'kms_key_id': 'KmsKeyId',
        'skip_final_snapshot': 'SkipFinalSnapshot',
        'final_db_snapshot_identifier': 'FinalDBSnapshotIdentifier',
        'apply_immediately': 'ApplyImmediately',
        'allocated_storage': 'AllocatedStorage',
        'db_instance_class': 'DBInstanceClass',        
        'copy_tags_to_snapshot': 'CopyTagsToSnapshot',
        'monitoring_interval': 'MonitoringInterval',
        'multi_az': 'MultiAZ',
        'license_model': 'LicenseModel',
        'auto_minor_version_upgrade': 'AutoMinorVersionUpgrade',
        'allow_major_version_upgrade': 'AllowMajorVersionUpgrade',
        'iops': 'Iops',
        'storage_type': 'StorageType',
        'publicly_accessible': 'PubliclyAccessible',
        'storage_encrypted': 'StorageEncrypted',
        'force_failover': 'ForceFailover',
        'db_cluster_identifier': 'DBClusterIdentifier',
        'source_db_instance_identifier': 'SourceDBInstanceIdentifier'}

    for (k, v) in camel_params.iteritems():
        if module.params.get(k) and k not in required_vars:
            if k in valid_vars: 
                params[v] = module.params[k]
            else:
                module.fail_json(msg="Parameter %s is not valid for %s command" % (k, command))
        if k in required_vars:
            if module.params.get(k):
                params[v] = module.params[k]
            else:
                module.fail_json(msg="Parameter %s required for %s command" % (k, command))

    tag_array = []
    if module.params.get('tags'):
        for tag, value in module.params.get('tags').iteritems():
            tag_array.append({'Key': tag, 'Value': value})
        params['Tags'] = tag_array
    
    return params

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        region=dict(type='str', required=True),
        command=dict(type='str', choices=['create', 'replicate', 'delete', 'facts', 'modify', 'promote', 'snapshot', 'reboot', 'restore'], required=True),
        db_name=dict(type='str', required=False),
        db_instance_identifier=dict(type='str', required=False),
        allocated_storage=dict(type='int', required=False),
        db_instance_class=dict(type='str', required=False),
        engine=dict(type='str', choices=['mariadb', 'MySQL', 'oracle-se1', 'oracle-se', 'oracle-ee', 'sqlserver-ee', 'sqlserver-se', 'sqlserver-ex', 'sqlserver-web', 'postgres', 'aurora'], required=False),
        master_username=dict(type='str', required=False),
        master_user_password=dict(type='str', no_log=True, required=False),
        vpc_security_group_ids=dict(type='list', required=False),
        apply_immediately=dict(type='bool', default=False),
        availability_zone=dict(type='str', required=False),
        db_subnet_group_name=dict(type='str', required=False),
        preferred_maintenance_window=dict(type='str', required=False),
        db_parameter_group_name=dict(type='str', required=False),
        backup_retention_period=dict(type=int, required=False),
        preferred_backup_window=dict(type='str', required=False),
        copy_tags_to_snapshot=dict(type='bool', required=False),
        monitoring_interval=dict(type='int', required=False),
        port=dict(type='int', required=False),
        multi_az=dict(type='bool', default=False),
        engine_version=dict(type='str', required=False),
        auto_minor_version_upgrade=dict(type='bool', required=False),
        allow_major_version_upgrade=dict(type='bool', required=False),
        license_model=dict(type='str', choices=['license-included', 'bring-your-own-license', 'general-public-license', 'postgresql-license'], required=False),
        iops=dict(type='int', required=False),
        option_group_name=dict(type='str', required=False),
        publicly_accessible=dict(type='bool', required=False),
        character_set_name = dict(type='str', required=False),
        tags=dict(type='dict', default=None, required=False),
        storage_encrypted=dict(type='bool', required=False),
        kms_key_id=dict(type='str', required=False),
        wait=dict(type='bool', default=False),
        wait_timeout=dict(type='int', default=320, required=False),
        new_db_instance_identifier=dict(type='str', required=False),
        storage_type=dict(type='str', required=False),
        db_snapshot_identifier=dict(type='str', required=False),
        skip_final_snapshot=dict(type='bool', default=False),
        final_db_snapshot_identifier=dict(type='str', required=False),
        force_failover=dict(type='bool', default=False),
        db_cluster_identifier=dict(type='str', required=False),
        source_db_instance_identifier=dict(type='str', required=False)
        )
    )
    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='json and boto3 is required.')

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        client = boto3_conn(module, conn_type='client', resource='rds', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.NoCredentialsError:
        e = get_exception()
        module.fail_json(msg="Can't authorize connection - "+str(e))

    invocations = {
            'create': create_db_instance,
            'modify': modify_db_instance,
            'snapshot': snapshot_db_instance,
            'delete': delete_db_instance_or_snapshot,
            'restore': restore_db_instance_from_snapshot,
            'reboot': reboot_db_instance,
            'replicate': replicate_db_instance,
            'promote': promote_db_instance
    }        

    changed, results = invocations[module.params.get('command')](client, module)

    module.exit_json(changed=changed, rds=results)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
