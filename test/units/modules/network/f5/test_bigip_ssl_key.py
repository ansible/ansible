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
from ansible.module_utils import basic
from ansible.compat.tests.mock import patch, Mock
from ansible.module_utils._text import to_bytes
from ansible.module_utils.f5_utils import AnsibleF5Client

try:
    from library.bigip_ssl_key import ArgumentSpec
    from library.bigip_ssl_key import Parameters
    from library.bigip_ssl_key import ModuleManager
    from library.bigip_ssl_key import HAS_F5SDK
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_ssl_key import ArgumentSpec
        from ansible.modules.network.f5.bigip_ssl_key import Parameters
        from ansible.modules.network.f5.bigip_ssl_key import ModuleManager
        from ansible.modules.network.f5.bigip_ssl_key import HAS_F5SDK
        from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
    except ImportError:
        raise SkipTest("F5 Ansible modules require the f5-sdk Python library")

fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
fixture_data = {}


def set_module_args(args):
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


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
        p = Parameters(args)
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


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
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

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        cm = ModuleManager(client)
        cm.exists = Mock(side_effect=[False, True])
        cm.create_on_device = Mock(return_value=True)

        results = cm.exec_module()

        assert results['changed'] is True
