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

from __future__ import annotations

from collections.abc import Container

import pytest

import unittest
from unittest.mock import patch, MagicMock

from ansible.errors import AnsibleError, AnsibleParserError
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

    @staticmethod
    def _assert_hashable(res):
        hash(res)

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
            yield

        params = my_generator()
        res = hash_params(params)
        self._assert_hashable(res)
        assert list(params)

    def test_container_but_not_iterable(self):
        # This is a Container that is not iterable, which is unlikely but...
        class MyContainer(Container):
            def __init__(self, _some_thing):
                pass

            def __contains__(self, item):
                """Implementation omitted, since it will never be called."""

        params = MyContainer('foo bar')

        with pytest.raises(TypeError) as ex:
            hash_params(params)

        assert ex.value.args == ("'MyContainer' object is not iterable",)

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

        params_dict = {}
        params_dict[res1] = 'params1'
        params_dict[res2] = 'params2'

        self.assertEqual(len(params_dict), 2)

        del params_dict[res2]
        self.assertEqual(len(params_dict), 1)

        for key in params_dict:
            self.assertTrue(key in params_dict)
            self.assertIn(key, params_dict)


class TestRole(unittest.TestCase):

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_load_role_with_tasks(self):

        fake_loader = DictDataLoader({
            "/etc/ansible/roles/foo_tasks/tasks/main.yml": """
            - shell: echo 'hello world'
            """,
        })

        mock_play = MagicMock()
        mock_play.role_cache = {}

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
        mock_play.role_cache = {}

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
        mock_play.role_cache = {}

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
        mock_play.role_cache = {}

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
        mock_play.role_cache = {}

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
        mock_play.role_cache = {}

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
        mock_play.role_cache = {}

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
        mock_play.role_cache = {}

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
        mock_play.role_cache = {}

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
        mock_play.role_cache = {}

        i = RoleInclude.load(dict(role='foo_complex'), play=mock_play, loader=fake_loader)
        r = Role.load(i, play=mock_play)

        self.assertEqual(r.get_name(), "foo_complex")


