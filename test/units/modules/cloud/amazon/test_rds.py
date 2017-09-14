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
from ansible.compat.tests.mock import MagicMock, patch, ANY

# This module should run in all cases where boto, boto3 or both are
# present.  Individual test cases should then be ready to skip if their
# pre-requisites are not present.
import ansible.modules.cloud.amazon.rds_instance as rds_i
import ansible.module_utils.rds as rds_u

from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.basic as basic
from ansible.module_utils.rds import RDSDBInstance
import pytest
import time
boto3 = pytest.importorskip("boto3")
boto = pytest.importorskip("boto")

def diff_return_a_populated_dict(junk, junktoo):
    """ return a populated dict which will be treated as true => something changed """
    return {"before":"fake", "after":"faketoo"}


def test_modify_should_return_changed_if_param_changes():
    basic._ANSIBLE_ARGS = '{ "ANSIBLE_MODULE_ARGS": { "instance_name":"fred", "port": 242} }'
    params = { "port": 342, "force_password_update": True, "instance_name": "fred" }
    rds_client_double = MagicMock()
    module_double = MagicMock(AnsibleModule( argument_spec = rds_i.argument_spec,
                                             required_if = rds_i.required_if ), params = params)
    with patch.object(RDSDBInstance, 'diff', diff_return_a_populated_dict):
        rds_i.modify_db_instance(module_double, rds_client_double)
    print("rds calls:\n" + str(rds_client_double.mock_calls))
    print("module calls:\n" + str(module_double.mock_calls))
    module_double.exit_json.assert_called_with(changed = True, diff = ANY, instance = ANY,
                                               operation = 'modify')


def test_modify_should_return_false_in_changed_if_param_same():
    basic._ANSIBLE_ARGS = '{ "ANSIBLE_MODULE_ARGS": { "instance_name":"fred", "port": 342} }'
    params = { "port": 342, "force_password_update": True, "instance_name": "fred" }
    rds_client_double = MagicMock()
    module_double = MagicMock(AnsibleModule(argument_spec = rds_i.argument_spec,
                                            required_if = rds_i.required_if), params = params)
    rds_i.modify_db_instance(module_double, rds_client_double)
    print("rds calls:\n" + str(rds_client_double.mock_calls))
    print("module calls:\n" + str(module_double.mock_calls))
    module_double.exit_json.assert_called_with(changed = False, diff = ANY, instance = ANY,
                                               operation = 'modify')


def test_diff_should_be_true_if_something_changed():
    dbinstance_double = MagicMock()
    rdi = rds_u.RDSDBInstance(dbinstance_double)
    params = { "port": 342, "iops": 3924, "instance_name": "fred" }
    diff = rdi.diff(params)
    print("diff:\n" + str(diff))
    print("dbinstance calls:\n" + str(dbinstance_double.mock_calls))
    assert(not not diff)


def test_diff_should_be_true_if_only_the_port_changed():
    dbinstance_double = MagicMock()
    rdi = rds_u.RDSDBInstance(dbinstance_double)
    params = { "endpoint": {"port": 342} }
    diff = rdi.diff(params)
    print("diff:\n" + str(diff))
    print("dbinstance calls:\n" + str(dbinstance_double.mock_calls))
    assert(not not diff)


def test_await_should_wait_till_not_pending():
    sleeper_double = MagicMock()
    get_db_instance_double = MagicMock(side_effect = [
        MagicMock( status = 'rebooting', data = { "pending_modified_values":  {"a":"b", "c":"d"}}),
        MagicMock( status = 'available', data = { "pending_modified_values":  {"a":"b", "c":"d"}}),
        MagicMock( status = 'rebooting', data = { "pending_modified_values":  {"a":"b"}}),
        MagicMock( status = 'rebooting', data = { "pending_modified_values":  {"a":"b", "c":"d"}}),
        MagicMock( status = 'rebooting', data = { "pending_modified_values":  {}}),
        MagicMock( status = 'available', data = { "pending_modified_values":  {"a":"b", "c":"d"}}),
        MagicMock( status = 'rebooting', data = { "pending_modified_values":  {"a":"b", "c":"d"}}),
        MagicMock( status = 'available', data = { "pending_modified_values":  {}}),
        MagicMock( status = 'available', data = { "pending_modified_values":  {}}),
    ])
    with patch.object(time, 'sleep',sleeper_double):
        with patch.object(rds_i, 'get_db_instance', get_db_instance_double):
            rds_i.await_resource(MagicMock(), MagicMock(), "available", MagicMock(),
                                 await_pending=1)

    print("dbinstance calls:\n" + str(get_db_instance_double.mock_calls))
    assert(len(sleeper_double.mock_calls) > 5), "await_pending didn't wait enough"
    assert(len(get_db_instance_double.mock_calls) > 7), "await_pending didn't wait enough"


def test_await_should_wait_for_delete_and_handle_none():
    sleeper_double=MagicMock()
    get_db_instance_double = MagicMock(side_effect=[
        MagicMock( status = 'rebooting', data = { "pending_modified_values":  {"a":"b", "c":"d"}}),
        MagicMock( status = 'available', data = { "pending_modified_values":  {"a":"b", "c":"d"}}),
        MagicMock( status = 'rebooting', data = { "pending_modified_values":  {"a":"b"}}),
        MagicMock( status = 'rebooting', data = { "pending_modified_values":  {}}),
        MagicMock( status = 'rebooting', data = { "pending_modified_values":  {"a":"b", "c":"d"}}),
        MagicMock( status = 'deleting', data = { "pending_modified_values":  {}}),
        None,
        None,
    ])
    with patch.object(time, 'sleep',sleeper_double):
        with patch.object(rds_i, 'get_db_instance', get_db_instance_double):
            rds_i.await_resource(MagicMock(), MagicMock(), "deleted", MagicMock(),
                                 await_pending = p1)

    print("dbinstance calls:\n" + str(get_db_instance_double.mock_calls))
    assert(len(sleeper_double.mock_calls) > 3), "await_pending didn't wait enough"
    assert(len(get_db_instance_double.mock_calls) > 5), "await_pending didn't wait enough"
