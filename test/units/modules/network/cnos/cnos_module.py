# Copyright (C) 2017 Lenovo, Inc.
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
import tempfile

from units.compat import unittest
from units.compat.mock import patch
from ansible.module_utils import basic


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


class AnsibleExitJson(Exception):
    pass


class AnsibleFailJson(Exception):
    pass


class TestCnosModule(unittest.TestCase):
    def setUp(self):
        super(TestCnosModule, self).setUp()

        self.test_log = tempfile.mkstemp(prefix='ansible-test-cnos-module-', suffix='.log')[1]

        self.mock_sleep = patch('time.sleep')
        self.mock_sleep.start()

    def tearDown(self):
        super(TestCnosModule, self).tearDown()

        self.mock_sleep.stop()
        os.remove(self.test_log)

    def execute_module(self, failed=False, changed=False, commands=None,
                       sort=True, defaults=False):

        self.load_fixtures(commands)

        if failed:
            result = self.failed()
            self.assertTrue(result['failed'], result)
        else:
            result = self.changed(changed)
            self.assertEqual(result['changed'], changed, result)

        if commands is not None:
            if sort:
                self.assertEqual(sorted(commands), sorted(result['commands']),
                                 result['commands'])
            else:
                self.assertEqual(commands, result['commands'],
                                 result['commands'])

        return result

    def failed(self):
        def fail_json(*args, **kwargs):
            kwargs['failed'] = True
            raise AnsibleFailJson(kwargs)

        with patch.object(basic.AnsibleModule, 'fail_json', fail_json):
            with self.assertRaises(AnsibleFailJson) as exc:
                self.module.main()

        result = exc.exception.args[0]
        self.assertTrue(result['failed'], result)
        return result

    def changed(self, changed=False):
        def exit_json(*args, **kwargs):
            if 'changed' not in kwargs:
                kwargs['changed'] = False
            raise AnsibleExitJson(kwargs)

        with patch.object(basic.AnsibleModule, 'exit_json', exit_json):
            with self.assertRaises(AnsibleExitJson) as exc:
                self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], changed, result)
        return result

    def load_fixtures(self, commands=None):
        pass
