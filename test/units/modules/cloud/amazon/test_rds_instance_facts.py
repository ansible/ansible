#
# (c) 2017 Michael De La Rue
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
from ansible.compat.tests.mock import MagicMock

# This module should run in all cases where boto, boto3 or both are
# present.  Individual test cases should then be ready to skip if their
# pre-requisites are not present.
import ansible.modules.cloud.amazon.rds_instance_facts as rds_i_f

from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.basic as basic
# from ansible.module_utils.aws.rds import
from ansible.module_utils._text import to_bytes
import pytest
from dateutil.tz import tzutc
import datetime
boto3 = pytest.importorskip("boto3")
boto = pytest.importorskip("boto")


def diff_return_a_populated_dict(junk, junktoo):
    """ return a populated dict which will be treated as true => something changed """
    return {"before": "fake", "after": "faketoo"}


# the following is an almost real responses from describe call based
#
# see test_rds.py for more

describe_rds_return = {
    u'DBInstances': [{
        u'PubliclyAccessible': True,
        u'MasterUsername': 'fakeuser',
        u'MonitoringInterval': 0,
        u'LicenseModel': 'postgresql-license',
        u'VpcSecurityGroups': [{u'Status': 'active', u'VpcSecurityGroupId': 'sg-12345678'}],
        u'InstanceCreateTime': datetime.datetime(2016, 5, 11, 17, 22, 5, 103000, tzinfo=tzutc()),
        u'CopyTagsToSnapshot': False,
        u'OptionGroupMemberships': [{u'Status': 'in-sync', u'OptionGroupName': 'default:postgres-9-5'}],
        u'PendingModifiedValues': {},
        u'Engine': 'postgres',
        u'MultiAZ': False,
        u'LatestRestorableTime': datetime.datetime(2018, 2, 11, 17, 3, 22, tzinfo=tzutc()),
        u'DBSecurityGroups': [],
        u'DBParameterGroups': [{u'DBParameterGroupName': 'default.postgres9.5',
                                u'ParameterApplyStatus': 'in-sync'}],
        u'AutoMinorVersionUpgrade': True,
        u'PreferredBackupWindow': '11:45-12:15',
        u'DBSubnetGroup': {
            u'Subnets': [{u'SubnetStatus': 'Active', u'SubnetIdentifier': 'subnet-abcdef12', u'SubnetAvailabilityZone': {u'Name': 'us-west-1b'}},
                         {u'SubnetStatus': 'Active', u'SubnetIdentifier': 'subnet-34567890', u'SubnetAvailabilityZone': {u'Name': 'us-west-1c'}},
                         {u'SubnetStatus': 'Active', u'SubnetIdentifier': 'subnet-09876542', u'SubnetAvailabilityZone': {u'Name': 'us-west-1a'}}],
            u'DBSubnetGroupName': 'junk',
            u'VpcId': 'vpc-54321fed',
            u'DBSubnetGroupDescription': 'junk',
            u'SubnetGroupStatus': 'Complete'},
        u'ReadReplicaDBInstanceIdentifiers': [],
        u'AllocatedStorage': 5,
        u'DBInstanceArn': 'arn:aws:rds:us-east-1:1234567890:db:fakedb',
        u'BackupRetentionPeriod': 1,
        u'PreferredMaintenanceWindow': 'sun:07:00-sun:08:00',
        u'Endpoint': {u'HostedZoneId': 'ZABCDE1234ABCD', u'Port': 5432,
                      u'Address': 'fakedb.abde1234abcd.us-west-1.rds.amazonaws.com'},
        u'DBInstanceStatus': 'available',
        u'EngineVersion': '9.5.2',
        u'AvailabilityZone': 'us-west-1b',
        u'DomainMemberships': [],
        u'StorageType': 'gp2',
        u'DbiResourceId': 'db-SABCDEFGHIJKLMNOPQ12345ABC',
        u'CACertificateIdentifier': 'rds-ca-2015',
        u'StorageEncrypted': False,
        u'DBInstanceClass': 'db.t2.micro',
        u'DbInstancePort': 0,
        u'DBInstanceIdentifier': 'fakedb'}],
    'ResponseMetadata': {
        'RetryAttempts': 0,
        'HTTPStatusCode': 200,
        'RequestId': '1abcdefa-2abc-3abc-4abc-5abcdeffedcb',
        'HTTPHeaders': {'x-amzn-requestid': '1abcdefa-2abc-3abc-4abc-5abcdeffedcb',
                        'vary': 'Accept-Encoding',
                        'content-length': '4181',
                        'content-type': 'text/xml',
                        'date': 'Tue, 15 Aug 2018 11:09:12 GMT'}}}

# def test_module_parses_args_right()

basic._ANSIBLE_ARGS = to_bytes(b'{ "ANSIBLE_MODULE_ARGS": { "id":"fred"} }')
ansible_module_template = AnsibleModule(argument_spec=rds_i_f.argument_spec)
#    basic._ANSIBLE_ARGS = to_bytes('{ "ANSIBLE_MODULE_ARGS": { "old_id": "fakedb", "old_id":"fred", "port": 342} }')
#    basic._ANSIBLE_ARGS = to_bytes('{ "ANSIBLE_MODULE_ARGS": { "id":"fred", "port": 342} }')


def test_instance_facts_should_return_facts():
    params = {
        "db_instance_identifier": "fakedb-too",
    }

    rds_client_double = MagicMock()
    rds_instance_entry_mock = rds_client_double.describe_db_instances.return_value.__getitem__.return_value.__getitem__
    rds_instance_entry_mock.return_value = describe_rds_return['DBInstances'][0]

    module_double = MagicMock(ansible_module_template)
    module_double.params = params
#    params_mock.__getitem__.side_effect = [old_params, params]

    facts_return = rds_i_f.instance_facts(module_double, rds_client_double)

    print("rds calls:\n" + str(rds_client_double.mock_calls))
    print("module calls:\n" + str(module_double.mock_calls))

    rds_client_double.describe_db_instances.assert_called_once()
    assert not facts_return["changed"], "facts module returned changed!!"
