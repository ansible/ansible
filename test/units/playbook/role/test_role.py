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

from units.compat import unittest
from units.compat.mock import patch, MagicMock

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.module_utils.common._collections_compat import Container
from ansible.playbook.block import Block

from units.mock.loader import DictDataLoader
from units.mock.path import mock_unfrackpath_noop

from ansible.playbook.role import Role
from ansible.playbook.role.include import RoleInclude
from ansible.playbook.role import hash_params


class TestHashParams(unittest.TestCase):
    def test(self):
        params = {'foo': 'bar'}
        res = hash_params(params)
        self._assert_set(res)
        self._assert_hashable(res)

    def _assert_hashable(self, res):
        a_dict = {}
        try:
            a_dict[res] = res
        except TypeError as e:
            self.fail('%s is not hashable: %s' % (res, e))

    def _assert_set(self, res):
        self.assertIsInstance(res, frozenset)

    def test_dict_tuple(self):
        params = {'foo': (1, 'bar',)}
        res = hash_params(params)
        self._assert_set(res)

    def test_tuple(self):
        params = (1, None, 'foo')
        res = hash_params(params)
        self._assert_hashable(res)

    def test_tuple_dict(self):
        params = ({'foo': 'bar'}, 37)
        res = hash_params(params)
        self._assert_hashable(res)

    def test_list(self):
        params = ['foo', 'bar', 1, 37, None]
        res = hash_params(params)
        self._assert_set(res)
        self._assert_hashable(res)

    def test_dict_with_list_value(self):
        params = {'foo': [1, 4, 'bar']}
        res = hash_params(params)
        self._assert_set(res)
        self._assert_hashable(res)

    def test_empty_set(self):
        params = set([])
        res = hash_params(params)
        self._assert_hashable(res)
        self._assert_set(res)

    def test_generator(self):
        def my_generator():
            for i in ['a', 1, None, {}]:
                yield i

        params = my_generator()
        res = hash_params(params)
        self._assert_hashable(res)

    def test_container_but_not_iterable(self):
        # This is a Container that is not iterable, which is unlikely but...
        class MyContainer(Container):
            def __init__(self, some_thing):
                self.data = []
                self.data.append(some_thing)

            def __contains__(self, item):
                return item in self.data

            def __hash__(self):
                return hash(self.data)

            def __len__(self):
                return len(self.data)

            def __call__(self):
                return False

        foo = MyContainer('foo bar')
        params = foo

        self.assertRaises(TypeError, hash_params, params)

    def test_param_dict_dupe_values(self):
        params1 = {'foo': False}
        params2 = {'bar': False}

        res1 = hash_params(params1)
        res2 = hash_params(params2)

        hash1 = hash(res1)
        hash2 = hash(res2)
        self.assertNotEqual(res1, res2)
        self.assertNotEqual(hash1, hash2)

    def test_param_dupe(self):
        params1 = {
            # 'from_files': {},
            'tags': [],
            u'testvalue': False,
            u'testvalue2': True,
            # 'when': []
        }
        params2 = {
            # 'from_files': {},
            'tags': [],
            u'testvalue': True,
            u'testvalue2': False,
            # 'when': []
        }
        res1 = hash_params(params1)
        res2 = hash_params(params2)

        self.assertNotEqual(hash(res1), hash(res2))
        self.assertNotEqual(res1, res2)

        foo = {}
        foo[res1] = 'params1'
        foo[res2] = 'params2'

        self.assertEqual(len(foo), 2)

        del foo[res2]
        self.assertEqual(len(foo), 1)

        for key in foo:
            self.assertTrue(key in foo)
            self.assertIn(key, foo)


