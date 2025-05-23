# -*- coding: utf-8 -*-
# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# pylint: disable=ansible-deprecated-no-version  # arg-splatting prevents pylint from understanding how deprecate is being called

from __future__ import annotations

import typing as t

import pytest

from ansible.module_utils._internal import _traceback
from ansible.module_utils.common import warnings
from ansible.module_utils.common.warnings import deprecate
from units.mock.module import ModuleEnvMocker

pytestmark = pytest.mark.usefixtures("module_env_mocker")


def test_dedupe_with_traceback(module_env_mocker: ModuleEnvMocker) -> None:
    module_env_mocker.set_traceback_config([_traceback.TracebackEvent.DEPRECATED])
    deprecate_args: dict[str, t.Any] = dict(msg="same", version="1.2.3", collection_name="blar.blar")

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
