# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import typing as t

import pytest

from ansible.module_utils.testing import patch_module_args

from ..mock.module import module_env_mocker  # expose shared fixture in this part of the unit test tree

assert module_env_mocker is not None  # avoid unused imports


@pytest.fixture
def set_module_args() -> t.Iterator[t.Callable[[dict[str, t.Any] | None], None]]:
    ctx: t.ContextManager | None = None

    def set_module_args(args: dict[str, t.Any] | None = None) -> None:
        nonlocal ctx

        args['_ansible_remote_tmp'] = '/tmp'
        args['_ansible_keep_remote_files'] = False

        ctx = t.cast(t.ContextManager, patch_module_args(args))
        ctx.__enter__()

    try:
        yield set_module_args
    finally:
        if ctx:
            ctx.__exit__(None, None, None)