class TestRole(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_load_role_with_tasks(self):

        fake_loader = DictDataLoader({
            "/etc/ansible/roles/foo_tasks/tasks/main.yml": """
            - shell: echo 'hello world'
            """,
        })

        mock_play = MagicMock()
        mock_play.ROLE_CACHE = {}

        i = RoleInclude.load('foo_tasks', play=mock_play, loader=fake_loader)
        r = Role.load(i, play=mock_play)

        self.assertEqual(str(r), 'foo_tasks')
        self.assertEqual(len(r._task_blocks), 1)
        assert isinstance(r._task_blocks[0], Block)

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_load_role_with_tasks_dir_vs_file(self):

        fake_loader = DictDataLoader({
            "/etc/ansible/roles/foo_tasks/tasks/custom_main/foo.yml": """
            - command: bar
            """,
            "/etc/ansible/roles/foo_tasks/tasks/custom_main.yml": """
            - command: baz
            """,
        })

        mock_play = MagicMock()
        mock_play.ROLE_CACHE = {}

        i = RoleInclude.load('foo_tasks', play=mock_play, loader=fake_loader)
        r = Role.load(i, play=mock_play, from_files=dict(tasks='custom_main'))

        self.assertEqual(r._task_blocks[0]._ds[0]['command'], 'baz')

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_load_role_with_handlers(self):

        fake_loader = DictDataLoader({
            "/etc/ansible/roles/foo_handlers/handlers/main.yml": """
            - name: test handler
              shell: echo 'hello world'
            """,
        })

        mock_play = MagicMock()
        mock_play.ROLE_CACHE = {}

        i = RoleInclude.load('foo_handlers', play=mock_play, loader=fake_loader)
        r = Role.load(i, play=mock_play)

        self.assertEqual(len(r._handler_blocks), 1)
        assert isinstance(r._handler_blocks[0], Block)

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_load_role_with_vars(self):

        fake_loader = DictDataLoader({
            "/etc/ansible/roles/foo_vars/defaults/main.yml": """
            foo: bar
            """,
            "/etc/ansible/roles/foo_vars/vars/main.yml": """
            foo: bam
            """,
        })

        mock_play = MagicMock()
        mock_play.ROLE_CACHE = {}

        i = RoleInclude.load('foo_vars', play=mock_play, loader=fake_loader)
        r = Role.load(i, play=mock_play)

        self.assertEqual(r._default_vars, dict(foo='bar'))
        self.assertEqual(r._role_vars, dict(foo='bam'))

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_load_role_with_vars_dirs(self):

        fake_loader = DictDataLoader({
            "/etc/ansible/roles/foo_vars/defaults/main/foo.yml": """
            foo: bar
            """,
            "/etc/ansible/roles/foo_vars/vars/main/bar.yml": """
            foo: bam
            """,
        })

        mock_play = MagicMock()
        mock_play.ROLE_CACHE = {}

        i = RoleInclude.load('foo_vars', play=mock_play, loader=fake_loader)
        r = Role.load(i, play=mock_play)

        self.assertEqual(r._default_vars, dict(foo='bar'))
        self.assertEqual(r._role_vars, dict(foo='bam'))

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_load_role_with_vars_nested_dirs(self):

        fake_loader = DictDataLoader({
            "/etc/ansible/roles/foo_vars/defaults/main/foo/bar.yml": """
            foo: bar
            """,
            "/etc/ansible/roles/foo_vars/vars/main/bar/foo.yml": """
            foo: bam
            """,
        })

        mock_play = MagicMock()
        mock_play.ROLE_CACHE = {}

        i = RoleInclude.load('foo_vars', play=mock_play, loader=fake_loader)
        r = Role.load(i, play=mock_play)

        self.assertEqual(r._default_vars, dict(foo='bar'))
        self.assertEqual(r._role_vars, dict(foo='bam'))

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_load_role_with_vars_nested_dirs_combined(self):

        fake_loader = DictDataLoader({
            "/etc/ansible/roles/foo_vars/defaults/main/foo/bar.yml": """
            foo: bar
            a: 1
            """,
            "/etc/ansible/roles/foo_vars/defaults/main/bar/foo.yml": """
            foo: bam
            b: 2
            """,
        })

        mock_play = MagicMock()
        mock_play.ROLE_CACHE = {}

        i = RoleInclude.load('foo_vars', play=mock_play, loader=fake_loader)
        r = Role.load(i, play=mock_play)

        self.assertEqual(r._default_vars, dict(foo='bar', a=1, b=2))

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_load_role_with_vars_dir_vs_file(self):

        fake_loader = DictDataLoader({
            "/etc/ansible/roles/foo_vars/vars/main/foo.yml": """
            foo: bar
            """,
            "/etc/ansible/roles/foo_vars/vars/main.yml": """
            foo: bam
            """,
        })

        mock_play = MagicMock()
        mock_play.ROLE_CACHE = {}

        i = RoleInclude.load('foo_vars', play=mock_play, loader=fake_loader)
        r = Role.load(i, play=mock_play)

        self.assertEqual(r._role_vars, dict(foo='bam'))

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_load_role_with_metadata(self):

        fake_loader = DictDataLoader({
            '/etc/ansible/roles/foo_metadata/meta/main.yml': """
                allow_duplicates: true
                dependencies:
                  - bar_metadata
                galaxy_info:
                  a: 1
                  b: 2
                  c: 3
            """,
            '/etc/ansible/roles/bar_metadata/meta/main.yml': """
                dependencies:
                  - baz_metadata
            """,
            '/etc/ansible/roles/baz_metadata/meta/main.yml': """
                dependencies:
                  - bam_metadata
            """,
            '/etc/ansible/roles/bam_metadata/meta/main.yml': """
                dependencies: []
            """,
            '/etc/ansible/roles/bad1_metadata/meta/main.yml': """
                1
            """,
            '/etc/ansible/roles/bad2_metadata/meta/main.yml': """
                foo: bar
            """,
            '/etc/ansible/roles/recursive1_metadata/meta/main.yml': """
                dependencies: ['recursive2_metadata']
            """,
            '/etc/ansible/roles/recursive2_metadata/meta/main.yml': """
                dependencies: ['recursive1_metadata']
            """,
        })

        mock_play = MagicMock()
        mock_play.collections = None
        mock_play.ROLE_CACHE = {}

        i = RoleInclude.load('foo_metadata', play=mock_play, loader=fake_loader)
        r = Role.load(i, play=mock_play)

        role_deps = r.get_direct_dependencies()

        self.assertEqual(len(role_deps), 1)
        self.assertEqual(type(role_deps[0]), Role)
        self.assertEqual(len(role_deps[0].get_parents()), 1)
        self.assertEqual(role_deps[0].get_parents()[0], r)
        self.assertEqual(r._metadata.allow_duplicates, True)
        self.assertEqual(r._metadata.galaxy_info, dict(a=1, b=2, c=3))

        all_deps = r.get_all_dependencies()
        self.assertEqual(len(all_deps), 3)
        self.assertEqual(all_deps[0].get_name(), 'bam_metadata')
        self.assertEqual(all_deps[1].get_name(), 'baz_metadata')
        self.assertEqual(all_deps[2].get_name(), 'bar_metadata')

        i = RoleInclude.load('bad1_metadata', play=mock_play, loader=fake_loader)
        self.assertRaises(AnsibleParserError, Role.load, i, play=mock_play)

        i = RoleInclude.load('bad2_metadata', play=mock_play, loader=fake_loader)
        self.assertRaises(AnsibleParserError, Role.load, i, play=mock_play)

        # TODO: re-enable this test once Ansible has proper role dep cycle detection
        # that doesn't rely on stack overflows being recoverable (as they aren't in Py3.7+)
        # see https://github.com/ansible/ansible/issues/61527
        # i = RoleInclude.load('recursive1_metadata', play=mock_play, loader=fake_loader)
        # self.assertRaises(AnsibleError, Role.load, i, play=mock_play)

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_load_role_complex(self):

        # FIXME: add tests for the more complex uses of
        #        params and tags/when statements

        fake_loader = DictDataLoader({
            "/etc/ansible/roles/foo_complex/tasks/main.yml": """
            - shell: echo 'hello world'
            """,
        })

        mock_play = MagicMock()
        mock_play.ROLE_CACHE = {}

        i = RoleInclude.load(dict(role='foo_complex'), play=mock_play, loader=fake_loader)
        r = Role.load(i, play=mock_play)

        self.assertEqual(r.get_name(), "foo_complex")
