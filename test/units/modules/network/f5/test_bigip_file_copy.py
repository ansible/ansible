# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, F5 Networks Inc.
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
    from library.modules.bigip_file_copy import ApiParameters
    from library.modules.bigip_file_copy import IFileManager
    from library.modules.bigip_file_copy import ModuleParameters
    from library.modules.bigip_file_copy import ModuleManager
    from library.modules.bigip_file_copy import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock
    from test.units.compat.mock import patch

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_file_copy import ApiParameters
    from ansible.modules.network.f5.bigip_file_copy import IFileManager
    from ansible.modules.network.f5.bigip_file_copy import ModuleParameters
    from ansible.modules.network.f5.bigip_file_copy import ModuleManager
    from ansible.modules.network.f5.bigip_file_copy import ArgumentSpec

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
            name='foo',
            source='file.txt',
            force=True
        )

        p = ModuleParameters(params=args)
        assert p.name == 'foo'
        assert p.source == 'file.txt'
        assert p.force is True

    def test_api_parameters(self):
        args = load_fixture('load_sys_file_external-monitor_1.json')
        p = ApiParameters(params=args)
        assert p.checksum == '0c78e6641632e47d11802b29cfd119d2233cb80a'


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create(self, *args):
        # Configure the arguments that would be sent to the Ansible module
        set_module_args(dict(
            name='foo',
            source='file.txt',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            required_if=self.spec.required_if
        )

        tm = IFileManager(module=module)
        tm.exists = Mock(return_value=False)
        tm.create_on_device = Mock(return_value=True)
        tm.upload_to_device = Mock(return_value=True)
        tm.remove_uploaded_file_from_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is True
