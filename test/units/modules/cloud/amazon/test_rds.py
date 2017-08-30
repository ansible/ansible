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
from ansible.compat.tests.mock import MagicMock, patch

# This module should run in all cases where boto, boto3 or both are
# present.  Individual test cases should then be ready to skip if their
# pre-requisites are not present.
import ansible.modules.cloud.amazon.rds_instance as rds_i

from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.basic as basic
import ansible.module_utils.aws.rds as rds
# from ansible.module_utils.aws.rds import
from ansible.module_utils._text import to_bytes
from botocore.exceptions import ClientError
import pytest
from dateutil.tz import tzutc
import time
import datetime
import copy
import json
boto3 = pytest.importorskip("boto3")
boto = pytest.importorskip("boto")


def diff_return_a_populated_dict(junk, junktoo):
    """ return a populated dict which will be treated as true => something changed """
    return {"before": "fake", "after": "faketoo"}


# the following are two matching almost real responses from describe
# and modify calls based on actual returns in which all of the
# returned data has been subtituted with fake identifiers etc.
#
# they are good for testing code can understand such a response and
# return something useful though we should not rely on the structure
# remaining stable beyond what is documented

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

# this is the return in the case that ApplyPending is _NOT_ given
modify_rds_return = {
    u'DBInstance': {
        u'PubliclyAccessible': True,
        u'MasterUsername': 'fakeuser',
        u'MonitoringInterval': 0,
        u'LicenseModel': 'postgresql-license',
        u'VpcSecurityGroups': [{u'Status': 'active', u'VpcSecurityGroupId': 'sg-12345678'}],
        u'InstanceCreateTime': datetime.datetime(2016, 5, 11, 17, 22, 5, 103000, tzinfo=tzutc()),
        u'CopyTagsToSnapshot': False,
        u'OptionGroupMemberships': [{u'Status': 'in-sync', u'OptionGroupName': 'default:postgres-9-5'}],
        u'PendingModifiedValues': {u'DBInstanceIdentifier': 'fakedb-too'},
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
        u'DBInstanceIdentifier': 'temp-test'},
    'ResponseMetadata': {
        'RetryAttempts': 0,
        'HTTPStatusCode': 200,
        'RequestId': '2abcdef3-1234-2234-3234-5abcdefffedb',
        'HTTPHeaders': {'x-amzn-requestid': '2abcdef3-1234-2234-3234-5abcdefffedb',
                        'vary': 'Accept-Encoding',
                        'content-length': '3802',
                        'content-type': 'text/xml',
                        'date': 'Thuf 17 Aug 2018 10:50:39 GMT'}}}

# def test_module_parses_args_right()

basic._ANSIBLE_ARGS = to_bytes(b'{ "ANSIBLE_MODULE_ARGS": { "db_instance_class":"very-small-indeed", "engine": "postgres", "id":"fred", "port": 242} }')
ansible_module_template = AnsibleModule(argument_spec=rds_i.argument_spec, required_if=rds_i.required_if)
#    basic._ANSIBLE_ARGS = to_bytes('{ "ANSIBLE_MODULE_ARGS": { "old_id": "fakedb", "old_id":"fred", "port": 342} }')
#    basic._ANSIBLE_ARGS = to_bytes('{ "ANSIBLE_MODULE_ARGS": { "id":"fred", "port": 342} }')


def test_modify_should_return_changed_if_param_changes():
    params = {
        "port": 342,
        "force_password_update": True,
        "db_instance_identifier": "fakedb-too",
        "old_db_instance_identifier": "fakedb",
        "allocated_storage": 5,
        "storage_type": "gp",
    }

    rds_client_double = MagicMock()
    rds_instance_entry_mock = rds_client_double.describe_db_instances.return_value.__getitem__.return_value.__getitem__
    rds_instance_entry_mock.return_value = describe_rds_return['DBInstances'][0]
    mod_db_fn = rds_client_double.modify_db_instance
    mod_db_fn.return_value = modify_rds_return

    module_double = MagicMock(ansible_module_template)
    module_double.params = params
#    params_mock.__getitem__.side_effect = [old_params, params]

    mod_return = rds_i.modify_db_instance(module_double, rds_client_double)
    print("rds calls:\n" + str(rds_client_double.mock_calls))
    print("module calls:\n" + str(module_double.mock_calls))

    mod_db_fn.assert_called_with(DBInstanceIdentifier='fakedb', DBPortNumber=342,
                                 NewDBInstanceIdentifier='fakedb-too', StorageType='gp')
    assert mod_return["changed"], "modify failed to return changed"


