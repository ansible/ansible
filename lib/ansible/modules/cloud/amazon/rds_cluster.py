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
---
module: rds_cluster
short_description: Manages RDS Clusters for Aurora instances
description:
  -Manages the creation, modification, deletion, snapshot and restore of RDS Clusters for Aurora instances in AWS
version_added: "2.2"
author: "Nick Aslanidis (@naslanidis)"
options:
  command:
    description:
      - specifies the action to take
      - absent to remove resource
    required: true
    default: None
    choices: [ 'create', 'delete', 'modify', 'snapshot', 'restore' ]
  db_cluster_identifier:
    description:
      - Database cluster identifier. Required except when using command=delete on just a snapshot
    required: false
    default: null
  engine:
    description:
      - The type of database.  Used only when command=create.
    required: false
    default: null
    choices: ['aurora']
  master_username:
    description:
      - Master database username. Used only when command=create.
    required: false
    default: null
  master_user_password:
    description:
      - Password for the master database username. Used only when command=create or command=modify.
    required: false
    default: null
  region:
    description:
      - The AWS region to use. If not specified then the value of the EC2_REGION environment variable, if any, is used.
    required: true
  database_name:
    description:
      - Name of a database to create within the instance.  If not specified then no database is created. Used only when command=create.
    required: false
    default: null
  engine_version:
    description:
      - Version number of the database engine to use. Used only when command=create. If not specified then the current Amazon Aurora engine version is used.
    required: false
    default: null
  db_cluster_parameter_group_name:
    description:
      - Name of the DB Cluster parameter group to associate with this instance.  If omitted then the RDS default DBClusterParameterGroupName will be used. Used only when command=create or command=modify.
    required: false
  vpc_security_group_ids:
    description:
      - Comma separated list of one or more security groups.  Used only when command=create or command=modify.
    required: false
    default: null
  port:
    description:
      - The port number on which the instances in the DB cluster accept connections. Used only when command=create
    required: false
    default: 3306 for Aurora
  option_group_name:
    description:
      - A value that indicates that the DB cluster should be associated with the specified option group.  If not specified then the default option group is used. Used only when command=create or command=modify.
    required: false
    default: null
  preferred_maintenance_window:
    description:
      - "Maintenance window in format of ddd:hh24:mi-ddd:hh24:mi.  (Example: Mon:22:00-Mon:23:15) If not specified then a random maintenance window is assigned. Used only when command=create or command=modify."
    required: false
    default: random
  preferred_backup_window:
    description:
      - Backup window in format of hh24:mi-hh24:mi.  If not specified then a random backup window is assigned. Used only when command=create or command=modify.
    required: false
    default: random
  backup_retention_period:
    description:
      - "The number of days for which automated backups are retained. You must specify a minimum value of 1. Valid range: 1-35. Used only when command=create or command=modify."
    required: false
    default: 1
  availability_zones:
    description:
      - A list of EC2 Availability Zones that instances in the DB cluster can be created in.  Used only when command=create or command=restore.
    required: false
    default: null
  db_subnet_group_name:
    description:
      - A DB subnet group to associate with this DB cluster. Used only when command=create.
    required: false
    default: null
  character_set_name:
    description:
      - Associate the DB cluster with a specified character set. Used with command=create.
    required: false
    default: null
  apply_immediately:
    description:
      - Boolean value to enable/disable ApplyImmediately. If enabled modifications will be applied as soon as possible rather than waiting for the next preferred maintenance window.
    required: false
    default: false
  db_cluster_snapshot_identifer:
    description:
      - The identifier of the DB cluster snapshot. Used with command=snapshot
    required: false
    default: null
  replication_source_identifier:
    description:
      -  The Amazon Resource Name (ARN) of the source DB cluster if this DB cluster is created as a Read Replica.
    required: false
    default: null
  tags:
    description:
      - "A dictionary of resource tags of the form: { tag1: value1, tag2: value2 }." 
      - Used with command=create, command=restore. 
    required: false
    default: null
  storage_encrypted:
    description:
      -  Specifies whether the DB cluster is encrypted.
    required: false
    default: false
  kms_key_id:
    description:
      -  The KMS key identifier for an encrypted DB cluster. The KMS key identifier is the Amazon Resource Name (ARN) for the KMS encryption key.
    required: false
    default: default encryption key for the account
  skip_final_snapshot:
    description:
      -  Boolean value that determines whether a final DB cluster snapshot is created before the DB cluster is deleted. Used when commad=delete.
    required: false
    default: false
  final_db_snapshot_identifier:
    description:
      -  The DB cluster snapshot identifier of the new DB cluster snapshot created when SkipFinalSnapshot is set to false.
    required: false
    default: null      
  snapshot_identifer:
    description:
      -  The identifier for the DB cluster snapshot to restore from. Used only when command=restore.
    required: false
    default: null
  wait:
    description:
      - When command=create, modify or restore then wait for the cluster to enter the 'available' state.  When command=delete wait for the cluster to be terminated.
    required: false
    default: "no"
    choices: [ "yes", "no" ]
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 320
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
# Create an Aurora Cluster
- name: Create an Aurora RDS Cluster 
  rds_cluster:
    region: ap-southeast-2
    profile: production
    command: create
    db_cluster_identifier: test-aurora-cluster
    engine: aurora 
    engine_version: 5.6.10a
    master_username: testuser
    master_user_password: password
    db_cluster_parameter_group_name: test-aurora-param-group
    vpc_security_group_ids: 
      - sg-d155a6c1
    db_subnet_group_name: abc-sbg-prod
    storage_encrypted: true
    tags: 
      Role: Aurora
    wait: yes
    wait_timeout: 720
  register: new_aurora_rds_cluster

