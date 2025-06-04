# coding: utf-8
# (c) 2015, Toshio Kuratomi <tkuratomi@ansible.com>
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

import collections.abc as c
import datetime
import typing as t

import pytest
import yaml

from collections.abc import Sequence, Set, Mapping
from io import StringIO

import unittest

from ansible import errors
from ansible.parsing.utils.yaml import from_yaml
from ansible.parsing.yaml.dumper import AnsibleDumper
from ansible.parsing.yaml.loader import AnsibleLoader
from ansible._internal._yaml._errors import AnsibleYAMLParserError
from ansible.parsing import vault
from ansible._internal._datatag._tags import Origin, TrustedAsTemplate
from ansible.module_utils._internal._datatag import _untaggable_types

from units.mock.yaml_helper import YamlTestUtils
from units.mock.vault_helper import TextVaultSecret

from yaml.parser import ParserError
from yaml.scanner import ScannerError

file_name = '/some/test/path/myfile.yml'


class TestAnsibleLoaderBasic(unittest.TestCase):

    def test_parse_number(self):
        stream = StringIO(u"""
                1
                """)
        stream.name = file_name
        data = yaml.load(stream, Loader=AnsibleLoader)
        self.assertEqual(data, 1)
        # No line/column info saved yet

    def test_parse_string(self):
        stream = StringIO(u"""
                Ansible
                """)
        stream.name = file_name
        data = yaml.load(stream, Loader=AnsibleLoader)
        self.assertEqual(data, u'Ansible')
        self.assertIsInstance(data, str)

        self.assertEqual(Origin.get_tag(data), Origin(path=file_name, line_num=2, col_num=17))

    def test_parse_utf8_string(self):
        stream = StringIO(u"""
                Cafè Eñyei
                """)
        stream.name = file_name
        data = yaml.load(stream, Loader=AnsibleLoader)
        self.assertEqual(data, u'Cafè Eñyei')
        self.assertIsInstance(data, str)

        self.assertEqual(Origin.get_tag(data), Origin(path=file_name, line_num=2, col_num=17))

    def test_parse_dict(self):
        stream = StringIO(u"""
                webster: daniel
                oed: oxford
                """)
        stream.name = file_name
        data = yaml.load(stream, Loader=AnsibleLoader)
        self.assertEqual(data, {'webster': 'daniel', 'oed': 'oxford'})
        self.assertEqual(len(data), 2)
        self.assertIsInstance(list(data.keys())[0], str)
        self.assertIsInstance(list(data.values())[0], str)

        # Beginning of the first key
        self.assertEqual(Origin.get_tag(data), Origin(path=file_name, line_num=2, col_num=17))

        self.assertEqual(Origin.get_tag(data[u'webster']), Origin(path=file_name, line_num=2, col_num=26))
        self.assertEqual(Origin.get_tag(data[u'oed']), Origin(path=file_name, line_num=3, col_num=22))

    def test_parse_list(self):
        stream = StringIO(u"""
                - a
                - b
                """)
        stream.name = file_name
        data = yaml.load(stream, Loader=AnsibleLoader)
        self.assertEqual(data, [u'a', u'b'])
        self.assertEqual(len(data), 2)
        self.assertIsInstance(data[0], str)

        self.assertEqual(Origin.get_tag(data), Origin(path=file_name, line_num=2, col_num=17))

        self.assertEqual(Origin.get_tag(data[0]), Origin(path=file_name, line_num=2, col_num=19))
        self.assertEqual(Origin.get_tag(data[1]), Origin(path=file_name, line_num=3, col_num=19))

    def test_parse_short_dict(self):
        stream = StringIO(u"""{"foo": "bar"}""")
        stream.name = file_name
        data = yaml.load(stream, Loader=AnsibleLoader)
        self.assertEqual(data, dict(foo=u'bar'))

        self.assertEqual(Origin.get_tag(data), Origin(path=file_name, line_num=1, col_num=1))
        self.assertEqual(Origin.get_tag(data[u'foo']), Origin(path=file_name, line_num=1, col_num=9))

        stream = StringIO(u"""foo: bar""")
        stream.name = file_name
        data = yaml.load(stream, Loader=AnsibleLoader)
        self.assertEqual(data, dict(foo=u'bar'))

        self.assertEqual(Origin.get_tag(data), Origin(path=file_name, line_num=1, col_num=1))
        self.assertEqual(Origin.get_tag(data[u'foo']), Origin(path=file_name, line_num=1, col_num=6))

    def test_error_conditions(self):
        stream = StringIO(u"""{""")
        stream.name = file_name
        with self.assertRaises(ParserError):
            yaml.load(stream, Loader=AnsibleLoader)

    def test_tab_error(self):
        stream = StringIO(u"""---\nhosts: localhost\nvars:\n  foo: bar\n\tblip: baz""")
        stream.name = file_name
        with self.assertRaises(ScannerError):
            yaml.load(stream, Loader=AnsibleLoader)

    def test_front_matter(self):
        stream = StringIO(u"""---\nfoo: bar""")
        stream.name = file_name
        data = yaml.load(stream, Loader=AnsibleLoader)
        self.assertEqual(data, dict(foo=u'bar'))

        self.assertEqual(Origin.get_tag(data), Origin(path=file_name, line_num=2, col_num=1))
        self.assertEqual(Origin.get_tag(data[u'foo']), Origin(path=file_name, line_num=2, col_num=6))

        # Initial indent (See: #6348)
        stream = StringIO(u""" - foo: bar\n   baz: qux""")
        stream.name = file_name
        data = yaml.load(stream, Loader=AnsibleLoader)
        self.assertEqual(data, [{u'foo': u'bar', u'baz': u'qux'}])

        self.assertEqual(Origin.get_tag(data), Origin(path=file_name, line_num=1, col_num=2))
        self.assertEqual(Origin.get_tag(data[0]), Origin(path=file_name, line_num=1, col_num=4))
        self.assertEqual(Origin.get_tag(data[0][u'foo']), Origin(path=file_name, line_num=1, col_num=9))
        self.assertEqual(Origin.get_tag(data[0][u'baz']), Origin(path=file_name, line_num=2, col_num=9))


