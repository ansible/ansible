# Copyright (c) 2018, Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

import errno
import os
import stat
import re
import pwd
import grp
import time
import shutil
import tempfile
import traceback
import fcntl

from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.six import b, binary_type
from contextlib import contextmanager

try:
    import selinux
    HAVE_SELINUX = True
except ImportError:
    HAVE_SELINUX = False

class LockTimeout(Exception):
    pass


class FileLock():
    def __init__(self):
        self.lockfd = None

    @contextmanager
    def lock_file(self, path, lock_timeout=None):
        '''
        Context for lock acquisition
        '''
        try:
            self.set_lock(path, lock_timeout)
            print('lock aquired')
            yield
        finally:
            print('releasing lock')
            self.unlock()

    def set_lock(self, path, lock_timeout=None):
        '''
        Create a lock file based on path with flock to prevent other processes
        using given path

        :kw path: Path (file) to lock
        :kw lock_timeout: Wait n seconds for lock acquisition
            Default is None (wait until lock is released)
            0 = Do not wait
        :returns: True if successful else an exception is raised
        '''
        tmp_dir = tempfile.gettempdir()
        lock_path = os.path.join(tmp_dir, 'ansible-{0}.lock'.format(os.path.basename(path)))
        l_wait = 0.1

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
                except IOError or BlockingIOError:
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
        Unlock the file descriptor locked by set_lock

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
