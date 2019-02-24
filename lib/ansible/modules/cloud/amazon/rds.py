#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: rds
version_added: "1.3"
short_description: create, delete, or modify an Amazon rds instance
description:
     - Creates, deletes, or modifies rds instances.  When creating an instance it can be either a new instance or a read-only replica of an existing
       instance. This module has a dependency on python-boto >= 2.5. The 'promote' command requires boto >= 2.18.0. Certain features such as tags rely
       on boto.rds2 (boto >= 2.26.0)
options:
  command:
    description:
      - Specifies the action to take. The 'reboot' option is available starting at version 2.0
    required: true
    choices: [ 'create', 'replicate', 'delete', 'facts', 'modify' , 'promote', 'snapshot', 'reboot', 'restore' ]
  instance_name:
    description:
      - Database instance identifier. Required except when using command=facts or command=delete on just a snapshot
  source_instance:
    description:
      - Name of the database to replicate. Used only when command=replicate.
  db_engine:
    description:
      - The type of database.  Used only when command=create.
      - mariadb was added in version 2.2
    choices: ['mariadb', 'MySQL', 'oracle-se1', 'oracle-se2', 'oracle-se', 'oracle-ee',
              'sqlserver-ee', 'sqlserver-se', 'sqlserver-ex', 'sqlserver-web', 'postgres', 'aurora']
  size:
    description:
      - Size in gigabytes of the initial storage for the DB instance. Used only when command=create or command=modify.
  instance_type:
    description:
      - The instance type of the database.  Must be specified when command=create. Optional when command=replicate, command=modify or command=restore.
        If not specified then the replica inherits the same instance type as the source instance.
  username:
    description:
      - Master database username. Used only when command=create.
  password:
    description:
      - Password for the master database username. Used only when command=create or command=modify.
  region:
    description:
      - The AWS region to use. If not specified then the value of the EC2_REGION environment variable, if any, is used.
    required: true
    aliases: [ 'aws_region', 'ec2_region' ]
  db_name:
    description:
      - Name of a database to create within the instance.  If not specified then no database is created. Used only when command=create.
  engine_version:
    description:
      - Version number of the database engine to use. Used only when command=create. If not specified then the current Amazon RDS default engine version is used
  parameter_group:
    description:
      - Name of the DB parameter group to associate with this instance.  If omitted then the RDS default DBParameterGroup will be used. Used only
        when command=create or command=modify.
  license_model:
    description:
      - The license model for this DB instance. Used only when command=create or command=restore.
    choices:  [ 'license-included', 'bring-your-own-license', 'general-public-license', 'postgresql-license' ]
  multi_zone:
    description:
      - Specifies if this is a Multi-availability-zone deployment. Can not be used in conjunction with zone parameter. Used only when command=create or
        command=modify.
    type: bool
  iops:
    description:
      - Specifies the number of IOPS for the instance.  Used only when command=create or command=modify. Must be an integer greater than 1000.
  security_groups:
    description:
      - Comma separated list of one or more security groups.  Used only when command=create or command=modify.
  vpc_security_groups:
    description:
      - Comma separated list of one or more vpc security group ids. Also requires `subnet` to be specified. Used only when command=create or command=modify.
  port:
    description:
      - Port number that the DB instance uses for connections. Used only when command=create or command=replicate.
      - Prior to 2.0 it always defaults to null and the API would use 3306, it had to be set to other DB default values when not using MySql.
        Starting at 2.0 it automatically defaults to what is expected for each C(db_engine).
    default: 3306 for mysql, 1521 for Oracle, 1433 for SQL Server, 5432 for PostgreSQL.
  upgrade:
    description:
      - Indicates that minor version upgrades should be applied automatically.
      - Used only when command=create or command=modify or command=restore or command=replicate.
    type: bool
    default: 'no'
  option_group:
    description:
      - The name of the option group to use.  If not specified then the default option group is used. Used only when command=create.
  maint_window:
    description:
      - >
        Maintenance window in format of ddd:hh24:mi-ddd:hh24:mi.  (Example: Mon:22:00-Mon:23:15) If not specified then a random maintenance window is
        assigned. Used only when command=create or command=modify.
  backup_window:
    description:
      - Backup window in format of hh24:mi-hh24:mi.  If not specified then a random backup window is assigned. Used only when command=create or command=modify.
  backup_retention:
    description:
      - >
        Number of days backups are retained.  Set to 0 to disable backups.  Default is 1 day.  Valid range: 0-35. Used only when command=create or
        command=modify.
  zone:
    description:
      - availability zone in which to launch the instance. Used only when command=create, command=replicate or command=restore.
    aliases: ['aws_zone', 'ec2_zone']
  subnet:
    description:
      - VPC subnet group.  If specified then a VPC instance is created. Used only when command=create.
  snapshot:
    description:
      - Name of snapshot to take. When command=delete, if no snapshot name is provided then no snapshot is taken. If used with command=delete with
        no instance_name, the snapshot is deleted. Used with command=facts, command=delete or command=snapshot.
  aws_secret_key:
    description:
      - AWS secret key. If not set then the value of the AWS_SECRET_KEY environment variable is used.
    aliases: [ 'ec2_secret_key', 'secret_key' ]
  aws_access_key:
    description:
      - AWS access key. If not set then the value of the AWS_ACCESS_KEY environment variable is used.
    aliases: [ 'ec2_access_key', 'access_key' ]
  wait:
    description:
      - When command=create, replicate, modify or restore then wait for the database to enter the 'available' state.  When command=delete wait for
        the database to be terminated.
    type: bool
    default: 'no'
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 300
  apply_immediately:
    description:
      - Used only when command=modify.  If enabled, the modifications will be applied as soon as possible rather than waiting for the next
        preferred maintenance window.
    type: bool
    default: 'no'
  force_failover:
    description:
      - Used only when command=reboot.  If enabled, the reboot is done using a MultiAZ failover.
    type: bool
    default: 'no'
    version_added: "2.0"
  new_instance_name:
    description:
      - Name to rename an instance to. Used only when command=modify.
    version_added: "1.5"
  character_set_name:
    description:
      - Associate the DB instance with a specified character set. Used with command=create.
    version_added: "1.9"
  publicly_accessible:
    description:
      - explicitly set whether the resource should be publicly accessible or not. Used with command=create, command=replicate. Requires boto >= 2.26.0
    version_added: "1.9"
  tags:
    description:
      - tags dict to apply to a resource. Used with command=create, command=replicate, command=restore. Requires boto >= 2.26.0
    version_added: "1.9"