class TestAnsibleLoaderVault(unittest.TestCase, YamlTestUtils):
    def setUp(self):
        self.vault_password = "hunter42"
        vault_secret = TextVaultSecret(self.vault_password)
        self.vault_secrets = [('vault_secret', vault_secret),
                              ('default', vault_secret)]
        self.vault = vault.VaultLib(self.vault_secrets)

    @property
    def vault_secret(self):
        return vault.match_encrypt_secret(self.vault_secrets)[1]

    def test_wrong_password(self):
        plaintext = u"Ansible"
        bob_password = "this is a different password"

        bobs_secret = TextVaultSecret(bob_password)
        bobs_secrets = [('default', bobs_secret)]

        bobs_vault = vault.VaultLib(bobs_secrets)

        ciphertext = bobs_vault.encrypt(plaintext, vault.match_encrypt_secret(bobs_secrets)[1])

        try:
            self.vault.decrypt(ciphertext)
        except Exception as e:
            self.assertIsInstance(e, errors.AnsibleError)
            self.assertEqual(e.message, 'Decryption failed (no vault secrets were found that could decrypt).')

    def _encrypt_plaintext(self, plaintext):
        # Construct a yaml repr of a vault by hand
        vaulted_var_bytes = self.vault.encrypt(plaintext, self.vault_secret)

        # add yaml tag
        vaulted_var = vaulted_var_bytes.decode()
        lines = vaulted_var.splitlines()
        lines2 = []
        for line in lines:
            lines2.append('        %s' % line)

        vaulted_var = '\n'.join(lines2)
        tagged_vaulted_var = u"""!vault |\n%s""" % vaulted_var
        return tagged_vaulted_var

    def _build_stream(self, yaml_text):
        stream = StringIO(yaml_text)
        stream.name = 'my.yml'
        return stream

    def _load_yaml(self, yaml_text, password):
        stream = self._build_stream(yaml_text)
        data = yaml.load(stream, Loader=AnsibleLoader)

        return data


