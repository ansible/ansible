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


def get_rds_db_instance(conn, instancename):
    try:
        response = conn.describe_db_instances(DBInstanceIdentifier=instancename)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'DBInstanceNotFound':
            return None
        else:
            raise
    return response['DBInstances'][0]


def rds_instance_to_facts(instance):
    assert 'DBInstanceIdentifier' in instance, "instance argument was not a valid instance"
    d = camel_dict_to_snake_dict(instance)
    d.update({
        'id': instance.get('DBInstanceIdentifier'),
        'instance_id': instance.get('DBInstanceIdentifier'),
        'create_time': instance.get('InstanceCreateTime', ''),
    })
    return d


def get_rds_snapshot(conn, snapshotid):
    try:
        response = conn.describe_db_snapshots(DBSnapshotIdentifier=snapshotid)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'DBSnapshotNotFound':
            return None
        else:
            raise
    return response['DBSnapshots'][0]


def rds_snap_to_facts(snapshot):
    assert 'DBSnapshotIdentifier' in snapshot, "snapshot argument was not a valid snapshot"
    d = camel_dict_to_snake_dict(snapshot)
    d.update({
        'id': snapshot.get('DBSnapshotIdentifier'),
        'instance_id': snapshot.get('DBInstanceIdentifier'),
        'create_time': snapshot.get('SnapshotCreateTime', ''),
    })
    return d


def rds_facts_diff(state_a, state_b):
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
    old_port = state_a.get("endpoint").get("port")
    new_port = state_b.get("endpoint").get("port")
    if old_port != new_port:
        before['port'] = old_port
        after['port'] = new_port
    result = dict()
    if before:
        result = dict(before_header=state_a.get('instance_id'), before=before, after=after)
        result['after_header'] = state_b.get('instance_id', state_a.get('instance_id'))
    return result
