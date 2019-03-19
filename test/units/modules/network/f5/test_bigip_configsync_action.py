# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
import pytest
import sys

if sys.version_info < (2, 7):
    pytestmark = pytest.mark.skip("F5 Ansible modules require Python >= 2.7")

from ansible.module_utils.basic import AnsibleModule

try:
    from library.modules.bigip_configsync_action import Parameters
    from library.modules.bigip_configsync_action import ModuleManager
    from library.modules.bigip_configsync_action import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock
    from test.units.compat.mock import patch

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_configsync_action import Parameters
    from ansible.modules.network.f5.bigip_configsync_action import ModuleManager
    from ansible.modules.network.f5.bigip_configsync_action import ArgumentSpec

    # Ansible 2.8 imports
    from units.compat import unittest
    from units.compat.mock import Mock
    from units.compat.mock import patch

    from units.modules.utils import set_module_args


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
        p = Parameters(params=args)
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
        p = Parameters(params=args)
        assert p.sync_device_to_group == 'yes'
        assert p.sync_group_to_device == 'no'
        assert p.overwrite_config == 'yes'
        assert p.device_group == 'foo'


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()
        self.patcher1 = patch('time.sleep')
        self.patcher1.start()

    def tearDown(self):
        self.patcher1.stop()

    def test_update_agent_status_traps(self, *args):
        set_module_args(dict(
            sync_device_to_group='yes',
            device_group="foo",
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            mutually_exclusive=self.spec.mutually_exclusive,
            required_one_of=self.spec.required_one_of
        )
        mm = ModuleManager(module=module)

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
