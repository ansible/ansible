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
    from library.modules.bigip_ssl_key import ArgumentSpec
    from library.modules.bigip_ssl_key import Parameters
    from library.modules.bigip_ssl_key import ModuleManager
    from library.modules.bigip_ssl_key import HAS_F5SDK
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_ssl_key import ArgumentSpec
        from ansible.modules.network.f5.bigip_ssl_key import Parameters
        from ansible.modules.network.f5.bigip_ssl_key import ModuleManager
        from ansible.modules.network.f5.bigip_ssl_key import HAS_F5SDK
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
    def test_module_parameters_key(self):
        key_content = load_fixture('create_insecure_key1.key')
        args = dict(
            content=key_content,
            name="cert1",
            partition="Common",
            state="present",
            password='password',
            server='localhost',
            user='admin'
        )
        p = Parameters(params=args)
        assert p.name == 'cert1'
        assert p.key_filename == 'cert1.key'
        assert '-----BEGIN RSA PRIVATE KEY-----' in p.content
        assert '-----END RSA PRIVATE KEY-----' in p.content
        assert p.key_checksum == '91bdddcf0077e2bb2a0258aae2ae3117be392e83'
        assert p.state == 'present'
        assert p.user == 'admin'
        assert p.server == 'localhost'
        assert p.password == 'password'
        assert p.partition == 'Common'


class TestModuleManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_import_key_no_key_passphrase(self, *args):
        set_module_args(dict(
            name='foo',
            content=load_fixture('cert1.key'),
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
        cm = ModuleManager(module=module)
        cm.exists = Mock(side_effect=[False, True])
        cm.create_on_device = Mock(return_value=True)

        results = cm.exec_module()

        assert results['changed'] is True
