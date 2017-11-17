# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
import sys

from nose.plugins.skip import SkipTest
if sys.version_info < (2, 7):
    raise SkipTest("F5 Ansible modules require Python >= 2.7")

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, Mock
from ansible.module_utils.f5_utils import AnsibleF5Client
from units.modules.utils import set_module_args

try:
    from library.bigip_configsync_actions import Parameters
    from library.bigip_configsync_actions import ModuleManager
    from library.bigip_configsync_actions import ArgumentSpec
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_configsync_actions import Parameters
        from ansible.modules.network.f5.bigip_configsync_actions import ModuleManager
        from ansible.modules.network.f5.bigip_configsync_actions import ArgumentSpec
        from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
    except ImportError:
        raise SkipTest("F5 Ansible modules require the f5-sdk Python library")

fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
fixture_data = {}


def load_fixture(name):
    path = os.path.join(fixture_path, name)

    if path in fixture_data:
        return fixture_data[path]

    with open(path) as f:
        data = f.read()

    try:
        data = json.loads(data)
    except Exception:
        pass

    fixture_data[path] = data
    return data


class TestParameters(unittest.TestCase):
    def test_module_parameters(self):
        args = dict(
            sync_device_to_group=True,
            sync_group_to_device=True,
            overwrite_config=True,
            device_group="foo"
        )
        p = Parameters(args)
        assert p.sync_device_to_group is True
        assert p.sync_group_to_device is True
        assert p.overwrite_config is True
        assert p.device_group == 'foo'

    def test_module_parameters_yes_no(self):
        args = dict(
            sync_device_to_group='yes',
            sync_group_to_device='no',
            overwrite_config='yes',
            device_group="foo"
        )
        p = Parameters(args)
        assert p.sync_device_to_group is True
        assert p.sync_group_to_device is False
        assert p.overwrite_config is True
        assert p.device_group == 'foo'


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_update_agent_status_traps(self, *args):
        set_module_args(dict(
            sync_device_to_group='yes',
            device_group="foo",
            password='passsword',
            server='localhost',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)

        # Override methods to force specific logic in the module to happen
        mm._device_group_exists = Mock(return_value=True)
        mm._sync_to_group_required = Mock(return_value=False)
        mm.execute_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=None)

        mm._get_status_from_resource = Mock()
        mm._get_status_from_resource.side_effect = [
            'Changes Pending', 'Awaiting Initial Sync', 'In Sync'
        ]

        results = mm.exec_module()

        assert results['changed'] is True
