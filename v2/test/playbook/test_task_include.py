# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

from ansible.compat.tests import unittest
from ansible.errors import AnsibleParserError
from ansible.parsing.yaml.objects import AnsibleMapping
from ansible.playbook.task_include import TaskInclude

from test.mock.loader import DictDataLoader

class TestTaskInclude(unittest.TestCase):

    def setUp(self):
        self._fake_loader = DictDataLoader({
            "foo.yml": """
            - shell: echo "hello world"
            """
        })

        pass

    def tearDown(self):
        pass

    def test_empty_task_include(self):
        ti = TaskInclude()

    def test_basic_task_include(self):
        ti = TaskInclude.load(AnsibleMapping(include='foo.yml'), loader=self._fake_loader)
        tasks = ti.compile()

    def test_task_include_with_loop(self):
        ti = TaskInclude.load(AnsibleMapping(include='foo.yml', with_items=['a', 'b', 'c']), loader=self._fake_loader)

    def test_task_include_with_conditional(self):
        ti = TaskInclude.load(AnsibleMapping(include='foo.yml', when="1 == 1"), loader=self._fake_loader)

    def test_task_include_with_tags(self):
        ti = TaskInclude.load(AnsibleMapping(include='foo.yml', tags="foo"), loader=self._fake_loader)
        ti = TaskInclude.load(AnsibleMapping(include='foo.yml', tags=["foo", "bar"]), loader=self._fake_loader)

    def test_task_include_errors(self):
        self.assertRaises(AnsibleParserError, TaskInclude.load, AnsibleMapping(include=''), loader=self._fake_loader)
        self.assertRaises(AnsibleParserError, TaskInclude.load, AnsibleMapping(include='foo.yml', vars="1"), loader=self._fake_loader)
        self.assertRaises(AnsibleParserError, TaskInclude.load, AnsibleMapping(include='foo.yml a=1', vars=dict(b=2)), loader=self._fake_loader)

