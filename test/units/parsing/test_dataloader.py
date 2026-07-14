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

import collections
import os
import pathlib
import tempfile

import unittest
from unittest.mock import patch

import pytest

from ansible.errors import AnsibleParserError, AnsibleFileNotFound
from ansible.parsing.vault import AnsibleVaultError
from ansible.module_utils.common.text.converters import to_text
from ansible._internal._datatag._tags import Origin, SourceWasEncrypted, TrustedAsTemplate

from units.mock.vault_helper import TextVaultSecret
from ansible.parsing.dataloader import DataLoader

from units.mock.path import mock_unfrackpath_noop
from units.test_utils.controller.display import emits_warnings


class TestDataLoader(unittest.TestCase):

    def setUp(self):
        self._loader = DataLoader()

    @patch('os.path.exists')
    def test__is_role(self, p_exists):
        p_exists.side_effect = lambda p: p == 'test_path/tasks/main.yml'
        self.assertTrue(self._loader._is_role('test_path/tasks'))
        self.assertTrue(self._loader._is_role('test_path/'))

    @patch.object(DataLoader, '_get_file_contents')
    def test_parse_json_from_file(self, mock_def):
        mock_def.return_value = (b"""{"a": 1, "b": 2, "c": 3}""", True)
        output = self._loader.load_from_file('dummy_json.txt')
        self.assertEqual(output, dict(a=1, b=2, c=3))

    @patch.object(DataLoader, '_get_file_contents')
    def test_parse_yaml_from_file(self, mock_def):
        mock_def.return_value = (b"""
        a: 1
        b: 2
        c: 3
        """, True)
        output = self._loader.load_from_file('dummy_yaml.txt')
        self.assertEqual(output, dict(a=1, b=2, c=3))

    @patch.object(DataLoader, '_get_file_contents')
    def test_parse_fail_from_file(self, mock_def):
        mock_def.return_value = (b"""
        TEXT:
            ***
               NOT VALID
        """, True)
        self.assertRaises(AnsibleParserError, self._loader.load_from_file, 'dummy_yaml_bad.txt')

    @patch('ansible.parsing.dataloader.unfrackpath', mock_unfrackpath_noop)
    @patch.object(DataLoader, '_is_role')
    def test_path_dwim_relative(self, mock_is_role):
        """
        simulate a nested dynamic include:

        playbook.yml:
        - hosts: localhost
          roles:
            - { role: 'testrole' }

        testrole/tasks/main.yml:
        - include_tasks: "include1.yml"
          static: no

        testrole/tasks/include1.yml:
        - include_tasks: include2.yml
          static: no

        testrole/tasks/include2.yml:
        - debug: msg="blah"
        """
        mock_is_role.return_value = False
        with patch('os.path.exists') as mock_os_path_exists:
            mock_os_path_exists.return_value = False
            self._loader.path_dwim_relative('/tmp/roles/testrole/tasks', 'tasks', 'included2.yml')

            # Fetch first args for every call
            # mock_os_path_exists.assert_any_call isn't used because os.path.normpath must be used in order to compare paths
            called_args = [os.path.normpath(to_text(call[0][0])) for call in mock_os_path_exists.call_args_list]

            # 'path_dwim_relative' docstrings say 'with or without explicitly named dirname subdirs':
            self.assertIn('/tmp/roles/testrole/tasks/included2.yml', called_args)
            self.assertIn('/tmp/roles/testrole/tasks/tasks/included2.yml', called_args)

            c = collections.Counter(called_args)
            assert c['/tmp/roles/testrole/tasks/included2.yml'] == 1
            assert c['/tmp/roles/testrole/tasks/tasks/included2.yml'] == 2

    def test_path_dwim_root(self):
        self.assertEqual(self._loader.path_dwim('/'), '/')

    def test_path_dwim_home(self):
        self.assertEqual(self._loader.path_dwim('~'), os.path.expanduser('~'))

    def test_path_dwim_tilde_slash(self):
        self.assertEqual(self._loader.path_dwim('~/'), os.path.expanduser('~'))

    def test_get_real_file(self):
        self.assertEqual(self._loader.get_real_file(__file__), __file__)

    def test_is_file(self):
        self.assertTrue(self._loader.is_file(__file__))

    def test_is_directory_positive(self):
        self.assertTrue(self._loader.is_directory(os.path.dirname(__file__)))

    def test_get_file_contents_none_path(self):
        with pytest.raises(TypeError, match='Invalid filename'):
            self._loader.get_text_file_contents(None)

    def test_get_file_contents_non_existent_path(self):
        with pytest.raises(AnsibleFileNotFound):
            self._loader.get_text_file_contents('/non_existent_file')


