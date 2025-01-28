# coding: utf-8
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

import io
import pytest
import typing as t
import unittest

import pytest_mock
import yaml

from ansible.module_utils.datatag import Tripwire
from ansible.module_utils.datatag.tags import Deprecated
from ansible.parsing import vault
from ansible.utils.datatag.tags import VaultedValue, TrustedAsTemplate
from ansible.parsing.yaml import dumper
from ansible.parsing.yaml.loader import AnsibleLoader
from ansible.parsing.yaml.dumper import AnsibleDumper
from ansible.plugins.filter.core import to_yaml, to_nice_yaml
from ansible._internal._templating._jinja_bits import _DEFAULT_UNDEF
from ansible._internal._templating._jinja_common import MarkerError

from ...mock.custom_collections import CustomMapping, CustomSequence
from units.mock.yaml_helper import YamlTestUtils
from units.mock.vault_helper import TextVaultSecret


class TestAnsibleDumper(unittest.TestCase, YamlTestUtils):
    def setUp(self):
        self.vault_password = "hunter42"
        vault_secret = TextVaultSecret(self.vault_password)
        self.vault_secrets = [('vault_secret', vault_secret)]
        self.good_vault = vault.VaultLib(self.vault_secrets)
        self.vault = self.good_vault
        self.stream = self._build_stream()
        self.dumper = dumper.AnsibleDumper

    def _build_stream(self, yaml_text=None):
        text = yaml_text or u''
        stream = io.StringIO(text)
        return stream

    def _loader(self, stream):
        return AnsibleLoader(stream, vault_secrets=self.vault.secrets)

    def test_bytes(self):
        b_text = u'tréma'.encode('utf-8')
        unsafe_object = TrustedAsTemplate().tag(b_text)
        yaml_out = self._dump_string(unsafe_object, dumper=self.dumper)

        stream = self._build_stream(yaml_out)
        loader = self._loader(stream)

        data_from_yaml = loader.get_single_data()

        result = b_text

        self.assertEqual(result, data_from_yaml)

    def test_unicode(self):
        u_text = u'nöel'
        unsafe_object = TrustedAsTemplate().tag(u_text)
        yaml_out = self._dump_string(unsafe_object, dumper=self.dumper)

        stream = self._build_stream(yaml_out)
        loader = self._loader(stream)

        data_from_yaml = loader.get_single_data()

        self.assertEqual(u_text, data_from_yaml)

    def test_undefined(self):
        with pytest.raises(MarkerError):
            self._dump_string(_DEFAULT_UNDEF, dumper=self.dumper)


@pytest.mark.parametrize("filter_impl, dump_vault_tags, expected_output, expected_warning", [
    (to_yaml, True, "!vault |-\n  ciphertext\n", None),
    (to_yaml, None, "!vault |-\n  ciphertext\n", "Implicit YAML dumping"),
    (to_yaml, False, "secret plaintext\n", None),
    (to_nice_yaml, True, "!vault |-\n    ciphertext\n", None),
    (to_nice_yaml, None, "!vault |-\n    ciphertext\n", "Implicit YAML dumping"),
    (to_nice_yaml, False, "secret plaintext\n", None),
])
def test_vaulted_value_dump(
        filter_impl: t.Callable,
        dump_vault_tags: bool | None,
        expected_output: str,
        expected_warning: str | None,
        mocker: pytest_mock.MockerFixture
) -> None:
    """Validate that strings tagged VaultedValue are represented properly."""
    value = VaultedValue(ciphertext="ciphertext").tag("secret plaintext")

    from ansible.utils.display import Display

    _deprecated_spy = mocker.spy(Display(), 'deprecated')

    res = filter_impl(value, dump_vault_tags=dump_vault_tags)

    assert res == expected_output

    # deprecated: description='enable the assertion for the deprecation warning below' core_version='2.21'
    # if expected_warning:
    #     assert _deprecated_spy.call_count == 1
    #     assert expected_warning in _deprecated_spy.call_args.kwargs['msg']


_test_tag = Deprecated(msg="test")


@pytest.mark.parametrize("value, expected", (
    (CustomMapping(dict(a=1)), "a: 1"),
    (CustomSequence([1]), "- 1"),
    (_test_tag.tag(dict(a=1)), "a: 1"),
    (_test_tag.tag([1]), "- 1"),
    (_test_tag.tag(1), "1"),
    (_test_tag.tag("Ansible"), "Ansible"),
))
def test_dump(value: t.Any, expected: str) -> None:
    """Verify supported types can be dumped."""
    result = yaml.dump(value, Dumper=AnsibleDumper).strip()

    assert result == expected


def test_dump_tripwire() -> None:
    """Verify dumping a tripwire trips it."""
    class Tripped(Exception):
        pass

    class CustomTripwire(Tripwire):
        def trip(self) -> t.NoReturn:
            raise Tripped()

    with pytest.raises(Tripped):
        yaml.dump(CustomTripwire(), Dumper=AnsibleDumper)
