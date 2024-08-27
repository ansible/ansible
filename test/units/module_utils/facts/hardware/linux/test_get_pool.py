# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import multiprocessing

from multiprocessing.pool import ThreadPool
from unittest import mock

from ansible.module_utils.facts.hardware.linux import _get_thread_pool


def test_get_pool():
    pool = _get_thread_pool(size=2)
    assert isinstance(pool, ThreadPool)


def test_get_dummy_pool():

    with mock.patch.object(multiprocessing.pool.ThreadPool, '__init__', side_effect=PermissionError('poof')):
        pool = _get_thread_pool(size=2, warn=print)
    assert not isinstance(pool, ThreadPool)