def test_modify_should_return_false_in_changed_if_param_same():
    params = {
        "port": 5432,
        "force_password_update": True,
        "db_instance_identifier": "fakedb-too",
        "old_db_instance_identifier": "fakedb",
        "allocated_storage": 5,
        "storage_type": "gp2",
    }

    rds_client_double = MagicMock()
    rds_instance_entry_mock = rds_client_double.describe_db_instances.return_value.__getitem__.return_value.__getitem__
    my_instance = copy.deepcopy(describe_rds_return['DBInstances'][0])
    my_instance['DBInstanceIdentifier'] = 'fakedb-too'
    rds_instance_entry_mock.return_value = my_instance

    rds_client_double.modify_db_instance.return_value = modify_rds_return

    module_double = MagicMock(ansible_module_template)
    module_double.params = params
    mod_return = rds_i.modify_db_instance(module_double, rds_client_double)
    print("rds calls:\n" + str(rds_client_double.mock_calls))
    print("module calls:\n" + str(module_double.mock_calls))

    rds_client_double.modify_db_instance.assert_not_called()
    assert not mod_return["changed"], "modify return changed when should be false"


# def test_rds_instance_should_be_careful():

#     #rds_instance should rename databases to the name given
#     context=dict(old_name='fakedb', new_name='fred')
#     given_that_an_RDS_instance_with_the_old_name_exists(context)
#     given_that_no_RDS_instance_with_the_new_name_exists(context)
#     when_the_module_function_is_called_with_both_old_and_new_name(context)
#     then_rds_modify_should_have_been_called_with_old_and_new_names(context)

#     #rds_instance should abort if both old name and new name exist
#     given_that_an_RDS_instance_with_the_old_name_exists(context)
#     given_that_an_RDS_instance_with_the_new_name_exists(context)
#     when_the_module_function_is_called_with_both_old_and_new_name(context)
#     then_the_module_function_should_abort_with_an_error(context)

#     #rds_instance should abort if the old name is an incorrect replica
#     context=dict(old_name='fakedb', new_name='fred')
#     given_that_an_RDS_instance_with_the_old_name_exists(context)
#     given_that_no_RDS_instance_with_the_new_name_exists(context)
#     #and implicitly that the old database has no replica source
#     when_the_module_function_is_called_with_both_old_and_new_name_and_a_replicaton_source(context)
#     then_rds_modify_should_not_have_been_called_with_old_and_new_names(context)
#     then_the_module_function_should_abort_with_an_error(context)

#     #rds_instance should abort if told to rename a non-replica to be a replica
#     context=dict(old_name='fakedb', new_name='fred')
#     given_that_an_RDS_instance_with_the_old_name_exists(context)
#     given_that_no_RDS_instance_with_the_new_name_exists(context)
#     when_the_module_function_is_called_with_both_old_and_new_name_and_a_replicaton_source(context)
#     then_rds_modify_should_not_have_been_called_with_old_and_new_names(context)
#     and_a_warning_should_be_recorded_that_an_instance_is_being_ignored(context)

#     #rds_instance should abort if told to create a replica on top of a non replica
#     context=dict(old_name='fakedb', new_name='fred')
#     given_that_an_RDS_instance_with_the_old_name_exists(context)
#     given_that_no_RDS_instance_with_the_new_name_exists(context)
#     when_the_module_function_is_called_with_both_old_and_new_name_and_a_replicaton_source(context)
#     then_rds_modify_should_not_have_been_called_with_old_and_new_names(context)
#     and_a_warning_should_be_recorded_that_an_instance_is_being_ignored(context)

#     when_I_am_told_to_rename_the_instance_from_the_old_to_new_name(context)
#     then_rds_modify_should_have_been_called_with_old_and_new_names(context)

#     given_that_I_have_an_RDS_instance_with_the_old_name(context)
#     #if we have the same name we leave it


def test_diff_should_be_true_if_something_changed():
    instance_before = {"endpoint": {"port": 342}, "port": 111, "iops": 1234, "id": "fred"}
    instance_after = {"endpoint": {"port": 342}, "port": 342, "iops": 3924, "id": "fred"}
    diff = rds.instance_facts_diff(instance_before, instance_after)
    print("diff:\n" + str(diff))
    assert(not not diff)


