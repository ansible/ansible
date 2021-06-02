# (c) 2021, Kevin Carter <kecarter@redhat.com>
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

from multiprocessing import Process
from multiprocessing.managers import DictProxy

import pytest

from ansible.executor import action_write_locks
from ansible.module_utils import six


ACTION_LOCK = action_write_locks.action_lock
ACTION_WRITE_LOCKS = action_write_locks.action_write_locks


def _acquire_in_thread_lock(test_int):
    """Run thread test.

    Test that that the original value is in our shared
    dictionary and that we can add items into the cache
    from within a process.
    """
    assert "testX" in ACTION_WRITE_LOCKS
    ACTION_WRITE_LOCKS["test%i" % test_int] = ACTION_LOCK()


def test_write_lock():
    """Test that the write lock is created with default items."""
    default_locks = {
        "copy",
        "file",
        "setup",
        "slurp",
        "stat",
    }
    assert default_locks <= set(ACTION_WRITE_LOCKS)

    expected_type = dict if six.PY2 else DictProxy
    assert type(ACTION_WRITE_LOCKS) == expected_type


def test_new_lock():
    """Test a new lock can be created."""
    assert "test" not in ACTION_WRITE_LOCKS
    ACTION_WRITE_LOCKS["test"] = ACTION_LOCK()
    assert "test" in ACTION_WRITE_LOCKS


@pytest.mark.skipif(six.PY2, reason="Test requires python 3")
def test_new_lock_with_threads_and_reimport():
    """Test that a new lock can be created within a Process."""
    ACTION_WRITE_LOCKS["testX"] = ACTION_LOCK()

    processes = [
        Process(target=_acquire_in_thread_lock, args=(item,))
        for item in range(1, 6)
    ]
    for t in processes:
        t.daemon = True
        t.start()

    for t in processes:
        t.join()

    # Assert the test items added in processes are still within the cache.
    test_process_lock_names = {"test{num}".format(num=item) for item in range(1, 6)}
    test_process_lock_names.add("testX")
    assert test_process_lock_names <= set(action_write_locks.action_write_locks)
