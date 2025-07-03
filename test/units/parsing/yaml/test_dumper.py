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

from ansible.module_utils._internal._datatag import Tripwire
from ansible.module_utils._internal._datatag._tags import Deprecated
from ansible.parsing import vault
from ansible._internal._datatag._tags import VaultedValue, TrustedAsTemplate
from ansible.parsing.yaml.loader import AnsibleLoader
from ansible.parsing.yaml.dumper import AnsibleDumper
from ansible.plugins.filter.core import to_yaml, to_nice_yaml
from ansible._internal._templating._jinja_bits import _DEFAULT_UNDEF
from ansible._internal._templating._jinja_common import MarkerError

from ...mock.custom_types import CustomMapping, CustomSequence
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
        self.dumper = AnsibleDumper

    def _build_stream(self, yaml_text=None):
        text = yaml_text or u''
        stream = io.StringIO(text)
        return stream

    def _loader(self, stream):
        return AnsibleLoader(stream)

    def test_bytes(self):
        b_text = u'tréma'.encode('utf-8')
        unsafe_object = TrustedAsTemplate().tag(b_text)
        yaml_out = self._dump_string(unsafe_object, dumper=self.dumper)

        stream = self._build_stream(yaml_out)

        data_from_yaml = yaml.load(stream, Loader=AnsibleLoader)

        result = b_text

        self.assertEqual(result, data_from_yaml)

    def test_unicode(self):
        u_text = u'nöel'
        unsafe_object = TrustedAsTemplate().tag(u_text)
        yaml_out = self._dump_string(unsafe_object, dumper=self.dumper)

        stream = self._build_stream(yaml_out)

        data_from_yaml = yaml.load(stream, Loader=AnsibleLoader)

        self.assertEqual(u_text, data_from_yaml)

    def test_undefined(self):
        with pytest.raises(MarkerError):
            self._dump_string(_DEFAULT_UNDEF, dumper=self.dumper)


@pytest.mark.parametrize("filter_impl, expected_output", [
    (to_yaml, "!vault |-\n  ciphertext\n"),
    (to_nice_yaml, "!vault |-\n    ciphertext\n"),
])
def test_vaulted_value_dump(
    filter_impl: t.Callable,
    expected_output: str,
    mocker: pytest_mock.MockerFixture
) -> None:
    """Validate that strings tagged VaultedValue are represented properly."""
    value = VaultedValue(ciphertext="ciphertext").tag("secret plaintext")

    from ansible.utils.display import Display

    _deprecated_spy = mocker.spy(Display(), 'deprecated')

    res = filter_impl(value)

    assert res == expected_output


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
