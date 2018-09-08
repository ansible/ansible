# Copyright: (c) 2018, Pluribus Networks
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
import tempfile

from units.compat import unittest
from units.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes


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


class TestNvosModule(unittest.TestCase):
    def setUp(self):
        super(TestNvosModule, self).setUp()

        self.test_log = tempfile.mkstemp(prefix='ansible-test-nvos-module-', suffix='.log')[1]

    def tearDown(self):
        super(TestNvosModule, self).tearDown()

        os.remove(self.test_log)

    def execute_module(self, failed=False, changed=False, commands=None,
                       sort=True, defaults=False, state=None):

        self.load_fixtures(commands, state)

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
