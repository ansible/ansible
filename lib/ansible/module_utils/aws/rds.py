# -*- coding: utf-8 -*-

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Author: Michael De La Rue 2017 largely rewritten but based on work
# by Will Thames taken in turn from the original rds module.

try:
    import botocore
except:
    pass  # it is assumed that calling modules will detect and provide an appropriate nice error.

from ansible.module_utils.ec2 import camel_dict_to_snake_dict

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


def get_db_instance(conn, instancename):
    try:
        response = conn.describe_db_instances(DBInstanceIdentifier=instancename)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'DBInstanceNotFound':
            return None
        else:
            raise
    return response['DBInstances'][0]


def instance_to_facts(instance):
    assert 'DBInstanceIdentifier' in instance, "instance argument was not a valid instance"
    d = camel_dict_to_snake_dict(instance)
    d.update({
        'id': instance.get('DBInstanceIdentifier'),
        'instance_id': instance.get('DBInstanceIdentifier'),
        'create_time': instance.get('InstanceCreateTime', ''),
    })
    return d


def get_snapshot(conn, snapshotid):
    try:
        response = conn.describe_db_snapshots(DBSnapshotIdentifier=snapshotid)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'DBSnapshotNotFound':
            return None
        else:
            raise
    return response['DBSnapshots'][0]


def snapshot_to_facts(snapshot):
    assert 'DBSnapshotIdentifier' in snapshot, "snapshot argument was not a valid snapshot"
    d = camel_dict_to_snake_dict(snapshot)
    d.update({
        'id': snapshot.get('DBSnapshotIdentifier'),
        'instance_id': snapshot.get('DBInstanceIdentifier'),
        'create_time': snapshot.get('SnapshotCreateTime', ''),
    })
    return d


def instance_facts_diff(state_a, state_b):
    """compare two fact dictionaries for rds instances

    This function takes two dictionaries of facts related to an RDS
    and compares them intelligently generating only the differences
    which ansible controls.  If nothing has changed then the
    difference should be an empty dictionary which can be treated as
    False

    The second dict is assumed to represent a target state and so if
    certain params (such as the maintainence window, which has an
    automatic default value set by AWS) are missing they will not be
    considered to show a difference.

    """
    # FIXME compare_keys should be all things that can be modified
    # except port and instance_name which are handled separately
    # valid_vars = ['backup_retention', 'backup_window',
    #               'db_name',  'db_engine', 'engine_version',
    #               'instance_type', 'iops', 'license_model',
    #               'maint_window', 'multi_zone', 'new_instance_name',
    #               'option_group', 'parameter_group', 'password', 'allocated_storage',
    #               'storage_type', 'subnet', 'tags', 'upgrade', 'username',
    #               'vpc_security_groups']
    compare_keys = ['backup_retention', 'instance_type', 'iops',
                    'maintenance_window', 'multi_zone',
                    'replication_source',
                    'allocated_storage', 'storage_type', 'tags', 'zone']
    leave_if_null = ['maintenance_window', 'backup_retention']
    before = dict()
    after = dict()
    for k in compare_keys:
        if state_a.get(k) != state_b.get(k):
            if state_b.get(k) is None and k in leave_if_null:
                pass
            else:
                before[k] = state_a.get(k)
                after[k] = state_b.get(k)

    # FIXME - verify that we actually should accept a lack of port
    try:
        old_port = state_a.get("endpoint").get("port")
    except AttributeError:
        old_port = None
    try:
        new_port = state_b.get("endpoint").get("port")
    except AttributeError:
        new_port = None

    if old_port != new_port:
        before['port'] = old_port
        after['port'] = new_port
    result = dict()
    if before:
        result = dict(before_header=state_a.get('instance_id'), before=before, after=after)
        result['after_header'] = state_b.get('instance_id', state_a.get('instance_id'))
    return result
