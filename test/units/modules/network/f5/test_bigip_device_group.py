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
from ansible.compat.tests.mock import Mock
from ansible.compat.tests.mock import patch
from ansible.module_utils.basic import AnsibleModule

try:
    from library.modules.bigip_device_group import Parameters
    from library.modules.bigip_device_group import ModuleManager
    from library.modules.bigip_device_group import ArgumentSpec
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_device_group import Parameters
        from ansible.modules.network.f5.bigip_device_group import ModuleManager
        from ansible.modules.network.f5.bigip_device_group import ArgumentSpec
        from ansible.module_utils.network.f5.common import F5ModuleError
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
        from units.modules.utils import set_module_args
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
            save_on_auto_sync=True,
            full_sync=False,
            description="my description",
            type="sync-failover",
            auto_sync=True
        )

        p = Parameters(params=args)
        assert p.save_on_auto_sync is True
        assert p.full_sync is False
        assert p.description == "my description"
        assert p.type == "sync-failover"
        assert p.auto_sync == 'enabled'

    def test_api_parameters(self):
        args = dict(
            asmSync="disabled",
            autoSync="enabled",
            fullLoadOnSync="false",
            incrementalConfigSyncSizeMax=1024,
            networkFailover="disabled",
            saveOnAutoSync="false",
            type="sync-only"
        )

        p = Parameters(params=args)
        assert p.auto_sync == 'enabled'
        assert p.full_sync is False
        assert p.max_incremental_sync_size == 1024
        assert p.save_on_auto_sync is False
        assert p.type == 'sync-only'


class TestModuleManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_default_device_group(self, *args):
        set_module_args(
            dict(
                name="foo-group",
                state="present",
                server='localhost',
                user='admin',
                password='password'
            )
        )

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.create_on_device = Mock(return_value=True)
        mm.exists = Mock(return_value=False)

        results = mm.exec_module()
        assert results['changed'] is True

    def test_update_device_group(self, *args):
        set_module_args(
            dict(
                full_sync=True,
                name="foo-group",
                state="present",
                server='localhost',
                user='admin',
                password='password'
            )
        )

        current = Parameters(params=load_fixture('load_tm_cm_device_group.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.update_on_device = Mock(return_value=True)
        mm.exists = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()
        assert results['changed'] is True

    def test_delete_device_group(self, *args):
        set_module_args(
            dict(
                name="foo-group",
                state="absent",
                server='localhost',
                user='admin',
                password='password'
            )
        )

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[True, False])
        mm.remove_from_device = Mock(return_value=True)

        results = mm.exec_module()
        assert results['changed'] is True
