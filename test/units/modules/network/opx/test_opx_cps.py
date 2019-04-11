#
# (c) 2018 Red Hat Inc.
#
# (c) 2018 Dell Inc. or its subsidiaries. All Rights Reserved.
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
__metaclass__ = type

from units.compat.mock import patch, Mock, MagicMock
import sys
sys.modules['cps'] = Mock(QUALIFIERS=[
    "target",
    "observed",
    "proposed",
    "realtime",
    "registration",
    "running",
    "startup"
], OPERATIONS=[
    "delete",
    "create",
    "set",
    "action",
    "get"
])
sys.modules['cps_object'] = Mock()
sys.modules['cps_utils'] = Mock()

from ansible.modules.network.opx import opx_cps

from units.modules.utils import set_module_args
from .opx_module import TestOpxModule, load_fixture


class TestOpxCpsModule(TestOpxModule):

    module = opx_cps

    def setUp(self):
        super(TestOpxCpsModule, self).setUp()

        self.mock_cps_get = patch('ansible.modules.network.opx.opx_cps.cps_get')
        self.cps_get = self.mock_cps_get.start()

        self.mock_cps_transaction = patch('ansible.modules.network.opx.opx_cps.cps_transaction')
        self.cps_transaction = self.mock_cps_transaction.start()

        self.mock_parse_cps_parameters = patch('ansible.modules.network.opx.opx_cps.parse_cps_parameters')
        self.parse_cps_parameters = self.mock_parse_cps_parameters.start()

        self.mock_get_config = patch('ansible.modules.network.opx.opx_cps.cps_get.parse_cps_parameters')
        self.get_config = self.mock_get_config.start()

    def tearDown(self):
        super(TestOpxCpsModule, self).tearDown()
        self.mock_cps_get.stop()
        self.mock_cps_transaction.stop()
        self.mock_parse_cps_parameters.stop()
        self.mock_get_config.stop()

    def test_opx_operation_create(self):
        resp = load_fixture('opx_operation_create.cfg')
        attr_data = {"base-if-vlan/if/interfaces/interface/id": 105,
                     "if/interfaces/interface/type": "ianaift:l2vlan"}
        module_name = "dell-base-if-cmn/if/interfaces/interface"
        set_module_args(dict(module_name=module_name, operation="create", attr_data=attr_data))
        self.get_config.return_value = dict()
        self.cps_transaction.return_value = dict(changed=True, response=resp)
        self.execute_module(changed=True, response=resp)
        self.assertEqual(self.parse_cps_parameters.call_count, 2)
        self.assertEqual(self.cps_transaction.call_count, 1)

    def test_opx_operation_set(self):
        resp = load_fixture('opx_operation_set.cfg')
        config_data = load_fixture('opx_get_config.cfg')
        attr_data = {"dell-if/if/interfaces/interface/untagged-ports": "e101-001-0",
                     "if/interfaces/interface/name": "br105"}
        module_name = "dell-base-if-cmn/if/interfaces/interface"
        set_module_args(dict(module_name=module_name, operation="set", attr_data=attr_data))
        self.get_config.return_value = config_data
        self.cps_transaction.return_value = dict(changed=True, response=resp)
        self.execute_module(changed=True, response=resp)
        self.assertEqual(self.parse_cps_parameters.call_count, 2)
        self.assertEqual(self.cps_transaction.call_count, 1)

    def test_opx_operation_delete(self):
        resp = load_fixture('opx_operation_delete.cfg')
        config_data = load_fixture('opx_get_config.cfg')
        attr_data = {"if/interfaces/interface/name": "br105"}
        module_name = "dell-base-if-cmn/if/interfaces/interface"
        set_module_args(dict(module_name=module_name, operation="delete", attr_data=attr_data))
        self.get_config.return_value = config_data
        self.cps_transaction.return_value = dict(changed=True, response=resp)
        self.execute_module(changed=True, response=resp)
        self.assertEqual(self.parse_cps_parameters.call_count, 2)
        self.assertEqual(self.cps_transaction.call_count, 1)

    def test_opx_operation_delete_fail(self):
        resp = load_fixture('opx_operation_delete.cfg')
        attr_data = {"if/interfaces/interface/name": "br105"}
        module_name = "dell-base-if-cmn/if/interfaces/interface"
        set_module_args(dict(module_name=module_name, operation="delete", attr_data=attr_data))
        self.get_config.return_value = dict()
        self.execute_module(changed=False)
        self.assertEqual(self.parse_cps_parameters.call_count, 2)
        self.assertEqual(self.cps_transaction.call_count, 1)

    def test_opx_operation_get(self):
        resp = load_fixture('opx_operation_get.cfg')
        attr_data = {"if/interfaces/interface/type": "ianaift:l2vlan"}
        module_name = "dell-base-if-cmn/if/interfaces/interface"
        set_module_args(dict(module_name=module_name, operation="get", attr_data=attr_data))
        self.cps_get.return_value = dict(changed=True, response=resp)
        self.cps_transaction.return_value = None
        self.execute_module(changed=True, response=resp)
        self.assertEqual(self.parse_cps_parameters.call_count, 1)
        self.assertEqual(self.cps_get.call_count, 1)
        self.cps_transaction.assert_not_called()

    def test_opx_operation_set_fail(self):
        attr_data = {"dell-if/if/interfaces/interface/untagged-ports": "e101-001-0",
                     "if/interfaces/interface/name": "br105"}
        exp_msg = "RuntimeError: Transaction error while set"
        module_name = "dell-base-if-cmn/if/interfaces/interface"
        set_module_args(dict(module_name=module_name, operation="set", attr_data=attr_data))
        self.get_config.return_value = dict()
        self.cps_transaction.side_effect = RuntimeError("Transaction error while set")
        self.execute_module(failed=True, msg=exp_msg)
        self.assertEqual(self.parse_cps_parameters.call_count, 2)
        self.assertEqual(self.cps_transaction.call_count, 1)

    def test_opx_operation_create_fail(self):
        attr_data = {"if/interfaces/interface/type": "ianaift:l2vlan"}
        config_data = load_fixture('opx_get_config.cfg')
        exp_msg = "RuntimeError: Transaction error while create"
        module_name = "dell-base-if-cmn/if/interfaces/interface"
        set_module_args(dict(module_name=module_name, operation="create", attr_data=attr_data))
        self.get_config.return_value = config_data
        self.cps_transaction.side_effect = RuntimeError("Transaction error while create")
        self.execute_module(failed=True, msg=exp_msg)
        self.assertEqual(self.parse_cps_parameters.call_count, 2)
        self.assertEqual(self.cps_transaction.call_count, 1)

    def test_opx_operation_get_db(self):
        resp = load_fixture('opx_operation_get_db.cfg')
        attr_data = {"if/interfaces/interface/name": "e101-001-0"}
        module_name = "dell-base-if-cmn/if/interfaces/interface"
        set_module_args(dict(module_name=module_name, operation="get", attr_data=attr_data, db=True))
        self.cps_get.return_value = dict(changed=True, response=resp)
        self.cps_transaction.return_value = None
        self.execute_module(changed=True, response=resp, db=True)
        self.assertEqual(self.parse_cps_parameters.call_count, 1)
        self.assertEqual(self.cps_get.call_count, 1)
        self.cps_transaction.assert_not_called()

    def test_opx_operation_set_commit_event(self):
        resp = load_fixture('opx_operation_set.cfg')
        config_data = load_fixture('opx_get_config.cfg')
        attr_data = {"dell-if/if/interfaces/interface/untagged-ports": "e101-001-0",
                     "if/interfaces/interface/name": "br105"}
        module_name = "dell-base-if-cmn/if/interfaces/interface"
        set_module_args(dict(module_name=module_name, operation="set", attr_data=attr_data, commit_event=True))
        self.get_config.return_value = config_data
        self.cps_transaction.return_value = dict(changed=True, response=resp)
        self.execute_module(changed=True, response=resp, commit_event=True)
        self.assertEqual(self.parse_cps_parameters.call_count, 2)
        self.assertEqual(self.cps_transaction.call_count, 1)