class TestAnsibleLoaderPlay(unittest.TestCase):

    def setUp(self):
        stream = StringIO("""
                - hosts: localhost
                  vars:
                    number: 1
                    string: Ansible
                    utf8_string: Cafè Eñyei
                    dictionary:
                      webster: daniel
                      oed: oxford
                    list:
                      - a
                      - b
                      - 1
                      - 2
                  tasks:
                    - name: Test case
                      ping:
                        data: "{{ utf8_string }}"

                    - name: Test 2
                      ping:
                        data: "Cafè Eñyei"

                    - name: Test 3
                      command: "printf 'Cafè Eñyei\\n'"
                      vars:
                        not_safe: !unsafe "{{ sorry }}"
                        also_not_safe: !unsafe ["{{ sorry }}"]
                """)
        self.play_filename = '/path/to/myplay.yml'
        stream.name = self.play_filename
        self.data = yaml.load(stream, Loader=AnsibleLoader)

    def tearDown(self):
        pass

    def test_data_complete(self):
        self.assertEqual(len(self.data), 1)
        self.assertIsInstance(self.data, list)
        self.assertEqual(frozenset(self.data[0].keys()), frozenset((u'hosts', u'vars', u'tasks')))

        self.assertEqual(self.data[0][u'hosts'], u'localhost')

        self.assertEqual(self.data[0][u'vars'][u'number'], 1)
        self.assertEqual(self.data[0][u'vars'][u'string'], u'Ansible')
        self.assertEqual(self.data[0][u'vars'][u'utf8_string'], u'Cafè Eñyei')
        self.assertEqual(self.data[0][u'vars'][u'dictionary'], {
            u'webster': u'daniel',
            u'oed': u'oxford'
        })
        self.assertEqual(self.data[0][u'vars'][u'list'], [u'a', u'b', 1, 2])

        self.assertEqual(self.data[0][u'tasks'], [
            {u'name': u'Test case', u'ping': {u'data': u'{{ utf8_string }}'}},
            {u'name': u'Test 2', u'ping': {u'data': u'Cafè Eñyei'}},
            {u'name': u'Test 3', u'command': u'printf \'Cafè Eñyei\n\'', 'vars': {'not_safe': "{{ sorry }}", 'also_not_safe': ["{{ sorry }}"]}},
        ])

    def walk(self, data):
        # Make sure there's no str in the data
        self.assertNotIsInstance(data, bytes)

        # Descend into various container types
        if isinstance(data, str):
            # strings are a sequence so we have to be explicit here
            return
        elif isinstance(data, (Sequence, Set)):
            for element in data:
                self.walk(element)
        elif isinstance(data, Mapping):
            for k, v in data.items():
                self.walk(k)
                self.walk(v)

        # Scalars were all checked so we're good to go
        return

    def test_no_str_in_data(self):
        # Checks that no strings are str type
        self.walk(self.data)

    def check_vars(self):
        self.assertEqual(Origin.get_tag(self.data[0][u'vars'][u'number']), Origin(path=self.play_filename, line_num=4, col_num=29))

        self.assertEqual(Origin.get_tag(self.data[0][u'vars'][u'string']), Origin(path=self.play_filename, line_num=5, col_num=29))
        self.assertEqual(Origin.get_tag(self.data[0][u'vars'][u'utf8_string']), Origin(path=self.play_filename, line_num=6, col_num=34))

        self.assertEqual(Origin.get_tag(self.data[0][u'vars'][u'dictionary']), Origin(path=self.play_filename, line_num=8, col_num=23))
        self.assertEqual(Origin.get_tag(self.data[0][u'vars'][u'dictionary'][u'webster']),
                         Origin(path=self.play_filename, line_num=8, col_num=32))
        self.assertEqual(Origin.get_tag(self.data[0][u'vars'][u'dictionary'][u'oed']),
                         Origin(path=self.play_filename, line_num=9, col_num=28))

        self.assertEqual(Origin.get_tag(self.data[0][u'vars'][u'list']), Origin(path=self.play_filename, line_num=11, col_num=23))
        self.assertEqual(Origin.get_tag(self.data[0][u'vars'][u'list'][0]), Origin(path=self.play_filename, line_num=11, col_num=25))
        self.assertEqual(Origin.get_tag(self.data[0][u'vars'][u'list'][1]), Origin(path=self.play_filename, line_num=12, col_num=25))
        self.assertEqual(Origin.get_tag(self.data[0][u'vars'][u'list'][2]), Origin(path=self.play_filename, line_num=13, col_num=25))
        self.assertEqual(Origin.get_tag(self.data[0][u'vars'][u'list'][3]), Origin(path=self.play_filename, line_num=14, col_num=25))

    def check_tasks(self):
        #
        # First Task
        #
        self.assertEqual(Origin.get_tag(self.data[0][u'tasks'][0]), Origin(path=self.play_filename, line_num=16, col_num=23))
        self.assertEqual(Origin.get_tag(self.data[0][u'tasks'][0][u'name']), Origin(path=self.play_filename, line_num=16, col_num=29))
        self.assertEqual(Origin.get_tag(self.data[0][u'tasks'][0][u'ping']), Origin(path=self.play_filename, line_num=18, col_num=25))
        self.assertEqual(Origin.get_tag(self.data[0][u'tasks'][0][u'ping'][u'data']),
                         Origin(path=self.play_filename, line_num=18, col_num=31))

        #
        # Second Task
        #
        self.assertEqual(Origin.get_tag(self.data[0][u'tasks'][1]), Origin(path=self.play_filename, line_num=20, col_num=23))
        self.assertEqual(Origin.get_tag(self.data[0][u'tasks'][1][u'name']), Origin(path=self.play_filename, line_num=20, col_num=29))
        self.assertEqual(Origin.get_tag(self.data[0][u'tasks'][1][u'ping']), Origin(path=self.play_filename, line_num=22, col_num=25))
        self.assertEqual(Origin.get_tag(self.data[0][u'tasks'][1][u'ping'][u'data']),
                         Origin(path=self.play_filename, line_num=22, col_num=31))

        #
        # Third Task
        #
        self.assertEqual(Origin.get_tag(self.data[0][u'tasks'][2]), Origin(path=self.play_filename, line_num=24, col_num=23))
        self.assertEqual(Origin.get_tag(self.data[0][u'tasks'][2][u'name']), Origin(path=self.play_filename, line_num=24, col_num=29))
        self.assertEqual(Origin.get_tag(self.data[0][u'tasks'][2][u'command']), Origin(path=self.play_filename, line_num=25, col_num=32))

        not_safe = self.data[0][u'tasks'][2][u'vars']['not_safe']
        also_not_safe = self.data[0][u'tasks'][2][u'vars']['also_not_safe']

        assert Origin.get_tag(not_safe) == Origin(path=self.play_filename, line_num=27, col_num=35)
        assert Origin.get_tag(also_not_safe) == Origin(path=self.play_filename, line_num=28, col_num=40)
        assert Origin.get_tag(also_not_safe) == Origin(path=self.play_filename, line_num=28, col_num=40)

        assert not TrustedAsTemplate.is_tagged_on(not_safe)
        assert not TrustedAsTemplate.is_tagged_on(also_not_safe)
        assert not TrustedAsTemplate.is_tagged_on(also_not_safe[0])

    def test_line_numbers(self):
        # Check the line/column numbers are correct
        # Note: Remember, currently dicts begin at the start of their first entry
        self.assertEqual(Origin.get_tag(self.data[0]), Origin(path=self.play_filename, line_num=2, col_num=19))
        self.assertEqual(Origin.get_tag(self.data[0][u'hosts']), Origin(path=self.play_filename, line_num=2, col_num=26))
        self.assertEqual(Origin.get_tag(self.data[0][u'vars']), Origin(path=self.play_filename, line_num=4, col_num=21))

        self.check_vars()

        self.assertEqual(Origin.get_tag(self.data[0][u'tasks']), Origin(path=self.play_filename, line_num=16, col_num=21))

        self.check_tasks()


