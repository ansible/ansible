# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
import pytest
import sys

from nose.plugins.skip import SkipTest
if sys.version_info < (2, 7):
    raise SkipTest("F5 Ansible modules require Python >= 2.7")

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import Mock
from ansible.compat.tests.mock import patch
from ansible.module_utils.basic import AnsibleModule

try:
    from library.modules.bigip_software_image import ApiParameters
    from library.modules.bigip_software_image import ModuleParameters
    from library.modules.bigip_software_image import ModuleManager
    from library.modules.bigip_software_image import ArgumentSpec
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_software_image import ApiParameters
        from ansible.modules.network.f5.bigip_software_image import ModuleParameters
        from ansible.modules.network.f5.bigip_software_image import ModuleManager
        from ansible.modules.network.f5.bigip_software_image import ArgumentSpec
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
            filename='/path/to/BIGIP-13.0.0.0.0.1645.iso',
            image='/path/to/BIGIP-13.0.0.0.0.1645.iso',
        )

        p = ModuleParameters(params=args)
        assert p.filename == 'BIGIP-13.0.0.0.0.1645.iso'
        assert p.image == '/path/to/BIGIP-13.0.0.0.0.1645.iso'

    def test_api_parameters(self):
        args = dict(
            file_size='1000 MB',
            build='0.0.3',
            checksum='8cdbd094195fab4b2b47ff4285577b70',
            image_type='release',
            version='13.1.0.8'
        )

        p = ApiParameters(params=args)
        assert p.file_size == 1000
        assert p.build == '0.0.3'
        assert p.checksum == '8cdbd094195fab4b2b47ff4285577b70'
        assert p.image_type == 'release'
        assert p.version == '13.1.0.8'


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create(self, *args):
        set_module_args(dict(
            image='/path/to/BIGIP-13.0.0.0.0.1645.iso',
            server='localhost',
            password='password',
            user='admin'
        ))

        current = ApiParameters(params=load_fixture('load_sys_software_image_1.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods in the specific type of manager
        mm = ModuleManager(module=module)
        mm.exists = Mock(side_effect=[False, True])
        mm.read_current_from_device = Mock(return_value=current)
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['file_size'] == 1948
