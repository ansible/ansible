# (c) 2018 Red Hat Inc.
#
# (c) 2018 Dell Inc. or its subsidiaries. All Rights Reserved.
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


class TestOpxModule(ModuleTestCase):

    def execute_module(self, failed=False, changed=False,
                       response=None, msg=None, db=None,
                       commit_event=None):

        self.load_fixtures(response)

        if failed:
            result = self.failed(msg)
            self.assertTrue(result['failed'], result)
        else:
            result = self.changed(changed, db)
            self.assertEqual(result['changed'], changed, result)

        return result

    def failed(self, msg):
        with self.assertRaises(AnsibleFailJson) as exc:
            self.module.main()

        result = exc.exception.args[0]
        self.assertTrue(result['failed'], result)
        self.assertEqual(result['msg'], msg, result)
        return result

    def changed(self, changed=False, db=None):
        with self.assertRaises(AnsibleExitJson) as exc:
            self.module.main()

        result = exc.exception.args[0]
        print("res" + str(result) + "dv=" + str(db) + "ch=" + str(changed))
        self.assertEqual(result['changed'], changed, result)
        if db:
            self.assertEqual(result['db'], db, result)

        return result

    def load_fixtures(self, response=None):
        pass
