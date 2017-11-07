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
from ansible.compat.tests.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible.module_utils.f5_utils import AnsibleF5Client
from ansible.module_utils.f5_utils import F5ModuleError

try:
    from library.bigip_device_dns import Parameters
    from library.bigip_device_dns import ModuleManager
    from library.bigip_device_dns import ArgumentSpec
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_device_dns import Parameters
        from ansible.modules.network.f5.bigip_device_dns import ModuleManager
        from ansible.modules.network.f5.bigip_device_dns import ArgumentSpec
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
    def test_module_parameters(self):
        args = dict(
            cache='disable',
            forwarders=['12.12.12.12', '13.13.13.13'],
            ip_version=4,
            name_servers=['10.10.10.10', '11.11.11.11'],
            search=['14.14.14.14', '15.15.15.15'],
            server='localhost',
            user='admin',
            password='password'
        )
        p = Parameters(args)
        assert p.cache == 'disable'
        assert p.name_servers == ['10.10.10.10', '11.11.11.11']
        assert p.search == ['14.14.14.14', '15.15.15.15']

        # BIG-IP considers "ipv4" to be an empty value
        assert p.ip_version == ''

    def test_ipv6_parameter(self):
        args = dict(
            ip_version=6
        )
        p = Parameters(args)
        assert p.ip_version == 'options inet6'

    def test_ensure_forwards_raises_exception(self):
        args = dict(
            forwarders=['12.12.12.12', '13.13.13.13'],
        )
        p = Parameters(args)
        with pytest.raises(F5ModuleError) as ex:
            foo = p.forwarders
        assert 'The modifying of forwarders is not supported' in str(ex)


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    @patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
           return_value=True)
    def test_update_settings(self, *args):
        set_module_args(dict(
            cache='disable',
            forwarders=['12.12.12.12', '13.13.13.13'],
            ip_version=4,
            name_servers=['10.10.10.10', '11.11.11.11'],
            search=['14.14.14.14', '15.15.15.15'],
            server='localhost',
            user='admin',
            password='password'
        ))

        # Configure the parameters that would be returned by querying the
        # remote device
        current = Parameters(
            dict(
                cache='enable'
            )
        )

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)

        # Override methods to force specific logic in the module to happen
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()

        assert results['changed'] is True
