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
from ansible.compat.tests.mock import MagicMock, Mock, patch, ANY

# This module should run in all cases where boto, boto3 or both are
# present.  Individual test cases should then be ready to skip if their
# pre-requisites are not present.
import ansible.modules.cloud.amazon.rds_instance as rds_i
import ansible.module_utils.rds as rds_u

from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.basic as ba
from ansible.module_utils.rds import RDSDBInstance
import pytest
import pdb
boto3 = pytest.importorskip("boto3")
boto = pytest.importorskip("boto")

def diff_return_a_populated_dict(junk,junktoo):
    """ return a populated dict which will be treated as true => something changed """
    return {"before":"fake","after":"faketoo"}

def test_modify_should_return_changed_if_param_changes():
    ba._ANSIBLE_ARGS='{"ANSIBLE_MODULE_ARGS":{"instance_name":"fred", "port": 242}}'
    params={"port":342,"force_password_update":True,"instance_name":"fred"}
    rds_client_double = MagicMock()
    module_double = MagicMock(AnsibleModule(argument_spec=rds_i.argument_spec,
                                            required_if=rds_i.required_if), params=params)
    with patch.object(RDSDBInstance, 'diff', diff_return_a_populated_dict):
        rds_i.modify_db_instance(module_double, rds_client_double)
    print("rds calls:\n" + str(rds_client_double.mock_calls))
    print("module calls:\n" + str(module_double.mock_calls))
    module_double.exit_json.assert_called_with(changed=True, diff=ANY, instance=ANY,
                                               operation='modify')


def test_modify_should_return_false_in_changed_if_param_same():
    ba._ANSIBLE_ARGS='{"ANSIBLE_MODULE_ARGS":{"instance_name":"fred", "port": 342}}'
    params={"port":342,"force_password_update":True,"instance_name":"fred"}
    rds_client_double = MagicMock()
#    pdb.set_trace()
    module_double = MagicMock(AnsibleModule(argument_spec=rds_i.argument_spec,
                                            required_if=rds_i.required_if), params=params)
    rds_i.modify_db_instance(module_double, rds_client_double)
    print("rds calls:\n" + str(rds_client_double.mock_calls))
    print("module calls:\n" + str(module_double.mock_calls))
    module_double.exit_json.assert_called_with(changed=False, diff=ANY, instance=ANY,
                                               operation='modify')


def test_diff_should_be_true_if_something_changed():
    dbinstance_double = MagicMock()
    rdi = rds_u.RDSDBInstance(dbinstance_double)
    params={"port":342,"force_password_update":True,"instance_name":"fred"}
    diff=rdi.diff(params)
    print("diff:\n" + str(diff))
    print("dbinstance calls:\n" + str(dbinstance_double.mock_calls))
    assert(not not diff)