# Modify an existing cluster
- name: Modify an RDS cluster
  rds_cluster:
    region: ap-southeast-2
    profile: production
    command: modify
    db_cluster_identifier: test-aurora-cluster
    apply_immediately: True
    db_cluster_parameter_group_name: test-aurora-param-group-2
    wait: yes
    wait_timeout: 720
  register: modified_aurora_rds_cluster

# Snapshot an existing cluster
- name: Snapshot an RDS Aurora Cluster
  rds_cluster:
    region: ap-southeast-2
    profile: production
    command: snapshot
    db_cluster_snapshot_identifier : test-aurora-cluster-snapshot-1
    db_cluster_identifier : test-aurora-cluster
    Tags: 
      Role: Aurora-cluster-snapshot
    wait: yes
    wait_timeout: 720
  register: new_rds_cluster_snapshot

# Delete an existing cluster
- name: Delete RDS Cluster 
  rds_cluster:
    region: ap-southeast-2
    profile: production
    command: delete
    skip_final_snapshot: true      
    db_cluster_identifier: test-aurora-cluster
    wait: yes
    wait_timeout: 720
  register: deleted_aurora_rds_cluster

# Restore a cluster from a snapshot
- name: Restore a snapshot as a new cluster
  rds_cluster:
    region: ap-southeast-2
    profile: production
    command: restore
    SnapshotIdentifier: test-aurora-cluster-snapshot-1
    db_cluster_identifier: test-aurora-cluster
    engine: aurora 
    engine_version: 5.6.10a
    db_subnet_group_name: abc-sbg-prod
    port: 3306
    vpc_security_group_ids: 
      - sg-d155a6c1  
    tags: 
      Role: Aurora-cluster
    wait: yes
    wait_timeout: 720
  register: restored_rds_cluster
'''

RETURN = '''

