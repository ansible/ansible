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
from ansible.module_utils.aws.core import AnsibleAWSModule
import ansible.modules.cloud.amazon.rds_snapshot_facts as rds_s_f
from ansible.module_utils._text import to_bytes
import ansible.module_utils.basic as basic
import pytest
from dateutil.tz import tzutc
import datetime

boto3 = pytest.importorskip("boto3")
boto = pytest.importorskip("boto")

basic._ANSIBLE_ARGS = to_bytes(b'{ "ANSIBLE_MODULE_ARGS": {"db_snapshot_identifier":"fred"} }')
ansible_module_template = AnsibleAWSModule(argument_spec=rds_s_f.argument_spec)

describe_snapshot_return = {
    'ResponseMetadata': {
        'RetryAttempts': 0,
        'HTTPStatusCode': 200,
        'RequestId': 'abababab-9876-1234-abcd-9876543210fe',
        'HTTPHeaders': {
            'x-amzn-requestid': 'abababab-9876-1234-abcd-9876543210fe',
            'date': 'Fri, 18 Aug 2017 12:43:58 GMT',
            'content-length': '1506',
            'content-type': 'text/xml'}},
    u'DBSnapshots': [{
        u'Engine': 'postgres',
        u'SnapshotCreateTime': datetime.datetime(2017, 6, 20, 12, 38, 18, 818000, tzinfo=tzutc()),
        u'AvailabilityZone': 'us-east-1b',
        u'DBSnapshotArn': 'arn:aws:rds:us-east-1:1234567890:snapshot:fake-snapshot',
        u'PercentProgress': 100,
        u'MasterUsername': 'fakeuser',
        u'Encrypted': False,
        u'LicenseModel': 'postgresql-license',
        u'StorageType': 'standard',
        u'Status': 'available',
        u'VpcId': 'vpc-54321fed',
        u'DBSnapshotIdentifier': 'fake-snapshot',
        u'InstanceCreateTime': datetime.datetime(2017, 6, 20, 12, 12, 18, 872000, tzinfo=tzutc()),
        u'OptionGroupName': 'default:postgres-9-6',
        u'AllocatedStorage': 5,
        u'EngineVersion': '9.6.2',
        u'SnapshotType': 'manual',
        u'Port': 3307,
        u'DBInstanceIdentifier': 'fakedb'}]}


def test_snapshot_facts_should_return_facts():
    params = {
        "db_snapshot_identifier": "fake-snapshot",
    }

    module_double = MagicMock(ansible_module_template)
    module_double.params = params
    rds_client_double = MagicMock()

    rds_client_double.describe_db_snapshots.return_value = describe_snapshot_return

    facts_return = rds_s_f.snapshot_facts(module_double, rds_client_double)

    rds_client_double.describe_db_snapshots.assert_called_once()
    module_double.fail_json.assert_not_called()
    assert not facts_return["changed"], "facts module returned changed!!"
