from __future__ import annotations

import collections
import dataclasses
import math
import pathlib
import tempfile
import typing as t

import pytest

from ansible.parsing.vault import EncryptedString
from ansible.plugins.loader import test_loader
from ansible.plugins.test import AnsibleJinja2Test
from ansible.template import Templar, trust_as_template
from units.test_utils.controller.display import emits_warnings


@dataclasses.dataclass
class Extra:
    variables: dict[str, t.Any] | None = None
    args: list[t.Any] | None = None
    kwargs: dict[str, t.Any] | None = None
    func: t.Callable[[Extra], None] | None = None


class MakeLink:
    _tempdir: tempfile.TemporaryDirectory[str] | None = None

    def __call__(self, *args, **kwargs) -> str:
        self._tempdir = tempfile.TemporaryDirectory()

        symlink = pathlib.Path(self._tempdir.name) / 'a_symlink'
        symlink.symlink_to('something')

        return str(symlink)

    def __del__(self) -> None:
        if self._tempdir:
            self._tempdir.cleanup()

    def __repr__(self) -> str:
        return 'MakeLink'


TEST_DATA_SET: tuple[tuple[t.Any, str, bool, Extra | None], ...] = (
    # core
    (dict(failed=1), 'failed', True, None),
    (dict(failed=0), 'failed', False, None),
    (dict(), 'failed', False, None),
    (dict(failed=1), 'success', False, None),
    (dict(failed=0), 'success', True, None),
    (dict(), 'success', True, None),
    (dict(unreachable=1), 'reachable', False, None),
    (dict(unreachable=0), 'reachable', True, None),
    (dict(), 'reachable', True, None),
    (dict(unreachable=0), 'unreachable', False, None),
    (dict(unreachable=1), 'unreachable', True, None),
    (dict(), 'unreachable', False, None),
    (dict(timedout=dict(period=99)), 'timedout', True, None),
    # (dict(timedout=1), 'timedout', False, None),  # oops, bug
    (dict(timedout=0), 'timedout', False, None),
    (dict(), 'timedout', False, None),
    (dict(changed=1), 'changed', True, None),
    (dict(changed=0), 'changed', False, None),
    (dict(), 'changed', False, None),
    # (dict(results=[]), 'changed', True, None), # oops, bug
    (dict(results=[dict(changed=1)]), 'changed', True, None),
    (dict(results=[dict(changed=0)]), 'changed', False, None),
    (dict(), 'changed', False, None),
    (dict(skipped=1), 'skipped', True, None),
    (dict(skipped=0), 'skipped', False, None),
    (dict(), 'skipped', False, None),
    (dict(finished=1), 'finished', True, None),
    (dict(finished=0), 'finished', False, None),
    (dict(), 'finished', True, None),
    (dict(started=1), 'started', True, None),
    (dict(started=0), 'started', False, None),
    (dict(), 'started', True, None),
    ('"foo"', 'match', True, Extra(args=['"foo"'])),
    ('"foo"', 'match', False, Extra(args=['"bar"'])),
    ('"xxfooxx"', 'search', True, Extra(args=['"foo"'])),
    ('"xxfooxx"', 'search', False, Extra(args=['"bar"'])),
    ('"fooxx"', 'regex', True, Extra(args=['"FOO"'], kwargs=dict(ignorecase=True, multiline=True, match_type='"match"'))),
    ('"fooxx"', 'regex', False, Extra(args=['"BAR"'], kwargs=dict(ignorecase=True, multiline=True, match_type='"match"'))),
    ('1.1', 'version_compare', True, Extra(args=['1.1', '"eq"'])),
    ('1.1', 'version_compare', False, Extra(args=['1.0', '"eq"'])),
    ([0], 'any', False, None),
    ([1], 'any', True, None),
    ([0], 'all', False, None),
    ([1], 'all', True, None),
    (1, 'truthy', True, None),
    (0, 'truthy', False, None),
    (1, 'falsy', False, None),
    (0, 'falsy', True, None),
    ('foo', 'vault_encrypted', True, Extra(variables=dict(foo=EncryptedString(ciphertext='$ANSIBLE_VAULT;1.1;BLAH')))),
    ('foo', 'vault_encrypted', False, Extra(variables=dict(foo='not_encrypted'))),
    (repr(str(pathlib.Path(__file__).parent / "dummy_vault.txt")), 'vaulted_file', True, None),
    (repr(__file__), 'vaulted_file', False, None),
    ('q', 'defined', True, None),
    ('not_defined', 'defined', False, None),
    ('q', 'undefined', False, None),
    ('not_defined', 'undefined', True, None),
    # files
    ('"/"', 'directory', True, None),
    (repr(__file__), 'directory', False, None),
    (repr(__file__), 'file', True, None),
    ('"/"', 'file', False, None),
    ('make_link()', 'link', True, Extra(variables=dict(make_link=MakeLink()))),
    ('"/"', 'link', False, None),
    ('"/"', 'exists', True, None),
    ('"/does_not_exist"', 'exists', False, None),
    ('"/"', 'link_exists', True, None),
    ('"/does_not_exist"', 'link_exists', False, None),
    ('"/absolute"', 'abs', True, None),
    ('"relative"', 'abs', False, None),
    ('"/"', 'same_file', True, Extra(args=['"/"'])),
    (repr(__file__), 'same_file', False, Extra(args=['"/"'])),
    ('"/"', 'mount', True, None),
    ('"/not_a_mount_point"', 'mount', False, None),
    # mathstuff
    ([1], 'subset', True, Extra(args=[[1]])),
    ([0], 'subset', False, Extra(args=[[1]])),
    ([1], 'superset', True, Extra(args=[[1]])),
    ([0], 'superset', False, Extra(args=[[1]])),
    ([0], 'contains', True, Extra(args=[0])),
    ([1], 'contains', False, Extra(args=[0])),
    ('nan', 'nan', True, Extra(variables=dict(nan=math.nan))),
    ('"a string"', 'nan', False, None),
    # uri
    ('"https://ansible.com/"', 'uri', True, None),
    (1, 'uri', False, None),
    ('"https://ansible.com/"', 'url', True, None),
    (1, 'url', False, None),
    ('"urn:https://ansible.com/"', 'urn', True, None),
    (1, 'urn', False, None),
)


