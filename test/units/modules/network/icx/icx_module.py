# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json

from units.modules.utils import AnsibleExitJson, AnsibleFailJson, ModuleTestCase


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


class TestICXModule(ModuleTestCase):
    ENV_ICX_USE_DIFF = True

    def set_running_config(self):
        self.ENV_ICX_USE_DIFF = self.get_running_config()

    def get_running_config(self, compare=None):
        if compare is not None:
            diff = compare
        elif os.environ.get('ANSIBLE_CHECK_ICX_RUNNING_CONFIG') is not None:
            if os.environ.get('ANSIBLE_CHECK_ICX_RUNNING_CONFIG') == 'False':
                diff = False
            else:
                diff = True
        else:
            diff = True
        return diff

    def execute_module(self, failed=False, changed=False, commands=None, sort=True, defaults=False, fields=None):

        self.load_fixtures(commands)

        if failed:
            result = self.failed()
            self.assertTrue(result['failed'], result)
        else:
            result = self.changed(changed)
            self.assertEqual(result['changed'], changed, result)

        if commands is not None:
            if sort:
                self.assertEqual(sorted(commands), sorted(result['commands']))
            else:
                self.assertEqual(commands, result['commands'], result['commands'])

        if fields is not None:
            for key in fields:
                if fields.get(key) is not None:
                    self.assertEqual(fields.get(key), result.get(key))

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

    def load_fixtures(self, commands=None):
        pass
