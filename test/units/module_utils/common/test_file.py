# -*- coding: utf-8 -*-
# (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import os
import pytest
import sys
from ansible.module_utils.common.file import FileLock, LockTimeout


class TestFileLock:

    @classmethod
    def setup_class(cls):
        if sys.version_info[0] == 3:
            cls.expected_exception = BlockingIOError
        else:
            cls.expected_exception = IOError

    def test_lock(self, tmpdir):
        file = os.path.join(tmpdir, "test_lock.data")
        lock = FileLock()
        with lock.lock_file(file, tmpdir, lock_timeout=0):
            # Try to lock it again
            lock2 = FileLock()
            with pytest.raises(self.expected_exception):
                lock2.set_lock(file, tmpdir, lock_timeout=0)