requirements:
    - "python >= 2.6"
    - "boto"
author:
    - "Bruce Pennypacker (@bpennypacker)"
    - "Will Thames (@willthames)"
extends_documentation_fragment:
    - aws
    - ec2
'''

# FIXME: the command stuff needs a 'state' like alias to make things consistent -- MPD

EXAMPLES = '''
# Basic mysql provisioning example
- rds:
    command: create
    instance_name: new-database
    db_engine: MySQL
    size: 10
    instance_type: db.m1.small
    username: mysql_admin
    password: 1nsecure
    tags:
      Environment: testing
      Application: cms

# Create a read-only replica and wait for it to become available
- rds:
    command: replicate
    instance_name: new-database-replica
    source_instance: new_database
    wait: yes
    wait_timeout: 600

# Delete an instance, but create a snapshot before doing so
- rds:
    command: delete
    instance_name: new-database
    snapshot: new_database_snapshot

# Get facts about an instance
- rds:
    command: facts
    instance_name: new-database
  register: new_database_facts

# Rename an instance and wait for the change to take effect
- rds:
    command: modify
    instance_name: new-database
    new_instance_name: renamed-database
    wait: yes

# Reboot an instance and wait for it to become available again
- rds:
    command: reboot
    instance_name: database
    wait: yes

# Restore a Postgres db instance from a snapshot, wait for it to become available again, and
#  then modify it to add your security group. Also, display the new endpoint.
#  Note that the "publicly_accessible" option is allowed here just as it is in the AWS CLI
- local_action:
     module: rds
     command: restore
     snapshot: mypostgres-snapshot
     instance_name: MyNewInstanceName
     region: us-west-2
     zone: us-west-2b
     subnet: default-vpc-xx441xxx
     publicly_accessible: yes
     wait: yes
     wait_timeout: 600
     tags:
         Name: pg1_test_name_tag
  register: rds

- local_action:
     module: rds
     command: modify
     instance_name: MyNewInstanceName
     region: us-west-2
     vpc_security_groups: sg-xxx945xx

- debug:
    msg: "The new db endpoint is {{ rds.instance.endpoint }}"
'''

RETURN = '''
instance:
    description: the rds instance
    returned: always
    type: complex
    contains:
        engine:
            description: the name of the database engine
            returned: when RDS instance exists
            type: string
            sample: "oracle-se"
        engine_version:
            description: the version of the database engine
            returned: when RDS instance exists
            type: string
            sample: "11.2.0.4.v6"
        license_model:
            description: the license model information
            returned: when RDS instance exists
            type: string
            sample: "bring-your-own-license"
        character_set_name:
            description: the name of the character set that this instance is associated with
            returned: when RDS instance exists
            type: string
            sample: "AL32UTF8"
        allocated_storage:
            description: the allocated storage size in gigabytes (GB)
            returned: when RDS instance exists
            type: string
            sample: "100"
        publicly_accessible:
            description: the accessibility options for the DB instance
            returned: when RDS instance exists
            type: boolean
            sample: "true"
        latest_restorable_time:
            description: the latest time to which a database can be restored with point-in-time restore
            returned: when RDS instance exists
            type: string
            sample: "1489707802.0"
        secondary_availability_zone:
            description: the name of the secondary AZ for a DB instance with multi-AZ support
            returned: when RDS instance exists and is multy-AZ
            type: string
            sample: "eu-west-1b"
        backup_window:
            description: the daily time range during which automated backups are created if automated backups are enabled
            returned: when RDS instance exists and automated backups are enabled
            type: string
            sample: "03:00-03:30"
        auto_minor_version_upgrade:
            description: indicates that minor engine upgrades will be applied automatically to the DB instance during the maintenance window
            returned: when RDS instance exists
            type: boolean
            sample: "true"
        read_replica_source_dbinstance_identifier:
            description: the identifier of the source DB instance if this RDS instance is a read replica
            returned: when read replica RDS instance exists
            type: string
            sample: "null"
        db_name:
            description: the name of the database to create when the DB instance is created
            returned: when RDS instance exists
            type: string
            sample: "ASERTG"
        endpoint:
            description: the endpoint uri of the database instance
            returned: when RDS instance exists
            type: string
            sample: "my-ansible-database.asdfaosdgih.us-east-1.rds.amazonaws.com"
        port:
            description: the listening port of the database instance
            returned: when RDS instance exists
            type: int
            sample: 3306
        parameter_groups:
            description: the list of DB parameter groups applied to this RDS instance
            returned: when RDS instance exists and parameter groups are defined
            type: complex
            contains:
                parameter_apply_status:
                    description: the status of parameter updates
                    returned: when RDS instance exists
                    type: string
                    sample: "in-sync"
                parameter_group_name:
                    description: the name of the DP parameter group
                    returned: when RDS instance exists
                    type: string
                    sample: "testawsrpprodb01spfile-1ujg7nrs7sgyz"
        option_groups:
            description: the list of option group memberships for this RDS instance
            returned: when RDS instance exists
            type: complex
            contains:
                option_group_name:
                    description: the option group name for this RDS instance
                    returned: when RDS instance exists
                    type: string
                    sample: "default:oracle-se-11-2"
                status:
                    description: the status of the RDS instance's option group membership
                    returned: when RDS instance exists
                    type: string
                    sample: "in-sync"
        pending_modified_values:
            description: a dictionary of changes to the RDS instance that are pending
            returned: when RDS instance exists
            type: complex
            contains:
                db_instance_class:
                    description: the new DB instance class for this RDS instance that will be applied or is in progress
                    returned: when RDS instance exists
                    type: string
                    sample: "null"
                db_instance_identifier:
                    description: the new DB instance identifier this RDS instance that will be applied or is in progress
                    returned: when RDS instance exists
                    type: string
                    sample: "null"
                allocated_storage:
                    description: the new allocated storage size for this RDS instance that will be applied or is in progress
                    returned: when RDS instance exists
                    type: string
                    sample: "null"
                backup_retention_period:
                    description: the pending number of days for which automated backups are retained
                    returned: when RDS instance exists
                    type: string
                    sample: "null"
                engine_version:
                    description: indicates the database engine version
                    returned: when RDS instance exists
                    type: string
                    sample: "null"
                iops:
                    description: the new provisioned IOPS value for this RDS instance that will be applied or is being applied
                    returned: when RDS instance exists
                    type: string
                    sample: "null"
                master_user_password:
                    description: the pending or in-progress change of the master credentials for this RDS instance
                    returned: when RDS instance exists
                    type: string
                    sample: "null"
                multi_az:
                    description: indicates that the single-AZ RDS instance is to change to a multi-AZ deployment
                    returned: when RDS instance exists
                    type: string
                    sample: "null"
                port:
                    description: specifies the pending port for this RDS instance
                    returned: when RDS instance exists
                    type: string
                    sample: "null"
        db_subnet_groups:
            description: information on the subnet group associated with this RDS instance
            returned: when RDS instance exists
            type: complex
            contains:
                description:
                    description: the subnet group associated with the DB instance
                    returned: when RDS instance exists
                    type: string
                    sample: "Subnets for the UAT RDS SQL DB Instance"
                name:
                    description: the name of the DB subnet group
                    returned: when RDS instance exists
                    type: string
                    sample: "samplesubnetgrouprds-j6paiqkxqp4z"
                status:
                    description: the status of the DB subnet group
                    returned: when RDS instance exists
                    type: string
                    sample: "complete"
                subnets:
                    description: the description of the DB subnet group
                    returned: when RDS instance exists
                    type: complex
                    contains:
                        availability_zone:
                            description: subnet availability zone information
                            returned: when RDS instance exists
                            type: complex
                            contains:
                                name:
                                    description: avaialbility zone
                                    returned: when RDS instance exists
                                    type: string
                                    sample: "eu-west-1b"
                                provisioned_iops_capable:
                                    description: whether provisioned iops are available in AZ subnet
                                    returned: when RDS instance exists
                                    type: boolean
                                    sample: "false"
                        identifier:
                            description: the identifier of the subnet
                            returned: when RDS instance exists
                            type: string
                            sample: "subnet-3fdba63e"
                        status:
                            description: the status of the subnet
                            returned: when RDS instance exists
                            type: string
                            sample: "active"
