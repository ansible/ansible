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
    from library.modules.bigip_log_destination import V1ApiParameters
    from library.modules.bigip_log_destination import V2ApiParameters
    from library.modules.bigip_log_destination import V1ModuleParameters
    from library.modules.bigip_log_destination import V2ModuleParameters
    from library.modules.bigip_log_destination import ModuleManager
    from library.modules.bigip_log_destination import V1Manager
    from library.modules.bigip_log_destination import V2Manager
    from library.modules.bigip_log_destination import ArgumentSpec
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_log_destination import V1ApiParameters
        from ansible.modules.network.f5.bigip_log_destination import V2ApiParameters
        from ansible.modules.network.f5.bigip_log_destination import V1ModuleParameters
        from ansible.modules.network.f5.bigip_log_destination import V2ModuleParameters
        from ansible.modules.network.f5.bigip_log_destination import ModuleManager
        from ansible.modules.network.f5.bigip_log_destination import V1Manager
        from ansible.modules.network.f5.bigip_log_destination import V2Manager
        from ansible.modules.network.f5.bigip_log_destination import ArgumentSpec
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


class TestV1Parameters(unittest.TestCase):
    def test_module_parameters(self):
        args = dict(
            name='foo',
            syslog_settings=dict(
                forward_to='pool1',
                syslog_format='rfc5424'
            ),
            password='password',
            server='localhost',
            user='admin'
        )
        p = V1ModuleParameters(params=args)
        assert p.name == 'foo'
        assert p.forward_to == '/Common/pool1'
        assert p.syslog_format == 'rfc5424'

    def test_api_parameters(self):
        args = load_fixture('load_sys_log_config_destination_1.json')
        p = V1ApiParameters(params=args)
        assert p.name == 'foo'
        assert p.syslog_format == 'rfc5424'
        assert p.forward_to == '/Common/pool1'


class TestV1Manager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_policy(self, *args):
        set_module_args(dict(
            name="foo",
            type='remote-syslog',
            syslog_settings=dict(
                forward_to='pool1',
            ),
            state='present',
            password='password',
            server='localhost',
            user='admin'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods in the specific type of manager
        tm = V1Manager(module=module, params=module.params)
        tm.exists = Mock(return_value=False)
        tm.create_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is True
