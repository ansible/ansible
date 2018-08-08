# Copyright (c) 2018, Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import errno
import os
import stat
import re
import pwd
import grp
import time
import shutil
import traceback
import fcntl
import sys

from contextlib import contextmanager
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.six import b, binary_type

try:
    import selinux
    HAVE_SELINUX = True
except ImportError:
    HAVE_SELINUX = False


class LockTimeout(Exception):
    pass


def is_executable(path):
    '''is the given path executable?

    Limitations:
    * Does not account for FSACLs.
    * Most times we really want to know "Can the current user execute this
      file"  This function does not tell us that, only if an execute bit is set.
    '''
    # These are all bitfields so first bitwise-or all the permissions we're
    # looking for, then bitwise-and with the file's mode to determine if any
    # execute bits are set.
    return ((stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH) & os.stat(path)[stat.ST_MODE])


class FileLock:
    '''
    Currently FileLock is implemented via fcntl.flock on a lock file, however this
    behaviour may change in the future. Avoid mixing lock types fcntl.flock,
    fcntl.lockf and module_utils.common.file.FileLock as it will certainly cause
    unwanted and/or unexpected behaviour
    '''
    def __init__(self):
        self.lockfd = None

    @contextmanager
    def lock_file(self, path, tmpdir, lock_timeout=None):
        '''
        Context for lock acquisition
        '''
        try:
            self.set_lock(path, tmpdir, lock_timeout)
            yield
        finally:
            self.unlock()

    def set_lock(self, path, tmpdir, lock_timeout=None):
        '''
        Create a lock file based on path with flock to prevent other processes
        using given path.
        Please note that currently file locking only works when it's executed by
        the same user, I.E single user scenarios

        :kw path: Path (file) to lock
        :kw tmpdir: Path where to place the temporary .lock file
        :kw lock_timeout:
            Wait n seconds for lock acquisition, fail if timeout is reached.
            0 = Do not wait, fail if lock cannot be acquired immediately,
            Default is None, wait indefinitely until lock is released.
        :returns: True
        '''
        lock_path = os.path.join(tmpdir, 'ansible-{0}.lock'.format(os.path.basename(path)))
        l_wait = 0.1
        r_exception = IOError
        if sys.version_info[0] == 3:
            r_exception = BlockingIOError

        self.lockfd = open(lock_path, 'w')

        if lock_timeout <= 0:
            fcntl.flock(self.lockfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            os.chmod(lock_path, stat.S_IWRITE | stat.S_IREAD)
            return True

        if lock_timeout:
            e_secs = 0
            while e_secs < lock_timeout:
                try:
                    fcntl.flock(self.lockfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    os.chmod(lock_path, stat.S_IWRITE | stat.S_IREAD)
                    return True
                except r_exception:
                    time.sleep(l_wait)
                    e_secs += l_wait
                    continue

            self.lockfd.close()
            raise LockTimeout('{0} sec'.format(lock_timeout))

        fcntl.flock(self.lockfd, fcntl.LOCK_EX)
        os.chmod(lock_path, stat.S_IWRITE | stat.S_IREAD)

        return True

    def unlock(self):
        '''
        Make sure lock file is available for everyone and Unlock the file descriptor
        locked by set_lock

        :returns: True
        '''
        if not self.lockfd:
            return True

        try:
            fcntl.flock(self.lockfd, fcntl.LOCK_UN)
            self.lockfd.close()
        except ValueError:  # file wasn't opened, let context manager fail gracefully
            pass

        return True
