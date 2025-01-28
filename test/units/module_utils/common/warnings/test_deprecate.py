# -*- coding: utf-8 -*-
# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# pylint: disable=ansible-deprecated-no-version  # arg-splatting prevents pylint from understanding how deprecate is being called

from __future__ import annotations

import pytest
import typing as t

from ansible.module_utils._internal import _traceback
from ansible.module_utils.common import warnings
from ansible.module_utils.common.messages import Detail, DeprecationSummary
from ansible.module_utils.common.warnings import deprecate
from units.mock.module import ModuleEnvMocker

pytestmark = pytest.mark.usefixtures("module_env_mocker")


@pytest.mark.parametrize("deprecate_kwargs", (
    dict(msg='Deprecation message'),
    dict(msg='Deprecation message', collection_name='ansible.builtin'),
    dict(msg='Deprecation message', version='2.14'),
    dict(msg='Deprecation message', version='2.14', collection_name='ansible.builtin'),
    dict(msg='Deprecation message', date='2199-12-31'),
    dict(msg='Deprecation message', date='2199-12-31', collection_name='ansible.builtin'),
))
def test_deprecate(deprecate_kwargs: dict[str, t.Any]):
    deprecate(**deprecate_kwargs)
    assert warnings.get_deprecation_messages() == (deprecate_kwargs,)
    assert warnings.get_deprecations() == [DeprecationSummary._from_details(Detail(msg=deprecate_kwargs.pop('msg')), **deprecate_kwargs)]


def test_multiple_deprecations():
    messages = [
        {'msg': 'First deprecation', 'version': None, 'collection_name': None},
        {'msg': 'Second deprecation', 'version': None, 'collection_name': 'ansible.builtin'},
        {'msg': 'Third deprecation', 'version': '2.14', 'collection_name': None},
        {'msg': 'Fourth deprecation', 'version': '2.9', 'collection_name': None},
        {'msg': 'Fifth deprecation', 'version': '2.9', 'collection_name': 'ansible.builtin'},
        {'msg': 'Sixth deprecation', 'date': '2199-12-31', 'collection_name': None},
        {'msg': 'Seventh deprecation', 'date': '2199-12-31', 'collection_name': 'ansible.builtin'},
    ]
    for d in messages:
        deprecate(**d)

    expected_deprecations = [DeprecationSummary._from_details(Detail(msg=d.pop('msg')), **d) for d in messages]

    assert warnings.get_deprecation_messages() == tuple(expected_deprecation._as_simple_dict() for expected_deprecation in expected_deprecations)
    assert warnings.get_deprecations() == expected_deprecations


def test_dedupe_with_traceback(module_env_mocker: ModuleEnvMocker) -> None:
    module_env_mocker.set_traceback_config([_traceback.TracebackEvent.DEPRECATED])
    deprecate_args = dict(msg="same", version="1.2.3", collection_name="blar.blar")

    # DeprecationMessageDetail dataclass object hash is the dedupe key; presence of differing tracebacks or SourceContexts affects de-dupe

    for _i in range(0, 10):
        # same location, same traceback- should be collapsed to one message
        deprecate(**deprecate_args)

    assert len(warnings.get_deprecation_messages()) == 1
    assert len(warnings.get_deprecations()) == 1

    for _i in range(0, 10):
        deprecate(**deprecate_args)  # with tracebacks on, we should have a different source location than the first loop, but still de-dupe

    assert len(warnings.get_deprecation_messages()) == 2
    assert len(warnings.get_deprecations()) == 2


@pytest.mark.parametrize(
    'test_case',
    (
        1,
        True,
        [1],
        {'k1': 'v1'},
        (1, 2),
        6.62607004,
        b'bytestr',
        None,
    )
)
def test_deprecate_failure(test_case):
    with pytest.raises(TypeError, match=f"must be <class 'str'> instead of {type(test_case)}"):
        deprecate(test_case)  # pylint: disable=ansible-deprecated-no-version
