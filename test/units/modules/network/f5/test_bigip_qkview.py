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
    from library.modules.bigip_qkview import Parameters
    from library.modules.bigip_qkview import ModuleManager
    from library.modules.bigip_qkview import MadmLocationManager
    from library.modules.bigip_qkview import BulkLocationManager
    from library.modules.bigip_qkview import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock
    from test.units.compat.mock import patch

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_qkview import Parameters
    from ansible.modules.network.f5.bigip_qkview import ModuleManager
    from ansible.modules.network.f5.bigip_qkview import MadmLocationManager
    from ansible.modules.network.f5.bigip_qkview import BulkLocationManager
    from ansible.modules.network.f5.bigip_qkview import ArgumentSpec

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
            filename='foo.qkview',
            asm_request_log=False,
            max_file_size=1024,
            complete_information=True,
            exclude_core=True,
            force=False,
            exclude=['audit', 'secure'],
            dest='/tmp/foo.qkview'
        )
        p = Parameters(params=args)
        assert p.filename == 'foo.qkview'
        assert p.asm_request_log is None
        assert p.max_file_size == '-s 1024'
        assert p.complete_information == '-c'
        assert p.exclude_core == '-C'
        assert p.force is False
        assert len(p.exclude_core) == 2
        assert 'audit' in p.exclude
        assert 'secure' in p.exclude
        assert p.dest == '/tmp/foo.qkview'

    def test_module_asm_parameter(self):
        args = dict(
            asm_request_log=True,
        )
        p = Parameters(params=args)
        assert p.asm_request_log == '-o asm-request-log'


class TestMadmLocationManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_qkview_default_options(self, *args):
        set_module_args(dict(
            dest='/tmp/foo.qkview',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods in the specific type of manager
        tm = MadmLocationManager(module=module, params=module.params)
        tm.exists = Mock(return_value=False)
        tm.execute_on_device = Mock(return_value=True)
        tm._move_qkview_to_download = Mock(return_value=True)
        tm._download_file = Mock(return_value=True)
        tm._delete_qkview = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.is_version_less_than_14 = Mock(return_value=True)
        mm.get_manager = Mock(return_value=tm)

        with patch('os.path.exists') as mo:
            mo.return_value = True
            results = mm.exec_module()

        assert results['changed'] is False


class TestBulkLocationManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_qkview_default_options(self, *args):
        set_module_args(dict(
            dest='/tmp/foo.qkview',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods in the specific type of manager
        tm = BulkLocationManager(module=module, params=module.params)
        tm.exists = Mock(return_value=False)
        tm.execute_on_device = Mock(return_value=True)
        tm._move_qkview_to_download = Mock(return_value=True)
        tm._download_file = Mock(return_value=True)
        tm._delete_qkview = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.is_version_less_than_14 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=tm)

        with patch('os.path.exists') as mo:
            mo.return_value = True
            results = mm.exec_module()

        assert results['changed'] is False