def test_diff_should_be_true_if_only_the_port_changed():
    params_a = {"endpoint": {"port": 342}}
    params_b = {"endpoint": {"port": 345}}
    diff = rds.instance_facts_diff(params_a, params_b)
    print("diff:\n" + str(diff))
    assert(not not diff)


def simple_instance_list(status, pending):
    return {u'DBInstances': [{u'DBInstanceArn': 'arn:aws:rds:us-east-1:1234567890:db:fakedb',
                              u'DBInstanceStatus': status,
                              u'PendingModifiedValues': pending,
                              u'DBInstanceIdentifier': 'fakedb'}]}


def test_await_should_wait_till_not_pending():
    sleeper_double = MagicMock()
    rds_client_double = MagicMock()
    rds_client_double.describe_db_instances.side_effect = [
        simple_instance_list('rebooting', {"a": "b", "c": "d"}),
        simple_instance_list('available', {"c": "d", "e": "f"}),
        simple_instance_list('rebooting', {"a": "b"}),
        simple_instance_list('rebooting', {"e": "f", "g": "h"}),
        simple_instance_list('rebooting', {}),
        simple_instance_list('available', {"g": "h", "i": "j"}),
        simple_instance_list('rebooting', {"i": "j", "k": "l"}),
        simple_instance_list('available', {}),
        simple_instance_list('available', {}),
    ]

    mod_mock = MagicMock()
    # we need our wait timeout to always be bigger than current time so that we use the
    # above values to check that the correct state has been waited for.
    mod_mock.params.get.return_value.__add__.return_value.__gt__.return_value = True
    mod_mock.params.get.return_value.__add__.return_value.__lt__.return_value = False
    mod_mock.params.get.return_value.__add__.return_value.__le__.return_value = False
    with patch.object(time, 'sleep', sleeper_double):
        rds_i.await_resource(rds_client_double, "some-instance", "available", mod_mock,
                             await_pending=1)
    print("dbinstance calls:\n" + str(rds_client_double.describe_db_instances.mock_calls))
    assert(len(sleeper_double.mock_calls) > 5), "await_pending didn't wait enough"
    assert(len(rds_client_double.describe_db_instances.mock_calls) > 7), "await_pending didn't wait enough"


error_response = {'Error': {'Code': 'DBInstanceNotFound', 'Message': 'Fake Testing Error'}}
operation_name = 'FakeOperation'
db_instance_gone_error = ClientError(error_response, operation_name)


def test_await_should_wait_for_delete_and_handle_none():
    sleeper_double = MagicMock()
    rds_client_double = MagicMock()
    rds_client_double.describe_db_instances.side_effect = MagicMock(side_effect=[
        simple_instance_list('rebooting', {"a": "b", "c": "d"}),
        simple_instance_list('available', {"a": "b", "c": "d"}),
        simple_instance_list('rebooting', {"a": "b"}),
        simple_instance_list('rebooting', {}),
        simple_instance_list('rebooting', {"a": "b", "c": "d"}),
        simple_instance_list('deleting', {}),
        # return error a few times so await can realise it's gone and any later lookup
        # for the return will be satisfied
        db_instance_gone_error,
        db_instance_gone_error,
        db_instance_gone_error,
    ])

    mod_mock = MagicMock()
    # we need our wait timeout to always be bigger than current time so that we use the
    # above values to check that the correct state has been waited for.
    mod_mock.params.get.return_value.__add__.return_value.__gt__.return_value = True
    mod_mock.params.get.return_value.__add__.return_value.__le__.return_value = True
    with patch.object(time, 'sleep', sleeper_double):
        rds_i.await_resource(rds_client_double, MagicMock(), "deleted", mod_mock,
                             await_pending=1)

    print("dbinstance calls:\n" + str(rds_client_double.describe_db_instances.mock_calls))
    assert(len(sleeper_double.mock_calls) > 3), "await_pending didn't sleep enough"
    assert(len(rds_client_double.describe_db_instances.mock_calls) > 5), "await_pending didn't wait enough"