DBClusters:
  AllocatedStorage:
    description: Specifies the allocated storage size in gigabytes (GB).
    returned: when command==create, modify, restore.
    type: integer
    sample: 123
  AvailabilityZones:
    description: Provides the list of EC2 Availability Zones that instances in the DB cluster can be created in.
    returned: when command==create, modify, restore.
    type: list
    sample: ["ap-southeast-2a", "ap-southeast-2b", "ap-southeast-2c"]
  BackupRetentionPeriod:
    description: Specifies the number of days for which automatic DB snapshots are retained.
    returned: when command==create, modify, restore.
    type: integer
    sample: 1
  DBClusterIdentifier:
    description: Contains a user-supplied DB cluster identifier. This identifier is the unique key that identifies a DB cluster
    returned: when command==create, modify, restore.
    type: string
    sample: "test-aurora-cluster" 
  DBClusterMembers:
    description: Contains a user-supplied DB cluster identifier. This identifier is the unique key that identifies a DB cluster
    returned: when command==create, modify, restore.
    type: list
    sample: []
  DBClusterParameterGroup:
    description: Specifies the name of the DB cluster parameter group for the DB cluster.
    returned: when command==create, restore.
    type: string
    sample: "test-aurora-param-group"
  DBSubnetGroup:
    description: A DB subnet group to associate with this DB cluster.
    returned: when command==create, restore.
    type: string
    sample: "abc-sbg-prod"
  DbClusterResourceId:
    description: The region-unique, immutable identifier for the DB cluster.
    returned: when command==create, modify, restore.
    type: string
    sample: "cluster-4XWMT2UOFW6AKGF3BKYH27FXT"
  EarliestRestorableTime:
    description: Specifies the earliest time to which a database can be restored with point-in-time restore.
    returned: when command==create, modify, restore.
    type: datetime
    sample: "2016-08-27T02:21:04.538000+00:00"
  Endpoint:
    description: Specifies the connection endpoint for the primary instance of the DB cluster.
    returned: when command==create, restore.
    type: string
    sample: "test-aurora-cluster.cluster-c4nb0jta2bug.ap-southeast-2.rds.amazonaws.com"
  Engine:
    description: Provides the name of the database engine to be used for this DB cluster.
    returned: when command==create, modify, restore.
    type: string
    sample: "aurora"
  EngineVersion:
    description: Indicates the database engine version.
    returned: when command==create, modify, restore.
    type: string
    sample: "5.6.10a"  
  HostedZoneId:
    description: Specifies the ID that Amazon Route 53 assigns when you create a hosted zone.
    returned: when command==create, modify, restore.
    type: string
    sample: "Z32T0VRHXEXS0V" 
  KmsKeyId:
    description: If StorageEncrypted is true, the KMS key identifier for the encrypted DB cluster.
    returned: when command==create, modify, restore.
    type: string
    sample: "arn:aws:kms:ap-southeast-2:123456789765:key/1b184ef4-e416-4004-a0f0-d5120a9f8e65"
  LatestRestorableTime:
    description: Specifies the latest time to which a database can be restored with point-in-time restore
    returned: when command==create, restore.
    type: datetime
    sample: "2016-08-27T02:21:04.538000+00:00"
  MasterUsername:
    description: Contains the master username for the DB cluster.
    returned: when command==create, modify, restore.
    type: string
    sample: "testuser"  
  Port:
    description: Specifies the port that the database engine is listening on.
    returned: when command==create, modify, restore.
    type: integer
    sample: 3306 
  PreferredBackupWindow:
    description: Specifies the daily time range during which automated backups are created if automated backups are enabled.
    returned: when command==create, modify, restore.
    type: string
    sample: "18:14-18:44" 
  PreferredMaintenanceWindow:
    description: Specifies the weekly time range during which system maintenance can occur, in Universal Coordinated Time (UTC).
    returned: when command==create, modify, restore.
    type: string
    sample: "tue:16:58-tue:17:28" 
  Status:
    description: Specifies the current state of this DB cluster.
    returned: when command==create, modify, restore.
    type: string
    sample: "available"           
  StorageEncrypted:
    description: Specifies whether the DB cluster is encrypted.
    returned: when command==create, modify, restore.
    type: boolean
    sample: true   
  VpcSecurityGroups:
    description: Provides a list of VPC security groups that the DB cluster belongs 
    returned: when command==create, modify, restore.
    type: list
    sample: [{"Status": "active", "VpcSecurityGroupId": "sg-d188c7b5"}]

