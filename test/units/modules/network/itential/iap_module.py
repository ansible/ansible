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

import json
import os
import unittest
from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase


# fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
# fixture_data = {}
#
#
# def load_fixture(name):
#     path = os.path.join(fixture_path, name)
#
#     if path in fixture_data:
#         return fixture_data[path]
#
#     with open(path) as f:
#         data = f.read()
#
#     try:
#         data = json.loads(data)
#     except:
#         pass
#
#     fixture_data[path] = data
#     return data


class TestIapModule(ModuleTestCase):
    def broken_function(self):
        raise Exception('This is broken')

    def execute_module(self, iap_port=None, token_key=None, defaults=False):
        # self.load_fixtures(iap_port, token_key)
        if iap_port is not None:
            self.assertEqual(iap_port, '5555')
            iap_port_result = 'Found iap_port {}'.format(iap_port)
        else:
            self.assertEqual(iap_port, None)
            iap_port_result = 'No iap_port found'

        if token_key is not None:
            self.assertEqual(token_key, 'sffsf')
            token_key_result = 'Found token_key {}'.format(token_key)
        else:
            self.assertNotEqual(token_key, None)
            token_key_result = 'No token_key found'
        result = dict(iap_port=iap_port_result, token_key=token_key_result)
        return result

    def failed(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            self.module.main()

        result = exc.exception.args[0]
        self.assertTrue(result['failed'], result)
        return result

    def changed(self, changed=False):
        with self.assertRaises(AnsibleExitJson) as exc:
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], changed, result)
        return result


if __name__ == '__main__':
    unittest.main()