def test_update_rds_tags_should_add_and_remove_appropriate_tags():
    params = {
        "tags": dict(newtaga="avalue", oldtagb="bvalue"),
        "db_instance_identifier": "fakedb-too",
    }
    rds_client_double = MagicMock()
    mk_tag_fn = rds_client_double.add_tags_to_resource
    rm_tag_fn = rds_client_double.remove_tags_from_resource
    ls_tag_fn = rds_client_double.list_tags_for_resource

    ls_tag_fn.return_value = {'TagList': [{"Key": "oldtagb", "Value": "bvalue"},
                                          {"Key": "oldtagc", "Value": "cvalue"}, ]}

    rds_instance_entry_mock = rds_client_double.describe_db_instances.return_value.__getitem__.return_value.__getitem__n
    my_instance = copy.deepcopy(describe_rds_return['DBInstances'][0])
    rds_instance_entry_mock.return_value = my_instance

    module_double = MagicMock(ansible_module_template)
    module_double.params = params

    tag_update_return = rds_i.update_rds_tags(module_double, rds_client_double, db_instance=my_instance)

    mk_tag_fn.assert_called_with(ResourceName='arn:aws:rds:us-east-1:1234567890:db:fakedb', Tags=[{'Value': 'avalue', 'Key': 'newtaga'}])
    rm_tag_fn.assert_called_with(ResourceName='arn:aws:rds:us-east-1:1234567890:db:fakedb', TagKeys=['oldtagc'])
    assert tag_update_return is True


def test_update_rds_tags_should_delete_if_empty_tags():
    params = {
        "tags": {},
        "db_instance_identifier": "fakedb-too",
    }
    rds_client_double = MagicMock()
    mk_tag_fn = rds_client_double.add_tags_to_resource
    rm_tag_fn = rds_client_double.remove_tags_from_resource
    ls_tag_fn = rds_client_double.list_tags_for_resource

    ls_tag_fn.return_value = {'TagList': [{"Key": "oldtagb", "Value": "bvalue"},
                                          {"Key": "oldtagc", "Value": "cvalue"}, ]}

    rds_instance_entry_mock = rds_client_double.describe_db_instances.return_value.__getitem__.return_value.__getitem__n
    my_instance = copy.deepcopy(describe_rds_return['DBInstances'][0])
    rds_instance_entry_mock.return_value = my_instance

    module_double = MagicMock(ansible_module_template)
    module_double.params = params

    tag_update_return = rds_i.update_rds_tags(module_double, rds_client_double, db_instance=my_instance)

    mk_tag_fn.assert_not_called()
    rm_tag_fn.assert_called_with(ResourceName='arn:aws:rds:us-east-1:1234567890:db:fakedb', TagKeys=['oldtagb', 'oldtagc'])
    assert tag_update_return is True


def test_update_rds_tags_should_not_act_if_no_tags():
    params = {
        "db_instance_identifier": "fakedb-too",
    }
    rds_client_double = MagicMock()
    mk_tag_fn = rds_client_double.add_tags_to_resource
    rm_tag_fn = rds_client_double.remove_tags_from_resource
    ls_tag_fn = rds_client_double.list_tags_for_resource

    ls_tag_fn.return_value = {'TagList': [{"Key": "oldtagb", "Value": "bvalue"},
                                          {"Key": "oldtagc", "Value": "cvalue"}, ]}

    rds_instance_entry_mock = rds_client_double.describe_db_instances.return_value.__getitem__.return_value.__getitem__n
    my_instance = copy.deepcopy(describe_rds_return['DBInstances'][0])
    rds_instance_entry_mock.return_value = my_instance

    module_double = MagicMock(ansible_module_template)
    module_double.params = params

    tag_update_return = rds_i.update_rds_tags(module_double, rds_client_double, db_instance=my_instance)

    mk_tag_fn.assert_not_called()
    rm_tag_fn.assert_not_called()
    assert tag_update_return is False


def set_module_args(args):
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


def test_select_params_should_provide_needed_args_to_create_if_module_has_basics():
    needed_args = ['DBInstanceIdentifier', 'DBInstanceClass', 'Engine']
    set_module_args({
        "db_instance_identifier": "fred",
        "db_instance_class": "t1-pretty-small-really",
        "engine": "postgres",
        "allocated_storage": 5
    })
    module = rds_i.setup_module_object()
    params = rds_i.select_parameters(module, rds_i.db_create_required_vars, rds_i.db_create_valid_vars)
    for i in needed_args:
        assert i in params, "{0} parameter missing".format(i)
        assert len(params(i)) > 0, "{0} parameter lacks value".format(i)