DBClusterSnapshots:
  AllocatedStorage:
    description: Specifies the allocated storage size in gigabytes (GB).
    returned: when command==snapshot
    type: integer
    sample: 123
  AvailabilityZones:
    description: Provides the list of EC2 Availability Zones that instances in the DB cluster snapshot can be restored in.
    returned: when command==snapshot
    type: list
    sample: ["ap-southeast-2a", "ap-southeast-2b", "ap-southeast-2c"]
  ClusterCreateTime:
    description: Specifies the DB cluster identifier of the DB cluster that this DB cluster snapshot was created from
    returned: when command==snapshot
    type: datetime
    sample: "2016-08-28T23:23:56.228000+00:00"
  DBClusterIdentifier:
    description: Specifies the DB cluster identifier of the DB cluster that this DB cluster snapshot was created from.
    returned: when command==snapshot
    type: string
    sample: "test-aurora-cluster" 
  DBClusterSnapshotIdentifier:
    description: Specifies the identifier for the DB cluster snapshot.
    returned: when command==snapshot
    type: string
    sample: "test-aurora-cluster-snapshot" 
  Engine:
    description: Provides the name of the database engine to be used for this DB cluster.
    returned: when command==snapshot
    type: string
    sample: "aurora"
  KmsKeyId:
    description: If StorageEncrypted is true, the KMS key identifier for the encrypted DB cluster snapshot.
    returned: when command==snapshot
    type: string
    sample: "arn:aws:kms:ap-southeast-2:123456789765:key/1b184ef4-e416-4004-a0f0-d5120a9f8e65" 
  LicenseModel:
    description: Provides the license model information for this DB cluster snapshot.
    returned: when command==snapshot
    type: string
    sample: "aurora"
  PercentProgress:
    description: Specifies the percentage of the estimated data that has been transferred.
    returned: when command==snapshot
    type: integer
    sample: 100
  Port:
    description: Specifies the port that the DB cluster was listening on at the time of the snapshot.
    returned: when command==snapshot
    type: integer
    sample: 3306 
  SnapshotCreateTime:
    description: Provides the time when the snapshot was taken, in Universal Coordinated Time (UTC).
    returned: when command==snapshot
    type: datetime
    sample: "2016-08-28T23:34:03.088000+00:00"
  SnapshotType:
    description: Provides the type of the DB cluster snapshot.
    returned: when command==snapshot
    type: string
    sample: "manual" 
  Status:
    description: Specifies the status of this DB cluster snapshot.
    returned: when command==snapshot
    type: string
    sample: "available"
  StorageEncrypted:
    description: Specifies whether the DB cluster snapshot is encrypted.
    returned: when command==snapshot
    type: boolean
    sample: true
  VpcId:
    description: Provides the VPC ID associated with the DB cluster snapshot.
    returned: when command==snapshot
    type: string
    sample: vpc-abe12acg 