class TestPathDwimRelativeDataLoader(unittest.TestCase):

    def setUp(self):
        self._loader = DataLoader()

    def test_all_slash(self):
        self.assertEqual(self._loader.path_dwim_relative('/', '/', '/'), '/')

    def test_path_endswith_role(self):
        self.assertEqual(self._loader.path_dwim_relative(path='foo/bar/tasks/', dirname='/', source='/'), '/')

    def test_path_endswith_role_main_yml(self):
        self.assertIn('main.yml', self._loader.path_dwim_relative(path='foo/bar/tasks/', dirname='/', source='main.yml'))

    def test_path_endswith_role_source_tilde(self):
        self.assertEqual(self._loader.path_dwim_relative(path='foo/bar/tasks/', dirname='/', source='~/'), os.path.expanduser('~'))


class TestPathDwimRelativeStackDataLoader(unittest.TestCase):

    def setUp(self):
        self._loader = DataLoader()

    def test_none(self):
        self.assertRaisesRegex(AnsibleFileNotFound, 'on the Ansible Controller', self._loader.path_dwim_relative_stack, None, None, None)

    def test_empty_strings(self):
        self.assertEqual(self._loader.path_dwim_relative_stack('', '', ''), os.path.abspath('./') + '/')

    def test_empty_lists(self):
        self.assertEqual(self._loader.path_dwim_relative_stack([], '', '~/'), os.path.expanduser('~'))

    def test_all_slash(self):
        self.assertEqual(self._loader.path_dwim_relative_stack('/', '/', '/'), '/')

    def test_path_endswith_role(self):
        self.assertEqual(self._loader.path_dwim_relative_stack(paths=['foo/bar/tasks/'], dirname='/', source='/'), '/')

    def test_path_endswith_role_source_tilde(self):
        self.assertEqual(self._loader.path_dwim_relative_stack(paths=['foo/bar/tasks/'], dirname='/', source='~/'), os.path.expanduser('~'))

    def test_path_endswith_role_source_main_yml(self):
        self.assertRaises(AnsibleFileNotFound, self._loader.path_dwim_relative_stack, ['foo/bar/tasks/'], '/', 'main.yml')

    def test_path_endswith_role_source_main_yml_source_in_dirname(self):
        self.assertRaises(AnsibleFileNotFound, self._loader.path_dwim_relative_stack, 'foo/bar/tasks/', 'tasks', 'tasks/main.yml')