@pytest.mark.parametrize("value,test,expected,extra", TEST_DATA_SET, ids=str)
def test_truthy_inputs(value: object, test: str, expected: bool, extra: Extra | None) -> None:
    """Ensure test plugins return the expected bool result, not just a truthy/falsey value."""
    test_invocation = test

    if extra:
        test_args = extra.args or []
        test_args.extend(f'{k}={v}' for k, v in (extra.kwargs or {}).items())
        test_invocation += '(' + ', '.join(str(arg) for arg in test_args) + ')'

    expression = f'{value} is {test_invocation}'

    with emits_warnings(deprecation_pattern=[]):
        result = Templar(variables=extra.variables if extra else None).evaluate_expression(trust_as_template(expression))

    assert result is expected


def test_ensure_all_plugins_tested() -> None:
    """Ensure all plugins have at least one entry in the test data set, accounting for functions which have multiple names."""
    test_plugins: list[AnsibleJinja2Test] = [plugin for plugin in test_loader.all() if plugin.ansible_name.startswith('ansible.builtin.')]
    plugin_aliases: dict[t.Any, set[str]] = collections.defaultdict(set)

    for test_plugin in test_plugins:
        plugin_aliases[test_plugin.j2_function].add(test_plugin.ansible_name)

    missing_entries: list[str] = []

    for plugin_names in plugin_aliases.values():
        matching_tests = {_expected for _value, test, _expected, _extra in TEST_DATA_SET if f'ansible.builtin.{test}' in plugin_names}
        missing = {True, False} - matching_tests

        if missing:  # pragma: nocover
            missing_entries.append(f'{plugin_names}: {missing}')

    assert not missing_entries
