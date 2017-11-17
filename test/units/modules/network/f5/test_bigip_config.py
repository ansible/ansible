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
    from library.bigip_config import Parameters
    from library.bigip_config import ModuleManager
    from library.bigip_config import ArgumentSpec
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_config import Parameters
        from ansible.modules.network.f5.bigip_config import ModuleManager
        from ansible.modules.network.f5.bigip_config import ArgumentSpec
        from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
    except ImportError:
        raise SkipTest("F5 Ansible modules require the f5-sdk Python library")

fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
fixture_data = {}


def load_fixture(name):
    path = os.path.join(fixture_path, name)
    with open(path) as f:
        data = f.read()
    try:
        data = json.loads(data)
    except Exception:
        pass
    return data


class TestParameters(unittest.TestCase):
    def test_module_parameters(self):
        args = dict(
            save='yes',
            reset='yes',
            merge_content='asdasd',
            verify='no',
            server='localhost',
            user='admin',
            password='password'
        )
        p = Parameters(args)
        assert p.save == 'yes'
        assert p.reset == 'yes'
        assert p.merge_content == 'asdasd'


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_run_single_command(self, *args):
        set_module_args(dict(
            save='yes',
            reset='yes',
            merge_content='asdasd',
            verify='no',
            server='localhost',
            user='admin',
            password='password'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)

        # Override methods to force specific logic in the module to happen
        mm.exit_json = Mock(return_value=True)
        mm.reset_device = Mock(return_value=True)
        mm.upload_to_device = Mock(return_value=True)
        mm.move_on_device = Mock(return_value=True)
        mm.merge_on_device = Mock(return_value=True)
        mm.remove_temporary_file = Mock(return_value=True)
        mm.save_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