'''

try:
   import json
   import time
   import botocore
   import boto3
   HAS_BOTO3 = True
except ImportError:
   HAS_BOTO3 = False


def wait_for_status(client, module, status):
    polling_increment_secs = 15
    max_retries = (module.params.get('wait_timeout') / polling_increment_secs)
    status_achieved = False

    for x in range(0, max_retries):
        if module.params.get('command') == 'snapshot':
            try:
                response = get_db_cluster_snapshot(client, module)
                if module.params.get('command') == 'delete' and response == None:
                    status_achieved = True
                    break
                else:
                    if response['DBClusterSnapshots'][0]['Status'] == status:
                        status_achieved = True
                        break
                    else:
                        time.sleep(polling_increment_secs)
            except botocore.exceptions.ClientError as e:
                module.fail_json(msg=str(e))
        else:
            try:
                response = get_db_cluster(client, module)
                if module.params.get('command') == 'delete' and response == None:
                    status_achieved = True
                    break
                else:
                    if response['DBClusters'][0]['Status'] == status:
                        status_achieved = True
                        break
                    else:
                        time.sleep(polling_increment_secs)
            except botocore.exceptions.ClientError as e:
                module.fail_json(msg=str(e))

    result = response
    return status_achieved, result


def get_db_cluster(client, module, cluster_name=None):
    params = dict()
    
    if cluster_name: 
        params['DBClusterIdentifier'] = cluster_name
    else:
        params['DBClusterIdentifier'] = module.params.get('db_cluster_identifier')

    try:
        response = client.describe_db_clusters(**params)

    except botocore.exceptions.ClientError as e:
        if 'DBClusterNotFoundFault' not in e.message:
            module.fail_json(msg=str(e))
        else:
            response = None

    return response


def get_db_cluster_snapshot(client, module, cluster_snapshot_name=None):
    params = dict()

    if cluster_snapshot_name:
        params['DBClusterSnapshotIdentifier'] = cluster_snapshot_name
    else:
        params['DBClusterSnapshotIdentifier'] = module.params.get('db_cluster_snapshot_identifer')

    try:
        response = client.describe_db_cluster_snapshots(**params)
    except botocore.exceptions.ClientError as e:
        if 'DBClusterSnapshotNotFoundFault' not in e.message:
            module.fail_json(msg=str(e))
        else:
            response = None

    return response


def create_db_cluster(client, module):
    required_vars = ['db_cluster_identifier', 'engine']
    valid_vars = ['availability_zones', 'backup_retention_period', 'character_set_name', 'database_name', 'db_cluster_parameter_group_name',
                  'vpc_security_group_ids', 'db_subnet_group_name', 'engine_version', 'port', 'master_username', 'master_user_password', 
                  'option_group_name', 'preferred_backup_window', 'preferred_maintenance_window', 'replication_source_identifier', 
                  'tags', 'storage_encrypted', 'kms_key_id']

    params = validate_parameters(required_vars, valid_vars, module)
    #check if the db cluster already exists
    db_cluster = get_db_cluster(client, module)
    if db_cluster:
        response = db_cluster
        changed=False
    else:
        try:
            response = client.create_db_cluster(**params)
            changed = True
        except botocore.exceptions.ClientError as e:
            e = get_exception()
            module.fail_json(msg=str(e))

        if module.params.get('wait'):
            status_achieved, response = wait_for_status(client, module, 'available')
            if not status_achieved:
                module.fail_json(msg='Error waiting for RDS cluster creation - please check the AWS console')

    result = response
    return changed, result


def modify_db_cluster(client, module):
    changed = False
    required_vars = ['db_cluster_identifier']
    valid_vars = ['vpc_security_group_ids', 'apply_immediately', 'master_user_password', 'preferred_maintenance_window', 'db_cluster_parameter_group_name', 
                  'backup_retention_period', 'preferred_backup_window', 'port', 'option_group_name', 'new_db_cluster_identifier']

    NewDBClusterIdentifier = module.params.get('new_db_cluster_identifier')
    params = validate_parameters(required_vars, valid_vars, module)
    
    #get current cluster  so we can see if anything was actually modified and set changed accordingly
    before_modify_cluster = get_db_cluster(client, module)
    
    try:
        response = client.modify_db_cluster(**params)
    except botocore.exceptions.ClientError as e:
        e = get_exception()
        module.fail_json(msg=str(e))

    if params.get('apply_immediately'):
        if NewDBClusterIdentifier:
            # Wait until the new cluster name is valid
            new_cluster = None
            while not new_cluser:
                new_cluster = get_db_cluster(client, module, NewDBClusterIdentifier)
                time.sleep(5)

    #lookup cluster again to see if anything was modified
    after_modify_cluster = get_db_cluster(client, module)
    if cmp(before_modify_cluster['DBClusters'], after_modify_cluster['DBClusters']) != 0:
        changed = True
    else:
        changed = False

    if module.params.get('wait'):
        if changed:
            #wait for status modifying, then wait for status available
            status_achieved, response = wait_for_status(client, module, 'available')
            if not status_achieved:
                module.fail_json(msg='Error modifying RDS cluster - please check the AWS console')
        else:
            response = get_db_cluster(client, module)

    result = response
    return changed, result


def snapshot_db_cluster(client, module):
    changed = False
    required_vars = ['db_cluster_snapshot_identifer','db_cluster_identifier']
    valid_vars = ['tags']

    params = validate_parameters(required_vars, valid_vars, module)

    db_cluster_snapshot = get_db_cluster_snapshot(client, module)
    if db_cluster_snapshot:
        response = db_cluster_snapshot
        changed=False
    else:
        try:
            response = client.create_db_cluster_snapshot(**params)
            changed = True
        except botocore.exceptions.ClientError as e:
            e = get_exception()
            module.fail_json(msg=str(e))

    if module.params.get('wait'):
        status_achieved, response = wait_for_status(client, module, 'available')
        if not status_achieved:
            module.fail_json(msg='Error waiting for RDS cluster snapshot creation - please check the AWS console')

    result = response
    return changed, result


def restore_db_cluster_from_snapshot(client, module):
    changed = False
    required_vars = ['db_cluster_identifier', 'snapshot_identifer', 'engine']
    valid_vars = ['engine_version', 'port', 'availability_zones', 'db_subnet_group_name', 'database_name', 'option_group_name', 'vpc_security_group_ids',
                  'tags', 'kms_key_id']

    params = validate_parameters(required_vars, valid_vars, module)

    #check if cluster already exists. If so, do nothing and return the cluster
    db_cluster = get_db_cluster(client, module)
    if db_cluster:
        response = db_cluster
        changed=False
    else:
        try:
            response = client.restore_db_cluster_from_snapshot(**params)
            changed = True
        except botocore.exceptions.ClientError as e:
            e = get_exception()
            module.fail_json(msg=str(e))

        if module.params.get('wait'):
            status_achieved, response = wait_for_status(client, module, 'available')
            if not status_achieved:
                module.fail_json(msg='Error waiting for RDS cluster restore - please check the AWS console')

    result = response
    return changed, result


def delete_db_cluster_or_snapshot(client, module):
    changed = False
    if module.params.get('db_cluster_snapshot_identifer'):
        required_vars =['db_cluster_snapshot_identifer'] 
        valid_vars = []
        params = validate_parameters(required_vars, valid_vars, module)
    else:
        required_vars =['db_cluster_identifier']
        valid_vars = ['final_db_snapshot_identifier', 'skip_final_snapshot']
        params = validate_parameters(required_vars, valid_vars, module)

    if module.params.get('db_cluster_snapshot_identifer'):
        #check if the db cluster exists before attempting to delete it
        db_cluster_snapshot = get_db_cluster_snapshot(client, module, module.params.get('DBClusterSnapshotIdentifier'))
        if not db_cluster_snapshot:
            response = None
            changed=False
        else:
            try:
                response = client.delete_db_cluster_snapshot(**params)
                changed = True
            except botocore.exceptions.ClientError as e:
                e = get_exception()
                module.fail_json(msg=str(e))   

    else:
        #check if the db cluster exists before attempting to delete it
        db_cluster = get_db_cluster(client, module)
        if not db_cluster:
            response = None
            changed=False
        else:
            try:
                response = client.delete_db_cluster(**params)
                changed = True
            except botocore.exceptions.ClientError as e:
                e = get_exception()
                module.fail_json(msg=str(e))

            if module.params.get('wait'):
                #wait for status deleting, then wait for status deleted
                status_achieved, response = wait_for_status(client, module, 'deleting')
                status_achieved, response = wait_for_status(client, module, 'deleted')
                if not status_achieved:
                    module.fail_json(msg='Error deleting RDS cluster  - please check the AWS console')

    result = response
    return changed, result


def validate_parameters(required_vars, valid_vars, module):
    params = {}
    command = module.params.get('command')

    # convert snek case args to camel case params required for API
    camel_params = {
        'availability_zones': 'AvailabilityZones',
        'backup_retention_period': 'BackupRetentionPeriod',
        'character_set_name': 'CharacterSetName',
        'database_name': 'DatabaseName',
        'db_cluster_identifier': 'DBClusterIdentifier',
        'db_cluster_parameter_group_name': 'DBClusterParameterGroupName',
        'db_cluster_snapshot_identifer': 'DBClusterSnapshotIdentifier',
        'vpc_security_group_ids': 'VpcSecurityGroupIds',
        'new_db_cluster_identifier': 'NewDBClusterIdentifier',
        'db_subnet_group_name': 'DBSubnetGroupName',
        'engine': 'Engine',
        'engine_version': 'EngineVersion',
        'port': 'Port',
        'master_username': 'MasterUsername',
        'master_user_password': 'MasterUserPassword',
        'option_group_name': 'OptionGroupName',
        'preferred_maintenance_window': 'PreferredMaintenanceWindow',      
        'preferred_backup_window': 'PreferredBackupWindow',
        'replication_source_identifier': 'ReplicationSourceIdentifier',
        'tags': 'Tags',
        'storage_encrypted': 'StorageEncrypted',
        'kms_key_id': 'KmsKeyId',
        'skip_final_snapshot': 'SkipFinalSnapshot',
        'final_db_snapshot_identifier': 'FinalDBSnapshotIdentifier',
        'apply_immediately': 'ApplyImmediately',
        'snapshot_identifer': 'SnapshotIdentifier'}

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
        region=dict(required=True),
        command=dict(choices=['create', 'replicate', 'delete', 'facts', 'modify', 'promote', 'snapshot', 'reboot', 'restore'], required=True),
        availability_zones=dict(type='list', required=False), 
        backup_retention_period=dict(type='int', required=False),   
        character_set_name = dict(required=False),
        database_name=dict(required=False),    
        db_cluster_identifier=dict(required=False),
        new_db_cluster_identifier=dict(required=False),
        db_cluster_parameter_group_name=dict(required=False),
        db_cluster_snapshot_identifer=dict(required=False),
        vpc_security_group_ids=dict(type='list', required=False),
        db_subnet_group_name=dict(required=False),  
        engine=dict(choices=['aurora'], required=False),
        engine_version=dict(required=False),
        port=dict(type='int', required=False),  
        master_username=dict(required=False),
        master_user_password=dict(no_log=True, required=False),         
        option_group_name=dict(required=False),
        preferred_maintenance_window=dict(required=False),                    
        preferred_backup_window=dict(required=False),
        replication_source_identifier=dict(required=False),
        tags=dict(default=None, required=False, type='dict', aliases=['resource_tags']),        
        storage_encrypted=dict(type='bool', required=False),
        kms_key_id=dict(required=False),
        skip_final_snapshot=dict(type='bool', required=False),
        final_db_snapshot_identifier=dict(required=False), 
        wait=dict(type='bool', default=False),
        wait_timeout=dict(type='int', default=320, required=False),
        apply_immediately=dict(type='bool', default=False),
        snapshot_identifer=dict(required=False)
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
            'create': create_db_cluster,
            'delete': delete_db_cluster_or_snapshot,
            'modify': modify_db_cluster,
            'snapshot': snapshot_db_cluster,
            'restore': restore_db_cluster_from_snapshot
    }

    changed, results = invocations[module.params.get('command')](client, module)

    module.exit_json(changed=changed, rds=results)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
