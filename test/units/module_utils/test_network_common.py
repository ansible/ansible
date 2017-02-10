#
# (c) 2016 Red Hat Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock
from ansible.errors import AnsibleModuleExit
from ansible.module_utils import network_common as net
from ansible.module_tuils.network_common import ComplexDict


class TestNetworkCommonModuleUtil(unittest.TestCase):

    def test_to_masklen(self):
        self.assertEqual(24, net.to_masklen('255.255.255.0'))

    def test_to_masklen_invalid(self):
        with self.assertRaises(ValueError):
            net.to_masklen('255')

    def test_to_netmask(self):
        self.assertEqual('255.0.0.0', net.to_netmask(8))
        self.assertEqual('255.0.0.0', net.to_netmask('8'))

    def test_to_netmask_invalid(self):
        with self.assertRaises(ValueError):
            net.to_netmask(128)

    def test_to_subnet(self):
        result = net.to_subnet('192.168.1.1', 24)
        self.assertEqual('192.168.1.0/24', result)

        result = net.to_subnet('192.168.1.1', 24, dotted_notation=True)
        self.assertEqual('192.168.1.0 255.255.255.0', result)

    def test_to_subnet_invalid(self):
        with self.assertRaises(ValueError):
            net.to_subnet('foo', 'bar')

    def test_is_masklen(self):
        self.assertTrue(net.is_masklen(32))
        self.assertFalse(net.is_masklen(33))
        self.assertFalse(net.is_masklen('foo'))

    def test_is_netmask(self):
        self.assertTrue(net.is_netmask('255.255.255.255'))
        self.assertFalse(net.is_netmask(24))
        self.assertFalse(net.is_netmask('foo'))

class TestComplexArgsModuleUtils(unittest.TestCase):

    def test_basic(self):
        set_module_args(dict(name='foo'))

        argument_spec = dict(name=dict())
        module = basic.AnsibleModule(argument_spec)

        spec = dict(
            name=dict(key=True),
            param1=dict(),
            param2=dict()
        )

        transform = ComplexDict(spec, module)
        result = transform(module.params['name'])

        self.assertEqual(result['name'], 'foo')
        self.assertIsNone(result['param1'])
        self.assertIsNone(result['param2'])

    def test_basic_required(self):
        set_module_args(dict(name='foo'))

        argument_spec = dict(name=dict())
        module = basic.AnsibleModule(argument_spec)

        spec = dict(
            name=dict(key=True),
            param1=dict(required=True),
            param2=dict()
        )

        transform = ComplexDict(spec, module)

        with self.assertRaises(ValueError):
            transform(module.params['name'])

    def test_basic_default(self):
        set_module_args(dict(name='foo'))

        argument_spec = dict(name=dict())
        module = basic.AnsibleModule(argument_spec)

        spec = dict(
            name=dict(key=True),
            param1=dict(default='test'),
            param2=dict()
        )

        transform = ComplexDict(spec, module)
        result = transform(module.params['name'])

        self.assertEqual(result['name'], 'foo')
        self.assertEqual(result['param1'], 'test')
        self.assertIsNone(result['param2'])

    def test_basic_type_check(self):
        set_module_args(dict(name={'name': 'foo', 'param1': 'bar'}))

        argument_spec = dict(name=dict(type='dict'))
        module = basic.AnsibleModule(argument_spec)

        spec = dict(
            name=dict(key=True),
            param1=dict(type='bool'),
            param2=dict()
        )

        transform = ComplexDict(spec, module)

        with self.assertRaises(SystemExit):
            transform(module.params['name'])

    def test_basic_read_from(self):
        set_module_args(dict(name='foo'))

        argument_spec = dict(name=dict(), param1=dict(default='test'))
        module = basic.AnsibleModule(argument_spec)

        spec = dict(
            name=dict(key=True),
            param1=dict(read_from='param1'),
            param2=dict()
        )

        transform = ComplexDict(spec, module)
        result = transform(module.params['name'])

        self.assertEqual(result['name'], 'foo')
        self.assertEqual(result['param1'], 'test')
        self.assertIsNone(result['param2'])

    def test_basic_read_from_override(self):
        set_module_args(dict(name='foo'))

        argument_spec = dict(name=dict(), param1=dict(default='test'))
        module = basic.AnsibleModule(argument_spec)

        spec = dict(
            name=dict(key=True),
            param1=dict(default='bar', read_from='param1'),
            param2=dict()
        )

        transform = ComplexDict(spec, module)
        result = transform(module.params['name'])

        self.assertEqual(result['name'], 'foo')
        self.assertEqual(result['param1'], 'bar')
        self.assertIsNone(result['param2'])

    def test_basic_fallback(self):
        set_module_args(dict(name='foo'))

        argument_spec = dict(name=dict(), param1=dict(default='test'))
        module = basic.AnsibleModule(argument_spec)

        spec = dict(
            name=dict(key=True),
            param1=dict(fallback=(basic.env_fallback, ['PATH'],)),
            param2=dict()
        )

        transform = ComplexDict(spec, module)
        result = transform(module.params['name'])

        self.assertEqual(result['name'], 'foo')
        self.assertEqual(result['param1'], os.getenv('PATH'))
        self.assertIsNone(result['param2'])