class TestDataLoaderWithVault(unittest.TestCase):

    def setUp(self):
        self._loader = DataLoader()
        vault_secrets = [('default', TextVaultSecret('ansible'))]
        self._loader.set_vault_secrets(vault_secrets)
        self.test_vault_data_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'vault.yml')

    def tearDown(self):
        pass

    def test_get_text_file_contents_vaulted_yaml(self) -> None:
        content = self._loader.get_text_file_contents(self.test_vault_data_path)

        assert SourceWasEncrypted.is_tagged_on(content)

    def test_get_text_file_contents_non_vaulted_file(self) -> None:
        content = self._loader.get_text_file_contents(__file__)

        assert not SourceWasEncrypted.is_tagged_on(content)

    def test_get_real_file_vault(self):
        real_file_path = self._loader.get_real_file(self.test_vault_data_path)
        self.assertTrue(os.path.exists(real_file_path))

    def test_get_real_file_vault_no_vault(self):
        self._loader.set_vault_secrets(None)
        self.assertRaises(AnsibleParserError, self._loader.get_real_file, self.test_vault_data_path)

    def test_get_real_file_vault_wrong_password(self):
        wrong_vault = [('default', TextVaultSecret('wrong_password'))]
        self._loader.set_vault_secrets(wrong_vault)
        self.assertRaises(AnsibleVaultError, self._loader.get_real_file, self.test_vault_data_path)

    def test_parse_from_vault_1_1_file(self):
        vaulted_data = """$ANSIBLE_VAULT;1.1;AES256
33343734386261666161626433386662623039356366656637303939306563376130623138626165
6436333766346533353463636566313332623130383662340a393835656134633665333861393331
37666233346464636263636530626332623035633135363732623332313534306438393366323966
3135306561356164310a343937653834643433343734653137383339323330626437313562306630
3035
"""

        with tempfile.NamedTemporaryFile(mode='w') as file:
            file.write(vaulted_data)
            file.flush()
            output = self._loader.load_from_file(file.name, cache='none')
            self.assertEqual(output, dict(foo='bar'))

            # no cache used
            self.assertFalse(self._loader._FILE_CACHE)

            # vault cache entry written
            output = self._loader.load_from_file(file.name, cache='vaulted')
            self.assertEqual(output, dict(foo='bar'))
            self.assertTrue(self._loader._FILE_CACHE)

            # cache entry used
            key = next(iter(self._loader._FILE_CACHE.keys()))
            modified = {'changed': True}
            self._loader._FILE_CACHE[key] = modified
            output = self._loader.load_from_file(file.name, cache='vaulted')
            self.assertEqual(output, modified)


def test_get_text_file_contents(tmp_path: pathlib.Path) -> None:
    original_contents = 'Hello World'

    temp_file = tmp_path / 'valid.txt'
    temp_file.write_text(original_contents)

    loader = DataLoader()
    read_contents = loader.get_text_file_contents(str(temp_file))

    assert read_contents == original_contents

    origin = Origin.get_tag(read_contents)

    assert origin.path == str(temp_file)
    assert origin.line_num is None
    assert origin.col_num is None
    assert origin.description is None


@pytest.mark.parametrize("content,encoding", (
    (b'\xa4\xa4\xb0\xea\xa4H', 'utf-8'),
    (b'\xa4\xa4\xb0\xea\xa4H', None),
))
def test_get_text_file_contents_encoding_deprecation(content: bytes, encoding: str | None, tmp_path: pathlib.Path) -> None:
    temp = tmp_path / 'bogus_file'
    temp.write_bytes(content)

    loader = DataLoader()

    if encoding:
        # help text will imply that encoding is settable if non-empty
        expected_warning_pattern = f"could not be decoded as {encoding!r}.*Ensure the correct encoding was specified"
    else:
        expected_warning_pattern = "could not be decoded as 'utf-8'.*must be UTF-8 encoded"

    with emits_warnings(deprecation_pattern=expected_warning_pattern):
        loaded = loader.get_text_file_contents(str(temp), encoding=encoding)

    assert loaded == content.decode(encoding or 'utf-8', errors='surrogateescape')

    assert Origin.is_tagged_on(loaded)
    assert not SourceWasEncrypted.is_tagged_on(loaded)
    assert not TrustedAsTemplate.is_tagged_on(loaded)


@pytest.mark.parametrize("encoding", (
    None,
    'utf-8',
    'big5',
))
def test_get_text_file_contents_strict(encoding: str | None) -> None:
    text_content = '中文'
    content = text_content.encode(encoding or 'utf-8')

    with tempfile.NamedTemporaryFile(mode='wb') as temp:
        temp.write(content)
        temp.flush()

        loader = DataLoader()
        loaded = loader.get_text_file_contents(temp.name, encoding=encoding)

        assert loaded == text_content

        assert Origin.is_tagged_on(loaded)
        assert not SourceWasEncrypted.is_tagged_on(loaded)
        assert not TrustedAsTemplate.is_tagged_on(loaded)
