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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: rds_instance
short_description: create, delete, or modify an Amazon rds instance
description:
     - Creates, deletes, or modifies rds instances. When creating an instance
       it can be either a new instance or a read-only replica of an existing instance.
requirements:
    - "python >= 2.6"
    - "boto3"
version_added: "2.4"
author:
    - Bruce Pennypacker (@bpennypacker)
    - Will Thames (@willthames)
    - Michael De La Rue (@mikedlr)
options:
  state:
    description:
      - Describes the desired state of the database instance. N.B. restarted is allowed as an alias for rebooted.
    required: false
    default: present
    choices: [ 'present', 'absent', 'rebooted' ]
  instance_name:
    description:
      - Database instance identifier.
    required: true
  source_instance:
    description:
      - Name of the database when sourcing from a replica
    required: false
  replica:
    description:
    - whether or not a database is a read replica
    default: False
  db_engine:
    description:
      - The type of database. Used only when state=present.
    required: false
    choices: [ 'mariadb', 'MySQL', 'oracle-se1', 'oracle-se2', 'oracle-se', 'oracle-ee', 'sqlserver-ee',
                sqlserver-se', 'sqlserver-ex', 'sqlserver-web', 'postgres', 'aurora']
  size:
    description:
      - Size in gigabytes of the initial storage for the DB instance.
    required: false
  storage_type:
    description:
      - Specifies the storage type to be associated with the DB instance. C(iops) must
        be specified if C(io1) is chosen.
    choices: ['standard', 'gp2', 'io1' ]
    default: standard unless iops is set
  instance_type:
    description:
      - The instance type of the database. If source_instance is specified then the replica inherits
        the same instance type as the source instance.
  username:
    description:
      - Master database username.
  password:
    description:
      - Password for the master database username.
  db_name:
    description:
      - Name of a database to create within the instance. If not specified then no database is created.
  engine_version:
    description:
      - Version number of the database engine to use. If not specified then the current Amazon RDS default engine version is used.
  parameter_group:
    description:
      - Name of the DB parameter group to associate with this instance. If omitted then the RDS default DBParameterGroup will be used.
    required: false
  license_model:
    description:
      - The license model for this DB instance.
    required: false
    choices:  [ 'license-included', 'bring-your-own-license', 'general-public-license', 'postgresql-license' ]
  multi_zone:
    description:
      - Specifies if this is a Multi-availability-zone deployment. Can not be used in conjunction with zone parameter.
    choices: [ "yes", "no" ]
    required: false
  iops:
    description:
      - Specifies the number of IOPS for the instance. Must be an integer greater than 1000.
    required: false
  security_groups:
    description: Comma separated list of one or more security groups.
    required: false
  vpc_security_groups:
    description: Comma separated list of one or more vpc security group ids. Also requires `subnet` to be specified.
    required: false
  port:
    description: Port number that the DB instance uses for connections.
    required: false
    default: 3306 for mysql, 1521 for Oracle, 1433 for SQL Server, 5432 for PostgreSQL.
  upgrade:
    description: Indicates that minor version upgrades should be applied automatically.
    required: false
    default: no
    choices: [ "yes", "no" ]
  option_group:
    description: The name of the option group to use. If not specified then the default option group is used.
    required: false
  maint_window:
    description: "Maintenance window in format of ddd:hh24:mi-ddd:hh24:mi (Example: Mon:22:00-Mon:23:15). If not specified then AWS will assign a random maintenance window."
    required: false
  backup_window:
    description: "Backup window in format of hh24:mi-hh24:mi (Example: 04:00-05:45). If not specified then AWS will assign a random backup window."
    required: false
  backup_retention:
    description: "Number of days backups are retained. Set to 0 to disable backups. Default is 1 day. Valid range: 0-35."
    required: false
  zone:
    description:
      - availability zone in which to launch the instance.
    required: false
    aliases: ['aws_zone', 'ec2_zone']
  subnet:
    description:
      - VPC subnet group. If specified then a VPC instance is created.
    required: false
  snapshot:
    description:
      - Name of snapshot to take when state=absent - if no snapshot name is provided then no snapshot is taken.
    required: false
  wait:
    description:
      - Wait for the database to enter the desired state.
    required: false
    default: "no"
    choices: [ "yes", "no" ]
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 300
  apply_immediately:
    description:
      - If enabled, the modifications will be applied as soon as possible rather than waiting for the next preferred maintenance window.
    default: no
    choices: [ "yes", "no" ]
  force_failover:
    description:
      - Used only when state=rebooted. If enabled, the reboot is done using a MultiAZ failover.
    required: false
    default: "no"
    choices: [ "yes", "no" ]
  force_password_update:
    description:
      - Whether to try to update the DB password for an existing database. There is no API method to
        determine whether or not a password will be updated, and it causes problems with later operations
        if a password is updated unnecessarily.
    default: "no"
    choices: [ "yes", "no" ]
  old_instance_name:
    description:
      - Name to rename an instance from.
    required: false
  character_set_name:
    description:
      - Associate the DB instance with a specified character set.
    required: false
  publicly_accessible:
    description:
      - explicitly set whether the resource should be publicly accessible or not.
    required: false
  cluster:
    description:
      -  The identifier of the DB cluster that the instance will belong to.
    required: false
  tags:
    description:
      - tags dict to apply to a resource.
    required: false
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Basic mysql provisioning example
- rds_instance:
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
- rds_instance:
    instance_name: new-database-replica
    source_instance: new_database
    wait: yes
    wait_timeout: 600

# Promote the read replica to a standalone database by removing
# the source_instance setting
- rds_instance:
    instance_name: new-database-replica
    wait: yes
    wait_timeout: 600

# Delete an instance, but create a snapshot before doing so
- rds_instance:
    state: absent
    instance_name: new-database
    snapshot: new_database_snapshot

# Rename an instance and wait for the change to take effect
- rds_instance:
    old_instance_name: new-database
    instance_name: renamed-database
    wait: yes

# Reboot an instance and wait for it to become available again
- rds_instance:
    state: rebooted
    instance_name: database
    wait: yes

# Restore a Postgres db instance from a snapshot, wait for it to become available again, and
#  then modify it to add your security group. Also, display the new endpoint.
#  Note that the "publicly_accessible" option is allowed here just as it is in the AWS CLI
- rds_instance:
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

- rds_instance:
     instance_name: MyNewInstanceName
     region: us-west-2
     vpc_security_groups: sg-xxx945xx

- debug:
    msg: "The new db endpoint is {{ rds.instance.endpoint }}"
'''

RETURN = '''
instance:
  description: the information returned in data from boto3 get_db_instance
  returned: success
  type: dict
operation:
  description: The operation carried out on the DBM, e.g. create if a new DBM was created or modified if an existing one was changed.
  returned: success
  type: string
  sample:
    "operation": "create"
'''

# from __future__ import (absolute_import, division, print_function)
import time
import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, get_aws_connection_info, boto3_conn, HAS_BOTO3, camel_dict_to_snake_dict
from ansible.module_utils.ec2 import ansible_dict_to_boto3_tag_list, boto3_tag_list_to_ansible_dict
from ansible.module_utils.rds import RDSDBInstance, get_db_instance
# import sys

try:
    import botocore
except ImportError:
    pass  # caught by imported HAS_BOTO3

DEFAULT_PORTS = {
    'aurora': 3306,
    'mariadb': 3306,
    'mysql': 3306,
    'oracle': 1521,
    'sqlserver': 1433,
    'postgres': 5432,
}

DB_ENGINES = [
    'MySQL',
    'aurora'
    'mariadb',
    'oracle-ee',
    'oracle-se',
    'oracle-se1',
    'oracle-se2',
    'postgres',
    'sqlserver-ee',
    'sqlserver-ex',
    'sqlserver-se',
    'sqlserver-web',
]


LICENSE_MODELS = [
    'bring-your-own-license',
    'general-public-license',
    'license-included',
    'postgresql-license'
]

PARAMETER_MAP = {
    'apply_immediately': 'ApplyImmediately',
    'backup_retention': 'BackupRetentionPeriod',
    'backup_window': 'PreferredBackupWindow',
    'character_set_name': 'CharacterSetName',
    'cluster': 'DBClusterIdentifer',
    'db_engine': 'Engine',
    'db_name': 'DBName',
    'engine_version': 'EngineVersion',
    'force_failover': 'ForceFailover',
    'instance_name': 'DBInstanceIdentifier',
    'instance_type': 'DBInstanceClass',
    'iops': 'Iops',
    'license_model': 'LicenseModel',
    'maint_window': 'PreferredMaintenanceWindow',
    'multi_zone': 'MultiAZ',
    'new_instance_name': 'NewDBInstanceIdentifier',
    'option_group': 'OptionGroupName',
    'parameter_group': 'DBParameterGroupName',
    'password': 'MasterUserPassword',
    'port': 'Port',
    'publicly_accessible': 'PubliclyAccessible',
    'security_groups': 'DBSecurityGroups',
    'size': 'AllocatedStorage',
    'skip_final_snapshot': 'SkipFinalSnapshot"',
    'source_instance': 'SourceDBInstanceIdentifier',
    'snapshot': 'DBSnapshotIdentifier',
    'storage_type': 'StorageType',
    'subnet': 'DBSubnetGroupName',
    'tags': 'Tags',
    'upgrade': 'AutoMinorVersionUpgrade',
    'username': 'MasterUsername',
    'vpc_security_groups': 'VpcSecurityGroupIds',
    'zone': 'AvailabilityZone',
}


def eprint(*args, **kwargs):
    pass
#    print(args, file=sys.stderr, **kwargs)


def await_resource(conn, resource, status, module, await_pending=None):
    wait_timeout = module.params.get('wait_timeout') + time.time()
    # Refresh the resource immediately in case we just changed it's state;
    # should we sleep first?
    resource = get_db_instance(conn, resource.name)
    eprint(str(resource))
    eprint("wait is " + str(wait_timeout) + " " + str(time.time()) + " await_pending is "
           + str(await_pending) + " status is " + str(resource.status))
    while ((await_pending and resource.data["pending_modified_values"])
           or resource.status != status) and wait_timeout > time.time():
        time.sleep(5)
        # Temporary until all the rds2 commands have their responses parsed
        if resource.name is None:
            module.fail_json(
                msg="There was a problem waiting for RDS instance %s" % resource.instance)
        resource = get_db_instance(conn, resource.name)
        eprint(str(resource))
        if resource is None:
            break
    if wait_timeout <= time.time() and resource.status != status:
        module.fail_json(msg="Timeout waiting for RDS resource %s status is still %s should be %s" % (
            resource.name, resource.status, status))
    return resource


def create_db_instance(module, conn):
    if module.params.get('db_engine') in ['aurora']:
        required_vars = ['instance_name', 'instance_type', 'db_engine']
        valid_vars = ['apply_immediately', 'character_set_name', 'cluster', 'db_name',
                      'engine_version', 'instance_type', 'license_model', 'maint_window',
                      'option_group', 'parameter_group', 'port', 'publicly_accessible',
                      'subnet', 'upgrade', 'tags', 'zone']
    else:
        required_vars = ['instance_name', 'db_engine', 'size', 'instance_type',
                         'username', 'password']
        valid_vars = ['apply_immediately', 'backup_retention', 'backup_window',
                      'character_set_name', 'cluster', 'db_name', 'engine_version',
                      'instance_type', 'license_model', 'maint_window', 'multi_zone',
                      'option_group', 'parameter_group', 'port', 'publicly_accessible',
                      'storage_type', 'subnet', 'upgrade', 'tags', 'security_groups',
                      'vpc_security_groups', 'zone']

    if module.params.get('subnet'):
        valid_vars.append('vpc_security_groups')
    else:
        valid_vars.append('security_groups')
    params = validate_parameters(required_vars, valid_vars, module)

    # we accept apply_immediately for compatibility with modify but ignore it.  -
    # FIXME should that not apply to _every_ variable which is extra in modify?
    try:
        del(params['ApplyImmediately'])
    except KeyError:
        pass

    instance_name = module.params.get('instance_name')

    instance = get_db_instance(conn, instance_name)
    if instance:
        changed = False
    else:
        try:
            response = conn.create_db_instance(**params)
            instance = RDSDBInstance(response['DBInstance'])
            changed = True
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Failed to create instance: %s " % str(e),
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    if module.params.get('wait'):
        resource = await_resource(conn, instance, 'available', module)
    else:
        resource = get_db_instance(conn, instance_name)

    module.exit_json(changed=changed, instance=resource.data,
                     operation="create")


def replicate_db_instance(module, conn):
    required_vars = ['instance_name', 'source_instance']
    valid_vars = ['instance_type', 'iops', 'option_group', 'port',
                  'publicly_accessible', 'storage_type',
                  'tags', 'upgrade', 'zone']
    params = validate_parameters(required_vars, valid_vars, module)
    instance_name = module.params.get('instance_name')

    instance = get_db_instance(conn, instance_name)
    if instance:
        changed = False
    else:
        try:
            response = conn.create_db_instance_read_replica(**params)
            instance = RDSDBInstance(response['DBInstance'])
            changed = True
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Failed to create replica instance: %s " % str(e),
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    if module.params.get('wait'):
        resource = await_resource(conn, instance, 'available', module)
    else:
        resource = get_db_instance(conn, instance_name)

    module.exit_json(changed=changed, instance=resource.data,
                     operation="replicate")


def delete_db_instance(module, conn):
    required_vars = ['instance_name']

    # we have to accept but ignore variables which have defaults
    valid_vars = ['snapshot', 'skip_final_snapshot', 'storage_type']

    try:
        del(module.params['storage_type'])
    except KeyError:
        pass

    params = validate_parameters(required_vars, valid_vars, module)
    instance_name = module.params.get('instance_name')
    snapshot = module.params.get('snapshot')

    result = get_db_instance(conn, instance_name)
    if not result:
        module.exit_json(changed=False)
    if result.status == 'deleting':
        module.exit_json(changed=False)
    try:
        if snapshot:
            params["SkipFinalSnapshot"] = False
            params["FinalDBSnapshotIdentifier"] = snapshot
            del(params['DBSnapshotIdentifier'])
        else:
            params["SkipFinalSnapshot"] = True
        response = conn.delete_db_instance(**params)
        instance = RDSDBInstance(response['DBInstance'])
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed to delete instance: %s " % str(e),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    # If we're not waiting for a delete to complete then we're all done
    # so just return
    if not module.params.get('wait'):
        module.exit_json(changed=True, operation="delete")
    try:
        instance = await_resource(conn, instance, 'deleted', module)
        module.exit_json(changed=True)
    except botocore.exceptions.ClientError as e:
        if e.code == 'DBInstanceNotFound':
            module.exit_json(changed=True, operation="delete")
        else:
            module.fail_json(msg="Failure waiting for deletion to complete: %s " % str(e),
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    assert(False), "error in module logic - this should not be reached"


def update_rds_tags(module, conn, resource, current_tags, desired_tags):
    changed = False
    # it's much easier to do set manipulation in ansible form
    current_tags = boto3_tag_list_to_ansible_dict(current_tags)
    desired_tags = boto3_tag_list_to_ansible_dict(desired_tags)
    current_keys = set(current_tags.keys())
    desired_keys = set(desired_tags.keys())
    to_add = desired_keys - current_keys
    to_delete = current_keys - desired_keys

    for k in desired_keys & current_keys:
        if current_tags[k] != desired_tags[k]:
            to_delete.add(k)
            to_add.add(k)

    if to_delete:
        try:
            conn.remove_tags_from_resource(
                ResourceName=resource, TagKeys=list(to_delete))
            changed = True
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Failure removing instance tags: %s" % str(e),
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    if to_add:
        try:
            conn.add_tags_to_resource(ResourceName=resource,
                                      Tags=[{'Key': k, 'Value': desired_tags[k]}
                                            for k in to_add])
            changed = True
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Failure adding instance tags: %s" % str(e),
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    return changed


def modify_db_instance(module, conn):
    force_password_update = module.params.pop('force_password_update')
    required_vars = ['instance_name']
    valid_vars = ['apply_immediately', 'backup_retention', 'backup_window', 'db_name',
                  'db_engine', 'engine_version', 'instance_type', 'iops', 'license_model',
                  'maint_window', 'multi_zone', 'new_instance_name', 'option_group',
                  'parameter_group', 'password', 'port', 'publicly_accessible', 'size',
                  'storage_type', 'subnet', 'tags', 'upgrade', 'username',
                  'security_groups', 'vpc_security_groups']

    before_instance_name = module.params.get('instance_name')
    before_instance = get_db_instance(conn, before_instance_name)
    for immutable_key in ['username', 'db_engine', 'db_name']:
        if immutable_key in module.params:
            if ((immutable_key in before_instance.data
                 and module.params[immutable_key] != before_instance.data[immutable_key])):
                module.fail_json(msg="Cannot modify parameter %s for instance %s" %
                                 (immutable_key, before_instance_name))
            del(module.params[immutable_key])

    params = validate_parameters(required_vars, valid_vars, module)
    after_instance_name = module.params.get('new_instance_name')

    will_change = before_instance.diff(module.params)
    if not will_change:
        module.exit_json(
            changed=False, instance=before_instance.data, operation="modify")

    # modify_db_instance takes DBPortNumber in contrast to
    # create_db_instance which takes Port
    try:
        params['DBPortNumber'] = params.pop('Port')
    except KeyError:
        pass
    # modify_db_instance does not accept tags
    try:
        tags = params.pop('Tags')
    except KeyError:
        tags = {}

    # modify_db_instance does not cope with DBSubnetGroup not moving VPC!
    if before_instance.instance['DBSubnetGroup']['DBSubnetGroupName'] == params.get(
            'DBSubnetGroupName'):
        del(params['DBSubnetGroupName'])
    if not force_password_update:
        try:
            del(params['MasterUserPassword'])
        except KeyError:
            pass

    try:
        response = conn.modify_db_instance(**params)
        return_instance = RDSDBInstance(response['DBInstance'])
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed to modify instance: %s " % str(e),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    if params.get('apply_immediately'):
        if after_instance_name:
            # Wait until the new instance name is valid
            after_instance = None
            while not after_instance:
                # FIXME: Timeout!!!
                after_instance = get_db_instance(conn, after_instance_name)
                time.sleep(5)

            # Found instance but it briefly flicks to available
            # before rebooting so let's wait until we see it rebooting
            # before we check whether to 'wait'
            after_instance = await_resource(
                conn, after_instance, 'rebooting', module)
    else:
        after_instance = get_db_instance(conn, before_instance_name)

    # Do we have a race condition here where, if we are unlucky, the name of the instance
    # set to change without apply_immediately _could_ change before we look it up again?
    # If so, when instance lookup fails with the old name we should try the
    # new.

    if module.params.get('wait'):
        if module.params.get('apply_immediately'):
            await_pending = True
        else:
            await_pending = False

        eprint("about to wait")
        return_instance = await_resource(conn, after_instance, 'available', module,
                                         await_pending=await_pending)
    else:
        eprint("skipping wait")
        return_instance = after_instance

    # guess that this changed the DB, need a way to check
    diff = before_instance.diff(return_instance.data)
    changed = not not diff

    # boto3 modify_db_instance can't modify tags directly
    current_tags = conn.list_tags_for_resource(
        ResourceName=response['DBInstance']['DBInstanceArn'])['TagList']
    if update_rds_tags(module, conn, response['DBInstance']['DBInstanceArn'],
                       current_tags, tags):
        changed = True
    module.exit_json(changed=changed, instance=return_instance.data, operation="modify",
                     diff=diff)


def promote_db_instance(module, conn):
    required_vars = ['instance_name']
    valid_vars = ['backup_retention', 'backup_window']
    params = validate_parameters(required_vars, valid_vars, module)
    instance_name = module.params.get('instance_name')

    result = get_db_instance(conn, instance_name)
    if not result:
        module.fail_json(msg="DB Instance %s does not exist" % instance_name)

    if result.data.get('replication_source'):
        try:
            response = conn.promote_read_replica(**params)
            instance = RDSDBInstance(response['DBInstance'])
            changed = True
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Failed to promote replica instance: %s " % str(e),
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    else:
        changed = False

    if module.params.get('wait'):
        instance = await_resource(conn, instance, 'available', module)
    else:
        instance = get_db_instance(conn, instance_name)

    module.exit_json(changed=changed, instance=instance.data,
                     operation="promote")


def reboot_db_instance(module, conn):
    required_vars = ['instance_name']
    valid_vars = ['force_failover']

    params = validate_parameters(required_vars, valid_vars, module)
    instance_name = module.params.get('instance_name')
    instance = get_db_instance(conn, instance_name)
    try:
        response = conn.reboot_db_instance(**params)
        instance = RDSDBInstance(response['DBInstance'])
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed to reboot instance: %s " % str(e),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    if module.params.get('wait'):
        instance = await_resource(conn, instance, 'available', module)
    else:
        instance = get_db_instance(conn, instance_name)

    module.exit_json(changed=True, instance=instance.data, operation="reboot")


def restore_db_instance(module, conn):
    required_vars = ['instance_name', 'snapshot']
    valid_vars = ['db_name', 'iops', 'license_model', 'multi_zone',
                  'option_group', 'port', 'publicly_accessible', 'storage_type',
                  'subnet', 'tags', 'upgrade', 'zone', 'instance_type']
    params = validate_parameters(required_vars, valid_vars, module)
    instance_name = module.params.get('instance_name')

    changed = False
    instance = get_db_instance(conn, instance_name)
    if not instance:
        try:
            response = conn.restore_db_instance_from_db_snapshot(**params)
            instance = RDSDBInstance(response['DBInstance'])
            changed = True
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Failed to restore instance: %s " % str(e),
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    if module.params.get('wait'):
        instance = await_resource(conn, instance, 'available', module)
    else:
        instance = get_db_instance(conn, instance_name)

    module.exit_json(changed=changed, instance=instance.data,
                     operation="restore")


def ensure_db_state(module, conn):
    instance_name = module.params.get('instance_name')
    instance = get_db_instance(conn, instance_name)
    if not instance:
        create_db_instance(module, conn)
    if instance.data.get('replication_source') and not module.params.get('source_instance'):
        promote_db_instance(module, conn)
    modify_db_instance(module, conn)
    # not reached!
    module.exit_json(changed=False, instance=instance.data)


def validate_parameters(required_vars, valid_vars, module):
    for v in required_vars:
        if not module.params.get(v):
            module.fail_json(msg="Parameter %s required" % v)

    params = {}
    for (k, v) in PARAMETER_MAP.items():
        if module.params.get(k):
            if k in valid_vars or k in required_vars:
                params[v] = module.params[k]
            else:
                raise Exception("Parameter %s is not valid" % k)

    # needed for checking that all variables are actually in the map
    for item in set(required_vars) | set(valid_vars):
        try:
            PARAMETER_MAP[item]
        except KeyError as e:
            module.fail_json(msg="unexpected module parameter" +
                             str(e), exception=traceback.format_exc())

    if module.params.get('security_groups'):
        params['DBSecurityGroups'] = module.params.get(
            'security_groups').split(',')

    # Convert tags dict to list of tuples that boto expects
    if 'Tags' in params:
        params['Tags'] = ansible_dict_to_boto3_tag_list(module.params['tags'])
    return params


argument_spec = ec2_argument_spec()
argument_spec.update(
    dict(
        state=dict(choices=['absent', 'present', 'rebooted', 'restarted'], default='present'),
        instance_name=dict(required=True),
        source_instance=dict(),
        db_engine=dict(choices=DB_ENGINES),
        size=dict(type='int'),
        instance_type=dict(aliases=['type']),
        username=dict(),
        password=dict(no_log=True),
        db_name=dict(),
        engine_version=dict(),
        parameter_group=dict(),
        license_model=dict(choices=LICENSE_MODELS),
        multi_zone=dict(type='bool', default=False),
        iops=dict(type='int'),
        storage_type=dict(
            choices=['standard', 'io1', 'gp2'], default='standard'),
        security_groups=dict(),
        vpc_security_groups=dict(type='list'),
        port=dict(type='int'),
        upgrade=dict(type='bool', default=False),
        option_group=dict(),
        maint_window=dict(),
        backup_window=dict(),
        backup_retention=dict(type='int'),
        zone=dict(aliases=['aws_zone', 'ec2_zone']),
        subnet=dict(),
        wait=dict(type='bool', default=False),
        wait_timeout=dict(type='int', default=600),
        snapshot=dict(),
        skip_final_snapshot=dict(type='bool'),
        apply_immediately=dict(type='bool', default=False),
        old_instance_name=dict(),
        tags=dict(type='dict'),
        publicly_accessible=dict(type='bool'),
        character_set_name=dict(),
        force_failover=dict(type='bool', default=False),
        force_password_update=dict(type='bool', default=False),
    )
)
required_if = [
    ('storage_type', 'io1', ['iops']),
]


def main():

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=required_if
    )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required for rds_instance module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(
        module, boto3=True)
    if not region:
        module.fail_json(
            msg="Region not specified. Unable to determine region from configuration.")

    # connect to the rds endpoint
    conn = boto3_conn(module, 'client', 'rds', region, **aws_connect_params)

    if module.params['state'] == 'absent':
        delete_db_instance(module, conn)
    if module.params['state'] in ['rebooted', 'restarted']:
        reboot_db_instance(module, conn)

    # set port to per db defaults if not specified
    if module.params['port'] is None and module.params['db_engine'] is not None:
        if '-' in module.params['db_engine']:
            engine = module.params['db_engine'].split('-')[0]
        else:
            engine = module.params['db_engine']
        module.params['port'] = DEFAULT_PORTS[engine.lower()]

    if module.params.get('source_instance'):
        replicate_db_instance(module, conn)
    if module.params.get('snapshot'):
        restore_db_instance(module, conn)
    ensure_db_state(module, conn)


if __name__ == '__main__':
    main()