@pytest.mark.parametrize("value", (
    "[1]",
    "{a: 1}",
    "1",
    "1.1",
    "true",
    "",
    "~",
))
def test_vault_tag_type_validation(value: str) -> None:
    with pytest.raises(AnsibleYAMLParserError) as error:
        from_yaml(f"!vault {value}")

    assert "requires a string value" in str(error.value)


class CustomMapping(c.Mapping):
    def __init__(self, data: dict) -> None:
        self._data = data

    def __getitem__(self, __key):
        return self._data[__key]

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __repr__(self):
        return f'{type(self).__name__}({self._data!r})'


YAML_STRINGS_AND_VALUES = (
    ("test", "test"),
    ("123", 123),
    ("1.234", 1.234),
    ("true", True),
    ("false", False),
    ("{foo: bar}", dict(foo="bar")),
    ("[1, 2, 3]", [1, 2, 3]),
    ("!!set {bar: null, foo: null}", {"foo", "bar"}),
    ("2024-01-01", datetime.date(2024, 1, 1)),
    ("2024-01-01 12:01:01", datetime.datetime(2024, 1, 1, 12, 1, 1)),
    ("null", None),
    ("!!binary |\n  aGVsbG8=", b'hello'),
)
"""These values can be round-tripped through YAML."""

YAML_STRINGS_FROM_VALUES = (
    ("{a: 1}", CustomMapping(dict(a=1))),
)
"""These values can be dumped to YAML, but are converted to another type in the process, so they can't be loaded as the original type that was dumped."""


@pytest.mark.parametrize("value, expected", YAML_STRINGS_AND_VALUES)
def test_load_data_types(value: str, expected: t.Any) -> None:
    """Verify supported data types can be YAML loaded."""
    value = Origin(path=file_name).tag(value)
    result = from_yaml(value)
    origin = Origin.get_tag(result)

    assert result == expected

    if type(result) in _untaggable_types:
        assert origin is None
    else:
        assert origin.path == file_name


@pytest.mark.parametrize("expected, value", YAML_STRINGS_AND_VALUES + YAML_STRINGS_FROM_VALUES)
def test_dump_data_types(value: str, expected: t.Any) -> None:
    """Verify supported data types can be YAML dumped."""
    result = yaml.dump(value, Dumper=AnsibleDumper, default_flow_style=True).rstrip()

    assert result == expected


@pytest.mark.parametrize("trust_input_str", (
    True,
    False,
))
def test_string_trust_propagation(trust_input_str: bool) -> None:
    """
    Verify that input trust propagation behaves as expected. An explicit boolean `trusted_as_template` arg to the loader is always
    respected; if not specified, the presence of trust on the input string determines if trust is applied to outputs.
    """
    data = "foo: bar"

    if trust_input_str:
        data = TrustedAsTemplate().tag(data)

    res = yaml.load(data, Loader=AnsibleLoader)  # type: ignore[arg-type]

    assert trust_input_str == TrustedAsTemplate.is_tagged_on(res['foo'])
