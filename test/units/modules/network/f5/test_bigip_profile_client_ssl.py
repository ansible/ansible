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

from nose.plugins.skip import SkipTest
if sys.version_info < (2, 7):
    raise SkipTest("F5 Ansible modules require Python >= 2.7")

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import Mock
from ansible.compat.tests.mock import patch
from ansible.module_utils.f5_utils import AnsibleF5Client

try:
    from library.bigip_profile_client_ssl import ModuleParameters
    from library.bigip_profile_client_ssl import ApiParameters
    from library.bigip_profile_client_ssl import ModuleManager
    from library.bigip_profile_client_ssl import ArgumentSpec
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_profile_client_ssl import ModuleParameters
        from ansible.modules.network.f5.bigip_profile_client_ssl import ApiParameters
        from ansible.modules.network.f5.bigip_profile_client_ssl import ModuleManager
        from ansible.modules.network.f5.bigip_profile_client_ssl import ArgumentSpec
        from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
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
            name='foo',
            parent='bar',
            ciphers='!SSLv3:!SSLv2:ECDHE+AES-GCM+SHA256:ECDHE-RSA-AES128-CBC-SHA',
            cert_key_chain=[
                dict(
                    cert='bigip_ssl_cert1',
                    key='bigip_ssl_key1',
                    chain='bigip_ssl_cert1'
                )
            ]
        )

        p = ModuleParameters(args)
        assert p.name == 'foo'
        assert p.parent == '/Common/bar'
        assert p.ciphers == '!SSLv3:!SSLv2:ECDHE+AES-GCM+SHA256:ECDHE-RSA-AES128-CBC-SHA'

    def test_api_parameters(self):
        args = load_fixture('load_ltm_profile_clientssl.json')
        p = ApiParameters(args)
        assert p.name == 'foo'
        assert p.ciphers == 'DEFAULT'


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create(self, *args):
        # Configure the arguments that would be sent to the Ansible module
        set_module_args(dict(
            name='foo',
            parent='bar',
            ciphers='!SSLv3:!SSLv2:ECDHE+AES-GCM+SHA256:ECDHE-RSA-AES128-CBC-SHA',
            cert_key_chain=[
                dict(
                    cert='bigip_ssl_cert1',
                    key='bigip_ssl_key1',
                    chain='bigip_ssl_cert1'
                )
            ],
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
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
