# -*- coding: utf-8 -*-
# (c) 2017 Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils.common.file import (
    FileLock
)


def test_lock_file():
    locker = FileLock()

    assert locker.set_lock("lock", "/tmp")
    assert locker.unlock()

    assert locker.set_lock("lock", "/tmp", None)
    assert locker.unlock()

    assert locker.set_lock("lock", "/tmp", -1)
    assert locker.unlock()

    assert locker.set_lock("lock", "/tmp", 0)
    assert locker.unlock()

    assert locker.set_lock("lock", "/tmp", 1)
    assert locker.unlock()
