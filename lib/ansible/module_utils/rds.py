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

import botocore

from ansible.module_utils.ec2 import camel_dict_to_snake_dict


def get_db_instance(conn, instancename):
    try:
        response = conn.describe_db_instances(DBInstanceIdentifier=instancename)
        instance = RDSDBInstance(response['DBInstances'][0])
        return instance
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'DBInstanceNotFound':
            return None
        else:
            raise


def get_db_snapshot(conn, snapshotid):
    try:
        response = conn.describe_db_snapshots(DBSnapshotIdentifier=snapshotid)
        snapshot = RDSSnapshot(response['DBSnapshots'][0])
        return snapshot
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'DBSnapshotNotFound':
            return None
        else:
            raise


class RDSDBInstance(object):
    def __init__(self, dbinstance):
        self.instance = dbinstance
        if 'DBInstanceIdentifier' not in dbinstance:
            self.name = None
        else:
            self.name = self.instance.get('DBInstanceIdentifier')
        self.status = self.instance.get('DBInstanceStatus')
        self.data = self.get_data()

    def get_data(self):
        return camel_dict_to_snake_dict(self.instance)

    def diff(self, params):
        compare_keys = ['backup_retention', 'instance_type', 'iops',
                        'maintenance_window', 'multi_zone',
                        'replication_source',
                        'size', 'storage_type', 'tags', 'zone']
        leave_if_null = ['maintenance_window', 'backup_retention']
        before = dict()
        after = dict()
        for k in compare_keys:
            if self.data.get(k) != params.get(k):
                if params.get(k) == None and k in leave_if_null:
                    pass
                else:
                    before[k] = self.data.get(k)
                    after[k] = params.get(k)
        port = self.data.get('port')
        if port != params.get('port'):
            before['port'] = port
            after['port'] = params.get('port')
        result = dict()
        if before:
            result = dict(before_header=self.name, before=before, after=after)
            result['after_header'] = params.get('new_instance_name', params.get('instance_name'))
        return result

    def __eq__(self, other):
        return not self.diff(other.instance)

    def __ne__(self, other):
        return not self == other


class RDSSnapshot(object):
    def __init__(self, snapshot):
        self.snapshot = snapshot
        self.name = self.snapshot.get('DBSnapshotIdentifier')
        self.status = self.snapshot.get('Status')
        self.data = self.get_data()

    def get_data(self):
        d = {
            'id': self.name,
            'create_time': self.snapshot.get('SnapshotCreateTime', ''),
            'status': self.status,
            'availability_zone': self.snapshot['AvailabilityZone'],
            'instance_id': self.snapshot['DBInstanceIdentifier'],
            'instance_created': self.snapshot['InstanceCreateTime'],
            'snapshot_type': self.snapshot['SnapshotType'],
        }
        if self.snapshot.get('Iops'):
            d['iops'] = self.snapshot['Iops'],
        return d
