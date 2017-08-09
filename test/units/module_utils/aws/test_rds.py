# -*- coding: utf-8 -*-
# (c) 2017, Michael De La Rue
#
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.aws.rds import get_rds_db_instance, rds_instance_to_facts, get_rds_snapshot, rds_snap_to_facts, rds_facts_diff
import unittest
import datetime
import copy
from dateutil.tz import tzutc


class FakeResource():
    """simulates an AWS resource by returning appropriate looking data structures

    For describe_db_instances and describe_db_snapshots, this is a resource capable of
    returning data structures that look like an instance and a snapshot as returned by AWS
    respectively.

    The data structures have actually been captured from AWS and then had all identifiers
    modified to fake values.  The internal structure of the identifiers may not be exactly
    right, however if used opaquely they should be fine.
    """

    def describe_db_instances(self, DBInstanceIdentifier=None):
        assert DBInstanceIdentifier == "fakeDBIDstring", "no RDS instance identifier"
        return {u'DBInstances': [{u'PubliclyAccessible': True, u'MasterUsername': 'fakeusername', u'MonitoringInterval': 0, u'LicenseModel': 'postgresql-license', u'VpcSecurityGroups': [{u'Status': 'active', u'VpcSecurityGroupId': 'sg-123456deadbeef'}], u'InstanceCreateTime': datetime.datetime(2016, 6, 11, 12, 22, 5, 123456, tzinfo=tzutc()), u'CopyTagsToSnapshot': False, u'OptionGroupMemberships': [{u'Status': 'in-sync', u'Opti50onGroupName': 'default:postgres-9-5'}], u'PendingModifiedValues': {}, u'Engine': 'postgres', u'MultiAZ': False, u'LatestRestorableTime': datetime.datetime(2018, 4, 2, 11, 7, 22, tzinfo=tzutc()), u'DBSecurityGroups': [], u'DBParameterGroups': [{u'DBParameterGroupName': 'default.postgres9.5', u'ParameterApplyStatus': 'in-sync'}], u'AutoMinorVersionUpgrade': True, u'PreferredBackupWindow': '11:45-12:15', u'DBSubnetGroup': {u'Subnets': [{u'SubnetStatus': 'Active', u'SubnetIdentifier': 'subnet-0deadbeef', u'SubnetAvailabilityZone': {u'Name': 'eu-west-1b'}}, {u'SubnetStatus': 'Active', u'SubnetIdentifier': 'subnet-0deadbeef', u'SubnetAvailabilityZone': {u'Name': 'eu-west-1c'}}, {u'SubnetStatus': 'Active', u'SubnetIdentifier': 'subnet-0deadbeef', u'SubnetAvailabilityZone': {u'Name': 'eu-west-1a'}}], u'DBSubnetGroupName': 'default', u'VpcId': 'vpc-0deadbeef', u'DBSubnetGroupDescription': 'default', u'SubnetGroupStatus': 'Complete'}, u'ReadReplicaDBInstanceIdentifiers': [], u'AllocatedStorage': 15, u'DBInstanceArn': 'arn:aws:rds:eu-west-1:123456789:db:fakeDBIDstring', u'BackupRetentionPeriod': 1, u'PreferredMaintenanceWindow': 'mon:05:00-mon:06:00', u'Endpoint': {u'HostedZoneId': 'ABCDEFG', u'Port': 5432, u'Address': 'fakeDBIDstring.eu-west-1.rds.amazonaws.com'}, u'DBInstanceStatus': 'available', u'EngineVersion': '9.5.2', u'AvailabilityZone': 'eu-west-1b', u'DomainMemberships': [], u'StorageType': 'gp2', u'DbiResourceId': 'db-ABCDEFGHIJK', u'CACertificateIdentifier': 'rds-ca-2015', u'StorageEncrypted': False, u'DBInstanceClass': 'db.t2.micro', u'DbInstancePort': 0, u'DBInstanceIdentifier': 'fakeDBIDstring'}], 'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 200, 'RequestId': '0deadbeef-0123-0123-0123-0123456789', 'HTTPHeaders': {'x-amzn-requestid': '0deadbeef-0123-0123-0123-0123456789', 'vary': 'Accept-Encoding', 'content-length': '4181', 'content-type': 'text/xml', 'date': 'Wed, 09 Aug 2018 11:01:02 GMT'}}}

    def describe_db_snapshots(self, DBSnapshotIdentifier=None):
        assert DBSnapshotIdentifier == "rds:fakeSnapshotIDstring", "no RDS snapshot identifier"
        return {'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 200, 'RequestId': '0deadbee-f000-0123-0123-012345678900', 'HTTPHeaders': {'x-amzn-requestid': '0deadbee-f000-0123-0123-012345678900', 'date': 'Wed, 09 Aug 2018 11:01:03 GMT', 'content-length': '1475', 'content-type': 'text/xml'}}, u'DBSnapshots': [{u'Engine': 'postgres', u'SnapshotCreateTime': datetime.datetime(2018, 3, 2, 1, 11, 01, 012345, tzinfo=tzutc()), u'AvailabilityZone': 'eu-west-1a', u'DBSnapshotArn': 'arn:aws:rds:eu-west-1:123456789:snapshot:rds:fakeSnapshotIDstring', u'PercentProgress': 100, u'MasterUsername': 'fakeuser', u'Encrypted': False, u'LicenseModel': 'postgresql-license', u'StorageType': 'gp2', u'Status': 'available', u'VpcId': 'vpc-0deadbeef', u'DBSnapshotIdentifier': 'rds:fakeSnapshotIDstring', u'InstanceCreateTime': datetime.datetime(2016, 6, 11, 12, 22, 5, 123456, tzinfo=tzutc()), u'OptionGroupName': 'default:postgres-9-5', u'AllocatedStorage': 5, u'EngineVersion': '9.5.4', u'SnapshotType': 'automated', u'Port': 5432, u'DBInstanceIdentifier': 'fakeDBIDstring'}]}


class RDSUtilsTestCase(unittest.TestCase):

    def test_get_db_instance_should_return_camel_dict(self):
        conn = FakeResource()
        db_inst = get_rds_db_instance(conn, "fakeDBIDstring")
        assert 'id' not in db_inst
        assert db_inst["DBInstanceIdentifier"] == "fakeDBIDstring"

    def test_get_db_snapshot_should_return_camel_dict(self):
        conn = FakeResource()
        db_snap = get_rds_snapshot(conn, "rds:fakeSnapshotIDstring")
        for i in "id", "wait", "wait_timeout":
            assert i not in db_snap
        assert db_snap["DBSnapshotIdentifier"] == "rds:fakeSnapshotIDstring"

    def test_instance_facts_gives_sensible_values(self):
        conn = FakeResource()
        db_facts = rds_instance_to_facts(get_rds_db_instance(conn, "fakeDBIDstring"))
        assert db_facts['id'] == "fakeDBIDstring"
#  FIXME - we need to agree which of these need to go
#        assert db_facts['size'] == "fakeSnapshotIDString"
#        assert db_facts['region'] == "fakeawsregion"
#        assert db_facts['port'] == "3210"

    def test_snapshot_facts_gives_sensible_values(self):
        conn = FakeResource()
        snap_facts = rds_snap_to_facts(get_rds_snapshot(conn, "rds:fakeSnapshotIDstring"))
        assert 'id' in snap_facts
#  FIXME - we need to agree which of these need to go
#        assert snap_facts['id'] == "fakeSnapshotIDString"
#        assert snap_facts['instance_id'] == "fakeBackedUpIDString"

    def test_diff_should_compare_important_rds_attributes(self):
        conn = FakeResource()
        db_inst = rds_instance_to_facts(get_rds_db_instance(conn, "fakeDBIDstring"))
        assert len(rds_facts_diff(db_inst, db_inst)) == 0, "comparison of identical instances shows difference!"
        assert not (rds_facts_diff(db_inst, db_inst)), "comparsion of identical instances is not false!"
        bigger_inst = copy.deepcopy(db_inst)
        bigger_inst["allocated_storage"] = db_inst["allocated_storage"] + 5
        assert len(rds_facts_diff(db_inst, bigger_inst)) > 0, "comparison of differing instances is empty!"
