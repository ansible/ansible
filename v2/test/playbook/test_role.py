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
from ansible.compat.tests.mock import patch, MagicMock

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.playbook.block import Block
from ansible.playbook.role import Role
from ansible.playbook.role.include import RoleInclude
from ansible.playbook.task import Task

from test.mock.loader import DictDataLoader

class TestRole(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_load_role_with_tasks(self):

        fake_loader = DictDataLoader({
            "/etc/ansible/roles/foo/tasks/main.yml": """
            - shell: echo 'hello world'
            """,
        })

        i = RoleInclude.load('foo', loader=fake_loader)
        r = Role.load(i)

        self.assertEqual(str(r), 'foo')
        self.assertEqual(len(r._task_blocks), 1)
        assert isinstance(r._task_blocks[0], Block)

    def test_load_role_with_handlers(self):

        fake_loader = DictDataLoader({
            "/etc/ansible/roles/foo/handlers/main.yml": """
            - name: test handler
              shell: echo 'hello world'
            """,
        })

        i = RoleInclude.load('foo', loader=fake_loader)
        r = Role.load(i)

        self.assertEqual(len(r._handler_blocks), 1)
        assert isinstance(r._handler_blocks[0], Block)

    def test_load_role_with_vars(self):

        fake_loader = DictDataLoader({
            "/etc/ansible/roles/foo/defaults/main.yml": """
            foo: bar
            """,
            "/etc/ansible/roles/foo/vars/main.yml": """
            foo: bam
            """,
        })

        i = RoleInclude.load('foo', loader=fake_loader)
        r = Role.load(i)

        self.assertEqual(r._default_vars, dict(foo='bar'))
        self.assertEqual(r._role_vars, dict(foo='bam'))

    def test_load_role_with_metadata(self):

        fake_loader = DictDataLoader({
            '/etc/ansible/roles/foo/meta/main.yml': """
                allow_duplicates: true
                dependencies:
                  - bar
                galaxy_info:
                  a: 1
                  b: 2
                  c: 3
            """,
            '/etc/ansible/roles/bar/meta/main.yml': """
                dependencies:
                  - baz
            """,
            '/etc/ansible/roles/baz/meta/main.yml': """
                dependencies:
                  - bam
            """,
            '/etc/ansible/roles/bam/meta/main.yml': """
                dependencies: []
            """,
            '/etc/ansible/roles/bad1/meta/main.yml': """
                1
            """,
            '/etc/ansible/roles/bad2/meta/main.yml': """
                foo: bar
            """,
            '/etc/ansible/roles/recursive1/meta/main.yml': """
                dependencies: ['recursive2']
            """,
            '/etc/ansible/roles/recursive2/meta/main.yml': """
                dependencies: ['recursive1']
            """,
        })

        i = RoleInclude.load('foo', loader=fake_loader)
        r = Role.load(i)

        role_deps = r.get_direct_dependencies()

        self.assertEqual(len(role_deps), 1)
        self.assertEqual(type(role_deps[0]), Role)
        self.assertEqual(len(role_deps[0].get_parents()), 1)
        self.assertEqual(role_deps[0].get_parents()[0], r)
        self.assertEqual(r._metadata.allow_duplicates, True)
        self.assertEqual(r._metadata.galaxy_info, dict(a=1, b=2, c=3))

        all_deps = r.get_all_dependencies()
        self.assertEqual(len(all_deps), 3)
        self.assertEqual(all_deps[0].get_name(), 'bar')
        self.assertEqual(all_deps[1].get_name(), 'baz')
        self.assertEqual(all_deps[2].get_name(), 'bam')

        i = RoleInclude.load('bad1', loader=fake_loader)
        self.assertRaises(AnsibleParserError, Role.load, i)

        i = RoleInclude.load('bad2', loader=fake_loader)
        self.assertRaises(AnsibleParserError, Role.load, i)

        i = RoleInclude.load('recursive1', loader=fake_loader)
        self.assertRaises(AnsibleError, Role.load, i)

    def test_load_role_complex(self):

        # FIXME: add tests for the more complex uses of
        #        params and tags/when statements

        fake_loader = DictDataLoader({
            "/etc/ansible/roles/foo/tasks/main.yml": """
            - shell: echo 'hello world'
            """,
        })

        i = RoleInclude.load(dict(role='foo'), loader=fake_loader)
        r = Role.load(i)

        self.assertEqual(r.get_name(), "foo")