class TestAlternativeRoleLayouts(unittest.TestCase):
    """Roles may use <subdir>.yml or an all-in-one main.yml in the role directory instead of <subdir>/main.yml."""

    R = "/etc/ansible/roles/foo/"

    @staticmethod
    def _load(files, from_files=None):
        fake_loader = DictDataLoader(
            {k if k.startswith('/') else TestAlternativeRoleLayouts.R + k: v for k, v in files.items()})
        mock_play = MagicMock()
        mock_play.role_cache = {}
        i = RoleInclude.load('foo', play=mock_play, loader=fake_loader)
        with patch('ansible.playbook.role._display.warning') as warning:
            role = Role.load(i, play=mock_play, from_files=from_files)
        # other warnings can be emitted while loading, only look at ours
        warnings = [c[0][0] for c in warning.call_args_list if 'more than one layout' in c[0][0]]
        return role, warnings

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_flat_files(self):
        r, warnings = self._load({
            "tasks.yml": "- debug: msg=hi\n",
            "handlers.yaml": "- name: h\n  debug: msg=h\n",
            "defaults.yml": "a: 1\n",
            "vars.json": '{"b": 2}',
            "meta.yml": "allow_duplicates: true\n",
        })
        assert warnings == []
        assert len(r._task_blocks) == 1
        assert len(r._handler_blocks) == 1
        assert r._default_vars == {'a': 1}
        assert r._role_vars == {'b': 2}
        assert r._metadata.allow_duplicates is True

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_all_in_one_main_yml(self):
        r, warnings = self._load({
            "main.yml": """
            meta: {allow_duplicates: true}
            defaults: {a: 1}
            vars: {b: 2}
            tasks:
              - debug: msg=hi
            handlers:
              - name: h
                debug: msg=h
            """,
        })
        assert warnings == []
        assert len(r._task_blocks) == 1
        assert len(r._handler_blocks) == 1
        assert r._default_vars == {'a': 1}
        assert r._role_vars == {'b': 2}
        assert r._metadata.allow_duplicates is True

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_all_in_one_main_json(self):
        r, warnings = self._load({"main.json": '{"defaults": {"a": 1}}'})
        assert warnings == []
        assert r._default_vars == {'a': 1}

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_priority_is_conventional_then_flat_then_all_in_one(self):
        # every layout defines tasks; conventional wins, the other two are reported
        r, warnings = self._load({
            "tasks/main.yml": "- debug: msg=conventional\n- debug: msg=two\n",
            "tasks.yml": "- debug: msg=flat\n",
            "main.yml": "tasks:\n  - debug: msg=allinone\n",
        })
        assert len(r._task_blocks[0].block) == 2
        assert len(warnings) == 1
        assert "'tasks'" in warnings[0] and "using 'tasks/'" in warnings[0]
        assert "tasks.yml" in warnings[0] and "main.yml" in warnings[0]

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_vars_and_defaults_are_merged_conventional_last(self):
        # dictionaries are merged like the files of a vars/main/ directory; conventional wins conflicts
        for subdir in ('vars', 'defaults'):
            attr = '_role_vars' if subdir == 'vars' else '_default_vars'
            r, warnings = self._load({
                f"{subdir}/main.yml": "a: 1\nx: conventional\n",
                f"{subdir}.yml": "b: 2\nx: flat\n",
                "main.yml": f"{subdir}: {{c: 3, x: allinone}}\n",
            })
            assert getattr(r, attr) == {'a': 1, 'b': 2, 'c': 3, 'x': 'conventional'}, subdir
            assert len(warnings) == 1, subdir
            assert "merging them" in warnings[0] and f"'{subdir}/' takes precedence" in warnings[0], subdir

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_merge_without_conventional_flat_beats_all_in_one(self):
        r, warnings = self._load({"vars.yml": "x: flat\nf: 1\n", "main.yml": "vars: {x: allinone, m: 2}\n"})
        assert r._role_vars == {'x': 'flat', 'f': 1, 'm': 2}
        assert len(warnings) == 1 and "'vars.yml' takes precedence" in warnings[0]

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_meta_is_not_merged(self):
        # like tasks and handlers, meta has a single winner
        r, warnings = self._load({
            "meta.yml": "allow_duplicates: true\n",
            "main.yml": "meta: {allow_duplicates: false, dependencies: []}\n",
        })
        assert r._metadata.allow_duplicates is True
        assert len(warnings) == 1 and "using 'meta.yml'" in warnings[0] and "ignoring main.yml" in warnings[0]

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_vars_directory_merge_is_unchanged_and_silent(self):
        r, warnings = self._load({"vars/main/a.yml": "a: 1\nx: a\n", "vars/main/b.yml": "b: 2\nx: b\n"})
        assert warnings == []
        assert r._role_vars == {'a': 1, 'b': 2, 'x': 'b'}

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_all_in_one_fills_in_what_other_layouts_do_not_define(self):
        r, warnings = self._load({
            "main.yml": "tasks:\n  - debug: msg=allinone\nhandlers:\n  - name: h\n    debug: msg=h\n",
            "tasks/main.yml": "- debug: msg=conventional\n",
        })
        # tasks come from tasks/ (and main.yml's tasks are reported), handlers from main.yml (nothing to compare)
        assert r._task_blocks[0].block[0].args['msg'] == 'conventional'
        assert len(r._handler_blocks) == 1
        assert len(warnings) == 1 and "'tasks'" in warnings[0]

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_extension_collision_is_silent_like_main_yml(self):
        r, warnings = self._load({
            "tasks.yml": "- debug: msg=one\n- debug: msg=two\n",
            "tasks.yaml": "- debug: msg=ignored\n",
            "tasks.json": '[{"debug": {"msg": "ignored"}}]',
        })
        assert warnings == []
        assert len(r._task_blocks[0].block) == 2

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_unrelated_files_with_similar_names_are_ignored(self):
        # these hold valid tasks, so if they were mistaken for role files the result (or a warning) would change
        junk = "- debug: msg=junk\n- debug: msg=junk2\n- debug: msg=junk3\n"
        r, warnings = self._load({
            "tasks.bak": junk,
            "tasks.md": junk,
            "tasks.yml.bak": junk,
            "tasks.yml~": junk,
            "tasks.txt": junk,
            "main.bak": "tasks:\n  - debug: msg=junk\n",
            "tasks/main.yml": "- debug: msg=conventional\n",
        })
        assert warnings == []
        assert len(r._task_blocks[0].block) == 1
        assert r._task_blocks[0].block[0].args['msg'] == 'conventional'

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_extensionless_files_are_not_role_files(self):
        r, warnings = self._load({
            "handlers": "- name: h\n  debug: msg=h\n",
            "main": "defaults: {a: 1}\n",
            "tasks/main.yml": "- debug: msg=hi\n",
        })
        assert warnings == []
        assert r._handler_blocks == [] and r._default_vars == {}

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_explicit_entry_point_does_not_consult_alternative_layouts(self):
        # tasks_from=install names a file in tasks/, the alternatives are stand-ins for the default entry point only
        r, warnings = self._load({
            "tasks/main.yml": "- debug: msg=default\n",
            "tasks/install.yml": "- debug: msg=install\n",
            "tasks.yml": "- debug: msg=flat\n",
            "main.yml": "tasks:\n  - debug: msg=allinone\n",
        }, from_files={'tasks': 'install'})
        assert warnings == []
        assert r._task_blocks[0].block[0].args['msg'] == 'install'

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_explicit_entry_point_without_data_does_not_fall_back_to_the_default_one(self):
        r, warnings = self._load({
            "tasks/empty.yml": "---\n# nothing\n",
            "tasks.yml": "- debug: msg=flat\n",
        }, from_files={'tasks': 'empty'})
        assert warnings == []
        assert r._task_blocks == []

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_argument_specs_file_is_not_a_competitor_of_flat_meta(self):
        r, warnings = self._load({
            "meta/argument_specs.yml": "argument_specs:\n  main:\n    short_description: s\n    options: {}\n",
            "meta.yml": "allow_duplicates: true\n",
            "tasks/main.yml": "- debug: msg=hi\n",
        })
        assert warnings == []
        assert r._metadata.allow_duplicates is True

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_mixing_layouts_across_subdirs_is_fine(self):
        r, warnings = self._load({
            "tasks/main.yml": "- debug: msg=hi\n",
            "handlers.yml": "- name: h\n  debug: msg=h\n",
            "defaults/main.yml": "a: 1\n",
        })
        assert warnings == []
        assert len(r._task_blocks) == 1 and len(r._handler_blocks) == 1 and r._default_vars == {'a': 1}

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_galaxy_init_stub_does_not_cause_ambiguity(self):
        # ansible-galaxy role init creates comment-only main.yml stubs; these contain no data
        r, warnings = self._load({
            "handlers/main.yml": "---\n# handlers file for foo\n",
            "tasks/main.yml": "---\n# tasks file for foo\n",
            "main.yml": "tasks:\n  - debug: msg=hi\nhandlers:\n  - name: h\n    debug: msg=h\n",
        })
        assert warnings == []
        assert len(r._task_blocks) == 1 and len(r._handler_blocks) == 1

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_conventional_only_is_untouched(self):
        r, warnings = self._load({"tasks/main.yml": "- debug: msg=hi\n"})
        assert warnings == []
        assert len(r._task_blocks) == 1

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_stray_main_yml_that_is_not_a_role_definition_is_ignored(self):
        # existing roles may have an unrelated main.yml in their root; it must not change anything
        for stray in ("- hosts: all\n  tasks: []\n", "just_a_var: 1\n", "---\n# nothing\n", "[]"):
            r, warnings = self._load({"main.yml": stray, "tasks/main.yml": "- debug: msg=conventional\n"})
            assert warnings == [], stray
            assert len(r._task_blocks) == 1, stray

    @patch('ansible.playbook.role.definition.unfrackpath', mock_unfrackpath_noop)
    def test_main_yml_unknown_key_next_to_valid_key(self):
        with pytest.raises(AnsibleError, match="Unknown top-level key.*taskz"):
            self._load({"main.yml": "tasks: []\ntaskz: []\n"})
