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
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible.module_utils.f5_utils import AnsibleF5Client

try:
    from library.bigip_device_trust import Parameters
    from library.bigip_device_trust import ModuleManager
    from library.bigip_device_trust import ArgumentSpec
    from library.bigip_device_trust import HAS_F5SDK
    from library.bigip_device_trust import HAS_NETADDR
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_device_trust import Parameters
        from ansible.modules.network.f5.bigip_device_trust import ModuleManager
        from ansible.modules.network.f5.bigip_device_trust import ArgumentSpec
        from ansible.modules.network.f5.bigip_device_trust import HAS_F5SDK
        from ansible.modules.network.f5.bigip_device_trust import HAS_NETADDR
        from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
    except ImportError:
        raise SkipTest("F5 Ansible modules require the f5-sdk Python library")

    from ansible.modules.network.f5.bigip_device_trust import HAS_NETADDR
    if not HAS_NETADDR:
        raise SkipTest("F5 Ansible modules require the netaddr Python library")

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
            peer_server='10.10.10.10',
            peer_hostname='foo.bar.baz',
            peer_user='admin',
            peer_password='secret'
        )

        p = Parameters(args)
        assert p.peer_server == '10.10.10.10'
        assert p.peer_hostname == 'foo.bar.baz'
        assert p.peer_user == 'admin'
        assert p.peer_password == 'secret'

    def test_module_parameters_with_peer_type(self):
        args = dict(
            peer_server='10.10.10.10',
            peer_hostname='foo.bar.baz',
            peer_user='admin',
            peer_password='secret',
            type='peer'
        )

        p = Parameters(args)
        assert p.peer_server == '10.10.10.10'
        assert p.peer_hostname == 'foo.bar.baz'
        assert p.peer_user == 'admin'
        assert p.peer_password == 'secret'
        assert p.type is True

    def test_module_parameters_with_subordinate_type(self):
        args = dict(
            peer_server='10.10.10.10',
            peer_hostname='foo.bar.baz',
            peer_user='admin',
            peer_password='secret',
            type='subordinate'
        )

        p = Parameters(args)
        assert p.peer_server == '10.10.10.10'
        assert p.peer_hostname == 'foo.bar.baz'
        assert p.peer_user == 'admin'
        assert p.peer_password == 'secret'
        assert p.type is False


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_device_trust(self, *args):
        set_module_args(dict(
            peer_server='10.10.10.10',
            peer_hostname='foo.bar.baz',
            peer_user='admin',
            peer_password='secret',
            server='localhost',
            password='password',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        mm = ModuleManager(client)
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True

    def test_create_device_trust_idempotent(self, *args):
        set_module_args(dict(
            peer_server='10.10.10.10',
            peer_hostname='foo.bar.baz',
            peer_user='admin',
            peer_password='secret',
            server='localhost',
            password='password',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        mm = ModuleManager(client)
        mm.exists = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is False