'''

import time

try:
    import boto.rds
    import boto.exception
except ImportError:
    pass  # Taken care of by ec2.HAS_BOTO

try:
    import boto.rds2
    import boto.rds2.exceptions
    HAS_RDS2 = True
except ImportError:
    HAS_RDS2 = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import AWSRetry
from ansible.module_utils.ec2 import HAS_BOTO, connect_to_aws, ec2_argument_spec, get_aws_connection_info


DEFAULT_PORTS = {
    'aurora': 3306,
    'mariadb': 3306,
    'mysql': 3306,
    'oracle': 1521,
    'sqlserver': 1433,
    'postgres': 5432,
}


class RDSException(Exception):
    def __init__(self, exc):
        if hasattr(exc, 'error_message') and exc.error_message:
            self.message = exc.error_message
            self.code = exc.error_code
        elif hasattr(exc, 'body') and 'Error' in exc.body:
            self.message = exc.body['Error']['Message']
            self.code = exc.body['Error']['Code']
        else:
            self.message = str(exc)
            self.code = 'Unknown Error'


class RDSConnection:
    def __init__(self, module, region, **aws_connect_params):
        try:
            self.connection = connect_to_aws(boto.rds, region, **aws_connect_params)
        except boto.exception.BotoServerError as e:
            module.fail_json(msg=e.error_message)

    def get_db_instance(self, instancename):
        try:
            return RDSDBInstance(self.connection.get_all_dbinstances(instancename)[0])
        except boto.exception.BotoServerError:
            return None

    def get_db_snapshot(self, snapshotid):
        try:
            return RDSSnapshot(self.connection.get_all_dbsnapshots(snapshot_id=snapshotid)[0])
        except boto.exception.BotoServerError:
            return None

    def create_db_instance(self, instance_name, size, instance_class, db_engine,
                           username, password, **params):
        params['engine'] = db_engine
        try:
            result = self.connection.create_dbinstance(instance_name, size, instance_class,
                                                       username, password, **params)
            return RDSDBInstance(result)
        except boto.exception.BotoServerError as e:
            raise RDSException(e)

    def create_db_instance_read_replica(self, instance_name, source_instance, **params):
        try:
            result = self.connection.createdb_instance_read_replica(instance_name, source_instance, **params)
            return RDSDBInstance(result)
        except boto.exception.BotoServerError as e:
            raise RDSException(e)

    def delete_db_instance(self, instance_name, **params):
        try:
            result = self.connection.delete_dbinstance(instance_name, **params)
            return RDSDBInstance(result)
        except boto.exception.BotoServerError as e:
            raise RDSException(e)

    def delete_db_snapshot(self, snapshot):
        try:
            result = self.connection.delete_dbsnapshot(snapshot)
            return RDSSnapshot(result)
        except boto.exception.BotoServerError as e:
            raise RDSException(e)

    def modify_db_instance(self, instance_name, **params):
        try:
            result = self.connection.modify_dbinstance(instance_name, **params)
            return RDSDBInstance(result)
        except boto.exception.BotoServerError as e:
            raise RDSException(e)

    def reboot_db_instance(self, instance_name, **params):
        try:
            result = self.connection.reboot_dbinstance(instance_name)
            return RDSDBInstance(result)
        except boto.exception.BotoServerError as e:
            raise RDSException(e)

    def restore_db_instance_from_db_snapshot(self, instance_name, snapshot, instance_type, **params):
        try:
            result = self.connection.restore_dbinstance_from_dbsnapshot(snapshot, instance_name, instance_type, **params)
            return RDSDBInstance(result)
        except boto.exception.BotoServerError as e:
            raise RDSException(e)

    def create_db_snapshot(self, snapshot, instance_name, **params):
        try:
            result = self.connection.create_dbsnapshot(snapshot, instance_name)
            return RDSSnapshot(result)
        except boto.exception.BotoServerError as e:
            raise RDSException(e)

    def promote_read_replica(self, instance_name, **params):
        try:
            result = self.connection.promote_read_replica(instance_name, **params)
            return RDSDBInstance(result)
        except boto.exception.BotoServerError as e:
            raise RDSException(e)


class RDS2Connection:
    def __init__(self, module, region, **aws_connect_params):
        try:
            self.connection = connect_to_aws(boto.rds2, region, **aws_connect_params)
        except boto.exception.BotoServerError as e:
            module.fail_json(msg=e.error_message)

    def get_db_instance(self, instancename):
        try:
            dbinstances = self.connection.describe_db_instances(
                db_instance_identifier=instancename
            )['DescribeDBInstancesResponse']['DescribeDBInstancesResult']['DBInstances']
            result = RDS2DBInstance(dbinstances[0])
            return result
        except boto.rds2.exceptions.DBInstanceNotFound as e:
            return None
        except Exception as e:
            raise e

    def get_db_snapshot(self, snapshotid):
        try:
            snapshots = self.connection.describe_db_snapshots(
                db_snapshot_identifier=snapshotid,
                snapshot_type='manual'
            )['DescribeDBSnapshotsResponse']['DescribeDBSnapshotsResult']['DBSnapshots']
            result = RDS2Snapshot(snapshots[0])
            return result
        except boto.rds2.exceptions.DBSnapshotNotFound:
            return None

    def create_db_instance(self, instance_name, size, instance_class, db_engine,
                           username, password, **params):
        try:
            result = self.connection.create_db_instance(instance_name, size, instance_class, db_engine, username, password,
                                                        **params)['CreateDBInstanceResponse']['CreateDBInstanceResult']['DBInstance']
            return RDS2DBInstance(result)
        except boto.exception.BotoServerError as e:
            raise RDSException(e)

    def create_db_instance_read_replica(self, instance_name, source_instance, **params):
        try:
            result = self.connection.create_db_instance_read_replica(
                instance_name,
                source_instance,
                **params
            )['CreateDBInstanceReadReplicaResponse']['CreateDBInstanceReadReplicaResult']['DBInstance']
            return RDS2DBInstance(result)
        except boto.exception.BotoServerError as e:
            raise RDSException(e)

    def delete_db_instance(self, instance_name, **params):
        try:
            result = self.connection.delete_db_instance(instance_name, **params)['DeleteDBInstanceResponse']['DeleteDBInstanceResult']['DBInstance']
            return RDS2DBInstance(result)
        except boto.exception.BotoServerError as e:
            raise RDSException(e)

    def delete_db_snapshot(self, snapshot):
        try:
            result = self.connection.delete_db_snapshot(snapshot)['DeleteDBSnapshotResponse']['DeleteDBSnapshotResult']['DBSnapshot']
            return RDS2Snapshot(result)
        except boto.exception.BotoServerError as e:
            raise RDSException(e)

    def modify_db_instance(self, instance_name, **params):
        try:
            result = self.connection.modify_db_instance(instance_name, **params)['ModifyDBInstanceResponse']['ModifyDBInstanceResult']['DBInstance']
            return RDS2DBInstance(result)
        except boto.exception.BotoServerError as e:
            raise RDSException(e)

    def reboot_db_instance(self, instance_name, **params):
        try:
            result = self.connection.reboot_db_instance(instance_name, **params)['RebootDBInstanceResponse']['RebootDBInstanceResult']['DBInstance']
            return RDS2DBInstance(result)
        except boto.exception.BotoServerError as e:
            raise RDSException(e)

    def restore_db_instance_from_db_snapshot(self, instance_name, snapshot, instance_type, **params):
        try:
            result = self.connection.restore_db_instance_from_db_snapshot(
                instance_name,
                snapshot,
                **params
            )['RestoreDBInstanceFromDBSnapshotResponse']['RestoreDBInstanceFromDBSnapshotResult']['DBInstance']
            return RDS2DBInstance(result)
        except boto.exception.BotoServerError as e:
            raise RDSException(e)

    def create_db_snapshot(self, snapshot, instance_name, **params):
        try:
            result = self.connection.create_db_snapshot(snapshot, instance_name, **params)['CreateDBSnapshotResponse']['CreateDBSnapshotResult']['DBSnapshot']
            return RDS2Snapshot(result)
        except boto.exception.BotoServerError as e:
            raise RDSException(e)

    def promote_read_replica(self, instance_name, **params):
        try:
            result = self.connection.promote_read_replica(instance_name, **params)['PromoteReadReplicaResponse']['PromoteReadReplicaResult']['DBInstance']
            return RDS2DBInstance(result)
        except boto.exception.BotoServerError as e:
            raise RDSException(e)


class RDSDBInstance:
    def __init__(self, dbinstance):
        self.instance = dbinstance
        self.name = dbinstance.id
        self.status = dbinstance.status

    def get_data(self):
        d = {
            'id': self.name,
            'create_time': self.instance.create_time,
            'status': self.status,
            'availability_zone': self.instance.availability_zone,
            'backup_retention': self.instance.backup_retention_period,
            'backup_window': self.instance.preferred_backup_window,
            'maintenance_window': self.instance.preferred_maintenance_window,
            'multi_zone': self.instance.multi_az,
            'instance_type': self.instance.instance_class,
            'username': self.instance.master_username,
            'iops': self.instance.iops
        }

        # Only assign an Endpoint if one is available
        if hasattr(self.instance, 'endpoint'):
            d["endpoint"] = self.instance.endpoint[0]
            d["port"] = self.instance.endpoint[1]
            if self.instance.vpc_security_groups is not None:
                d["vpc_security_groups"] = ','.join(x.vpc_group for x in self.instance.vpc_security_groups)
            else:
                d["vpc_security_groups"] = None
        else:
            d["endpoint"] = None
            d["port"] = None
            d["vpc_security_groups"] = None
        d['DBName'] = self.instance.DBName if hasattr(self.instance, 'DBName') else None
        # ReadReplicaSourceDBInstanceIdentifier may or may not exist
        try:
            d["replication_source"] = self.instance.ReadReplicaSourceDBInstanceIdentifier
        except Exception:
            d["replication_source"] = None
        return d


class RDS2DBInstance:
    def __init__(self, dbinstance):
        self.instance = dbinstance
        if 'DBInstanceIdentifier' not in dbinstance:
            self.name = None
        else:
            self.name = self.instance.get('DBInstanceIdentifier')
        self.status = self.instance.get('DBInstanceStatus')

    def get_data(self):
        d = {
            'id': self.name,
            'create_time': self.instance['InstanceCreateTime'],
            'engine': self.instance['Engine'],
            'engine_version': self.instance['EngineVersion'],
            'license_model': self.instance['LicenseModel'],
            'character_set_name': self.instance['CharacterSetName'],
            'allocated_storage': self.instance['AllocatedStorage'],
            'publicly_accessible': self.instance['PubliclyAccessible'],
            'latest_restorable_time': self.instance['LatestRestorableTime'],
            'status': self.status,
            'availability_zone': self.instance['AvailabilityZone'],
            'secondary_availability_zone': self.instance['SecondaryAvailabilityZone'],
            'backup_retention': self.instance['BackupRetentionPeriod'],
            'backup_window': self.instance['PreferredBackupWindow'],
            'maintenance_window': self.instance['PreferredMaintenanceWindow'],
            'auto_minor_version_upgrade': self.instance['AutoMinorVersionUpgrade'],
            'read_replica_source_dbinstance_identifier': self.instance['ReadReplicaSourceDBInstanceIdentifier'],
            'multi_zone': self.instance['MultiAZ'],
            'instance_type': self.instance['DBInstanceClass'],
            'username': self.instance['MasterUsername'],
            'db_name': self.instance['DBName'],
            'iops': self.instance['Iops'],
            'replication_source': self.instance['ReadReplicaSourceDBInstanceIdentifier']
        }
        if self.instance['DBParameterGroups'] is not None:
            parameter_groups = []
            for x in self.instance['DBParameterGroups']:
                parameter_groups.append({'parameter_group_name': x['DBParameterGroupName'], 'parameter_apply_status': x['ParameterApplyStatus']})
            d['parameter_groups'] = parameter_groups
        if self.instance['OptionGroupMemberships'] is not None:
            option_groups = []
            for x in self.instance['OptionGroupMemberships']:
                option_groups.append({'status': x['Status'], 'option_group_name': x['OptionGroupName']})
            d['option_groups'] = option_groups
        if self.instance['PendingModifiedValues'] is not None:
            pdv = self.instance['PendingModifiedValues']
            d['pending_modified_values'] = {
                'multi_az': pdv['MultiAZ'],
                'master_user_password': pdv['MasterUserPassword'],
                'port': pdv['Port'],
                'iops': pdv['Iops'],
                'allocated_storage': pdv['AllocatedStorage'],
                'engine_version': pdv['EngineVersion'],
                'backup_retention_period': pdv['BackupRetentionPeriod'],
                'db_instance_class': pdv['DBInstanceClass'],
                'db_instance_identifier': pdv['DBInstanceIdentifier']
            }
        if self.instance["DBSubnetGroup"] is not None:
            dsg = self.instance["DBSubnetGroup"]
            db_subnet_groups = {}
            db_subnet_groups['vpc_id'] = dsg['VpcId']
            db_subnet_groups['name'] = dsg['DBSubnetGroupName']
            db_subnet_groups['status'] = dsg['SubnetGroupStatus'].lower()
            db_subnet_groups['description'] = dsg['DBSubnetGroupDescription']
            db_subnet_groups['subnets'] = []
            for x in dsg["Subnets"]:
                db_subnet_groups['subnets'].append({
                    'status': x['SubnetStatus'].lower(),
                    'identifier': x['SubnetIdentifier'],
                    'availability_zone': {
                        'name': x['SubnetAvailabilityZone']['Name'],
                        'provisioned_iops_capable': x['SubnetAvailabilityZone']['ProvisionedIopsCapable']
                    }
                })
            d['db_subnet_groups'] = db_subnet_groups
        if self.instance["VpcSecurityGroups"] is not None:
            d['vpc_security_groups'] = ','.join(x['VpcSecurityGroupId'] for x in self.instance['VpcSecurityGroups'])
        if "Endpoint" in self.instance and self.instance["Endpoint"] is not None:
            d['endpoint'] = self.instance["Endpoint"].get('Address', None)
            d['port'] = self.instance["Endpoint"].get('Port', None)
        else:
            d['endpoint'] = None
            d['port'] = None
        d['DBName'] = self.instance['DBName'] if hasattr(self.instance, 'DBName') else None
        return d


class RDSSnapshot:
    def __init__(self, snapshot):
        self.snapshot = snapshot
        self.name = snapshot.id
        self.status = snapshot.status

    def get_data(self):
        d = {
            'id': self.name,
            'create_time': self.snapshot.snapshot_create_time,
            'status': self.status,
            'availability_zone': self.snapshot.availability_zone,
            'instance_id': self.snapshot.instance_id,
            'instance_created': self.snapshot.instance_create_time,
        }
        # needs boto >= 2.21.0
        if hasattr(self.snapshot, 'snapshot_type'):
            d["snapshot_type"] = self.snapshot.snapshot_type
        if hasattr(self.snapshot, 'iops'):
            d["iops"] = self.snapshot.iops
        return d


class RDS2Snapshot:
    def __init__(self, snapshot):
        if 'DeleteDBSnapshotResponse' in snapshot:
            self.snapshot = snapshot['DeleteDBSnapshotResponse']['DeleteDBSnapshotResult']['DBSnapshot']
        else:
            self.snapshot = snapshot
        self.name = self.snapshot.get('DBSnapshotIdentifier')
        self.status = self.snapshot.get('Status')

    def get_data(self):
        d = {
            'id': self.name,
            'create_time': self.snapshot['SnapshotCreateTime'],
            'status': self.status,
            'availability_zone': self.snapshot['AvailabilityZone'],
            'instance_id': self.snapshot['DBInstanceIdentifier'],
            'instance_created': self.snapshot['InstanceCreateTime'],
            'snapshot_type': self.snapshot['SnapshotType'],
            'iops': self.snapshot['Iops'],
        }
        return d


def await_resource(conn, resource, status, module):
    start_time = time.time()
    wait_timeout = module.params.get('wait_timeout') + start_time
    check_interval = 5
    while wait_timeout > time.time() and resource.status != status:
        time.sleep(check_interval)
        if wait_timeout <= time.time():
            module.fail_json(msg="Timeout waiting for RDS resource %s" % resource.name)
        if module.params.get('command') == 'snapshot':
            # Temporary until all the rds2 commands have their responses parsed
            if resource.name is None:
                module.fail_json(msg="There was a problem waiting for RDS snapshot %s" % resource.snapshot)
            # Back off if we're getting throttled, since we're just waiting anyway
            resource = AWSRetry.backoff(tries=5, delay=20, backoff=1.5)(conn.get_db_snapshot)(resource.name)
        else:
            # Temporary until all the rds2 commands have their responses parsed
            if resource.name is None:
                module.fail_json(msg="There was a problem waiting for RDS instance %s" % resource.instance)
            # Back off if we're getting throttled, since we're just waiting anyway
            resource = AWSRetry.backoff(tries=5, delay=20, backoff=1.5)(conn.get_db_instance)(resource.name)
            if resource is None:
                break
        # Some RDS resources take much longer than others to be ready. Check
        # less aggressively for slow ones to avoid throttling.
        if time.time() > start_time + 90:
            check_interval = 20
    return resource


def create_db_instance(module, conn):
    required_vars = ['instance_name', 'db_engine', 'size', 'instance_type', 'username', 'password']
    valid_vars = ['backup_retention', 'backup_window',
                  'character_set_name', 'db_name', 'engine_version',
                  'instance_type', 'iops', 'license_model', 'maint_window',
                  'multi_zone', 'option_group', 'parameter_group', 'port',
                  'subnet', 'upgrade', 'zone']
    if module.params.get('subnet'):
        valid_vars.append('vpc_security_groups')
    else:
        valid_vars.append('security_groups')
    if HAS_RDS2:
        valid_vars.extend(['publicly_accessible', 'tags'])
    params = validate_parameters(required_vars, valid_vars, module)
    instance_name = module.params.get('instance_name')

    result = conn.get_db_instance(instance_name)
    if result:
        changed = False
    else:
        try:
            result = conn.create_db_instance(instance_name, module.params.get('size'),
                                             module.params.get('instance_type'), module.params.get('db_engine'),
                                             module.params.get('username'), module.params.get('password'), **params)
            changed = True
        except RDSException as e:
            module.fail_json(msg="Failed to create instance: %s" % e.message)

    if module.params.get('wait'):
        resource = await_resource(conn, result, 'available', module)
    else:
        resource = conn.get_db_instance(instance_name)

    module.exit_json(changed=changed, instance=resource.get_data())


def replicate_db_instance(module, conn):
    required_vars = ['instance_name', 'source_instance']
    valid_vars = ['instance_type', 'port', 'upgrade', 'zone']
    if HAS_RDS2:
        valid_vars.extend(['iops', 'option_group', 'publicly_accessible', 'tags'])
    params = validate_parameters(required_vars, valid_vars, module)
    instance_name = module.params.get('instance_name')
    source_instance = module.params.get('source_instance')

    result = conn.get_db_instance(instance_name)
    if result:
        changed = False
    else:
        try:
            result = conn.create_db_instance_read_replica(instance_name, source_instance, **params)
            changed = True
        except RDSException as e:
            module.fail_json(msg="Failed to create replica instance: %s " % e.message)

    if module.params.get('wait'):
        resource = await_resource(conn, result, 'available', module)
    else:
        resource = conn.get_db_instance(instance_name)

    module.exit_json(changed=changed, instance=resource.get_data())


def delete_db_instance_or_snapshot(module, conn):
    required_vars = []
    valid_vars = ['instance_name', 'snapshot', 'skip_final_snapshot']
    params = validate_parameters(required_vars, valid_vars, module)
    instance_name = module.params.get('instance_name')
    snapshot = module.params.get('snapshot')

    if not instance_name:
        result = conn.get_db_snapshot(snapshot)
    else:
        result = conn.get_db_instance(instance_name)
    if not result:
        module.exit_json(changed=False)
    if result.status == 'deleting':
        module.exit_json(changed=False)
    try:
        if instance_name:
            if snapshot:
                params["skip_final_snapshot"] = False
                if HAS_RDS2:
                    params["final_db_snapshot_identifier"] = snapshot
                else:
                    params["final_snapshot_id"] = snapshot
            else:
                params["skip_final_snapshot"] = True
            result = conn.delete_db_instance(instance_name, **params)
        else:
            result = conn.delete_db_snapshot(snapshot)
    except RDSException as e:
        module.fail_json(msg="Failed to delete instance: %s" % e.message)

    # If we're not waiting for a delete to complete then we're all done
    # so just return
    if not module.params.get('wait'):
        module.exit_json(changed=True)
    try:
        await_resource(conn, result, 'deleted', module)
        module.exit_json(changed=True)
    except RDSException as e:
        if e.code == 'DBInstanceNotFound':
            module.exit_json(changed=True)
        else:
            module.fail_json(msg=e.message)
    except Exception as e:
        module.fail_json(msg=str(e))


def facts_db_instance_or_snapshot(module, conn):
    instance_name = module.params.get('instance_name')
    snapshot = module.params.get('snapshot')

    if instance_name and snapshot:
        module.fail_json(msg="Facts must be called with either instance_name or snapshot, not both")
    if instance_name:
        resource = conn.get_db_instance(instance_name)
        if not resource:
            module.fail_json(msg="DB instance %s does not exist" % instance_name)
    if snapshot:
        resource = conn.get_db_snapshot(snapshot)
        if not resource:
            module.fail_json(msg="DB snapshot %s does not exist" % snapshot)

    module.exit_json(changed=False, instance=resource.get_data())


def modify_db_instance(module, conn):
    required_vars = ['instance_name']
    valid_vars = ['apply_immediately', 'backup_retention', 'backup_window',
                  'db_name', 'engine_version', 'instance_type', 'iops', 'license_model',
                  'maint_window', 'multi_zone', 'new_instance_name',
                  'option_group', 'parameter_group', 'password', 'size', 'upgrade']

    params = validate_parameters(required_vars, valid_vars, module)
    instance_name = module.params.get('instance_name')
    new_instance_name = module.params.get('new_instance_name')

    try:
        result = conn.modify_db_instance(instance_name, **params)
    except RDSException as e:
        module.fail_json(msg=e.message)
    if params.get('apply_immediately'):
        if new_instance_name:
            # Wait until the new instance name is valid
            new_instance = None
            while not new_instance:
                new_instance = conn.get_db_instance(new_instance_name)
                time.sleep(5)

            # Found instance but it briefly flicks to available
            # before rebooting so let's wait until we see it rebooting
            # before we check whether to 'wait'
            result = await_resource(conn, new_instance, 'rebooting', module)

    if module.params.get('wait'):
        resource = await_resource(conn, result, 'available', module)
    else:
        resource = conn.get_db_instance(instance_name)

    # guess that this changed the DB, need a way to check
    module.exit_json(changed=True, instance=resource.get_data())


def promote_db_instance(module, conn):
    required_vars = ['instance_name']
    valid_vars = ['backup_retention', 'backup_window']
    params = validate_parameters(required_vars, valid_vars, module)
    instance_name = module.params.get('instance_name')

    result = conn.get_db_instance(instance_name)
    if not result:
        module.fail_json(msg="DB Instance %s does not exist" % instance_name)

    if result.get_data().get('replication_source'):
        try:
            result = conn.promote_read_replica(instance_name, **params)
            changed = True
        except RDSException as e:
            module.fail_json(msg=e.message)
    else:
        changed = False

    if module.params.get('wait'):
        resource = await_resource(conn, result, 'available', module)
    else:
        resource = conn.get_db_instance(instance_name)

    module.exit_json(changed=changed, instance=resource.get_data())


def snapshot_db_instance(module, conn):
    required_vars = ['instance_name', 'snapshot']
    valid_vars = ['tags']
    params = validate_parameters(required_vars, valid_vars, module)
    instance_name = module.params.get('instance_name')
    snapshot = module.params.get('snapshot')
    changed = False
    result = conn.get_db_snapshot(snapshot)
    if not result:
        try:
            result = conn.create_db_snapshot(snapshot, instance_name, **params)
            changed = True
        except RDSException as e:
            module.fail_json(msg=e.message)

    if module.params.get('wait'):
        resource = await_resource(conn, result, 'available', module)
    else:
        resource = conn.get_db_snapshot(snapshot)

    module.exit_json(changed=changed, snapshot=resource.get_data())


def reboot_db_instance(module, conn):
    required_vars = ['instance_name']
    valid_vars = []

    if HAS_RDS2:
        valid_vars.append('force_failover')

    params = validate_parameters(required_vars, valid_vars, module)
    instance_name = module.params.get('instance_name')
    result = conn.get_db_instance(instance_name)
    changed = False
    try:
        result = conn.reboot_db_instance(instance_name, **params)
        changed = True
    except RDSException as e:
        module.fail_json(msg=e.message)

    if module.params.get('wait'):
        resource = await_resource(conn, result, 'available', module)
    else:
        resource = conn.get_db_instance(instance_name)

    module.exit_json(changed=changed, instance=resource.get_data())


def restore_db_instance(module, conn):
    required_vars = ['instance_name', 'snapshot']
    valid_vars = ['db_name', 'iops', 'license_model', 'multi_zone',
                  'option_group', 'port', 'publicly_accessible',
                  'subnet', 'tags', 'upgrade', 'zone']
    if HAS_RDS2:
        valid_vars.append('instance_type')
    else:
        required_vars.append('instance_type')
    params = validate_parameters(required_vars, valid_vars, module)
    instance_name = module.params.get('instance_name')
    instance_type = module.params.get('instance_type')
    snapshot = module.params.get('snapshot')

    changed = False
    result = conn.get_db_instance(instance_name)
    if not result:
        try:
            result = conn.restore_db_instance_from_db_snapshot(instance_name, snapshot, instance_type, **params)
            changed = True
        except RDSException as e:
            module.fail_json(msg=e.message)

    if module.params.get('wait'):
        resource = await_resource(conn, result, 'available', module)
    else:
        resource = conn.get_db_instance(instance_name)

    module.exit_json(changed=changed, instance=resource.get_data())


def validate_parameters(required_vars, valid_vars, module):
    command = module.params.get('command')
    for v in required_vars:
        if not module.params.get(v):
            module.fail_json(msg="Parameter %s required for %s command" % (v, command))

    # map to convert rds module options to boto rds and rds2 options
    optional_params = {
        'port': 'port',
        'db_name': 'db_name',
        'zone': 'availability_zone',
        'maint_window': 'preferred_maintenance_window',
        'backup_window': 'preferred_backup_window',
        'backup_retention': 'backup_retention_period',
        'multi_zone': 'multi_az',
        'engine_version': 'engine_version',
        'upgrade': 'auto_minor_version_upgrade',
        'subnet': 'db_subnet_group_name',
        'license_model': 'license_model',
        'option_group': 'option_group_name',
        'size': 'allocated_storage',
        'iops': 'iops',
        'new_instance_name': 'new_instance_id',
        'apply_immediately': 'apply_immediately',
    }
    # map to convert rds module options to boto rds options
    optional_params_rds = {
        'db_engine': 'engine',
        'password': 'master_password',
        'parameter_group': 'param_group',
        'instance_type': 'instance_class',
    }
    # map to convert rds module options to boto rds2 options
    optional_params_rds2 = {
        'tags': 'tags',
        'publicly_accessible': 'publicly_accessible',
        'parameter_group': 'db_parameter_group_name',
        'character_set_name': 'character_set_name',
        'instance_type': 'db_instance_class',
        'password': 'master_user_password',
        'new_instance_name': 'new_db_instance_identifier',
        'force_failover': 'force_failover',
    }
    if HAS_RDS2:
        optional_params.update(optional_params_rds2)
        sec_group = 'db_security_groups'
    else:
        optional_params.update(optional_params_rds)
        sec_group = 'security_groups'
        # Check for options only supported with rds2
        for k in set(optional_params_rds2.keys()) - set(optional_params_rds.keys()):
            if module.params.get(k):
                module.fail_json(msg="Parameter %s requires boto.rds (boto >= 2.26.0)" % k)

    params = {}
    for (k, v) in optional_params.items():
        if module.params.get(k) is not None and k not in required_vars:
            if k in valid_vars:
                params[v] = module.params[k]
            else:
                if module.params.get(k) is False:
                    pass
                else:
                    module.fail_json(msg="Parameter %s is not valid for %s command" % (k, command))

    if module.params.get('security_groups'):
        params[sec_group] = module.params.get('security_groups').split(',')

    vpc_groups = module.params.get('vpc_security_groups')
    if vpc_groups:
        if HAS_RDS2:
            params['vpc_security_group_ids'] = vpc_groups
        else:
            groups_list = []
            for x in vpc_groups:
                groups_list.append(boto.rds.VPCSecurityGroupMembership(vpc_group=x))
            params['vpc_security_groups'] = groups_list

    # Convert tags dict to list of tuples that rds2 expects
    if 'tags' in params:
        params['tags'] = module.params['tags'].items()
    return params


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        command=dict(choices=['create', 'replicate', 'delete', 'facts', 'modify', 'promote', 'snapshot', 'reboot', 'restore'], required=True),
        instance_name=dict(required=False),
        source_instance=dict(required=False),
        db_engine=dict(choices=['mariadb', 'MySQL', 'oracle-se1', 'oracle-se2', 'oracle-se', 'oracle-ee', 'sqlserver-ee', 'sqlserver-se', 'sqlserver-ex',
                                'sqlserver-web', 'postgres', 'aurora'], required=False),
        size=dict(required=False),
        instance_type=dict(aliases=['type'], required=False),
        username=dict(required=False),
        password=dict(no_log=True, required=False),
        db_name=dict(required=False),
        engine_version=dict(required=False),
        parameter_group=dict(required=False),
        license_model=dict(choices=['license-included', 'bring-your-own-license', 'general-public-license', 'postgresql-license'], required=False),
        multi_zone=dict(type='bool', required=False),
        iops=dict(required=False),
        security_groups=dict(required=False),
        vpc_security_groups=dict(type='list', required=False),
        port=dict(required=False, type='int'),
        upgrade=dict(type='bool', default=False),
        option_group=dict(required=False),
        maint_window=dict(required=False),
        backup_window=dict(required=False),
        backup_retention=dict(required=False),
        zone=dict(aliases=['aws_zone', 'ec2_zone'], required=False),
        subnet=dict(required=False),
        wait=dict(type='bool', default=False),
        wait_timeout=dict(type='int', default=300),
        snapshot=dict(required=False),
        apply_immediately=dict(type='bool', default=False),
        new_instance_name=dict(required=False),
        tags=dict(type='dict', required=False),
        publicly_accessible=dict(required=False),
        character_set_name=dict(required=False),
        force_failover=dict(type='bool', required=False, default=False)
    )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    invocations = {
        'create': create_db_instance,
        'replicate': replicate_db_instance,
        'delete': delete_db_instance_or_snapshot,
        'facts': facts_db_instance_or_snapshot,
        'modify': modify_db_instance,
        'promote': promote_db_instance,
        'snapshot': snapshot_db_instance,
        'reboot': reboot_db_instance,
        'restore': restore_db_instance,
    }

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)
    if not region:
        module.fail_json(msg="Region must be specified as a parameter, in EC2_REGION or AWS_REGION environment variables or in boto configuration file")

    # set port to per db defaults if not specified
    if module.params['port'] is None and module.params['db_engine'] is not None and module.params['command'] == 'create':
        if '-' in module.params['db_engine']:
            engine = module.params['db_engine'].split('-')[0]
        else:
            engine = module.params['db_engine']
        module.params['port'] = DEFAULT_PORTS[engine.lower()]

    # connect to the rds endpoint
    if HAS_RDS2:
        conn = RDS2Connection(module, region, **aws_connect_params)
    else:
        conn = RDSConnection(module, region, **aws_connect_params)

    invocations[module.params.get('command')](module, conn)


if __name__ == '__main__':
    main()
