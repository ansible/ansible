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


FILE_ATTRIBUTES = {
    'A': 'noatime',
    'a': 'append',
    'c': 'compressed',
    'C': 'nocow',
    'd': 'nodump',
    'D': 'dirsync',
    'e': 'extents',
    'E': 'encrypted',
    'h': 'blocksize',
    'i': 'immutable',
    'I': 'indexed',
    'j': 'journalled',
    'N': 'inline',
    's': 'zero',
    'S': 'synchronous',
    't': 'notail',
    'T': 'blockroot',
    'u': 'undelete',
    'X': 'compressedraw',
    'Z': 'compresseddirty',
}


# Used for parsing symbolic file perms
MODE_OPERATOR_RE = re.compile(r'[+=-]')
USERS_RE = re.compile(r'[^ugo]')
PERMS_RE = re.compile(r'[^rwxXstugo]')


_PERM_BITS = 0o7777          # file mode permission bits
_EXEC_PERM_BITS = 0o0111     # execute permission bits
_DEFAULT_PERM = 0o0666       # default file permission bits


def is_executable(path):
    # This function's signature needs to be repeated
    # as the first line of its docstring.
    # This method is reused by the basic module,
    # the repetion helps the basic module's html documentation come out right.
    # http://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#confval-autodoc_docstring_signature
    '''is_executable(path)

    is the given path executable?

    :arg path: The path of the file to check.

    Limitations:

    * Does not account for FSACLs.
    * Most times we really want to know "Can the current user execute this
      file".  This function does not tell us that, only if any execute bit is set.
    '''
    # These are all bitfields so first bitwise-or all the permissions we're
    # looking for, then bitwise-and with the file's mode to determine if any
    # execute bits are set.
    return ((stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH) & os.stat(path)[stat.ST_MODE])


def format_attributes(attributes):
    attribute_list = [FILE_ATTRIBUTES.get(attr) for attr in attributes if attr in FILE_ATTRIBUTES]
    return attribute_list


def get_flags_from_attributes(attributes):
    flags = [key for key, attr in FILE_ATTRIBUTES.items() if attr in attributes]
    return ''.join(flags)


def get_file_arg_spec():
    arg_spec = dict(
        mode=dict(type='raw'),
        owner=dict(),
        group=dict(),
        seuser=dict(),
        serole=dict(),
        selevel=dict(),
        setype=dict(),
        attributes=dict(aliases=['attr']),
    )
    return arg_spec


class LockTimeout(Exception):
    pass


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


class LockedFile:
    '''
    Avoid mixing lock mixing, either use this class or fcntl,
    otherwise it will certainly cause unwanted and/or unexpected behaviour.
    File will automatically be locked on open (or fail to open if not possible)
    and will stay locked until closed.

    Also note that POSIX and BSD locks are notoriouslly unreliable, you should
    really try to avoid andy parallel access to files and use atomic_write to
    ensure data consistency (last writer wins vs having all writers try to lock).
    '''
    def __init__(self, path):
        '''
        :kw path: Path (file) to lock
        '''
        try:
            fcntl.flock()
        except AttributeError:
            # dont have flock (BSD+), fallback to lockf (POSIX)
            self._method = 'lockf'
        except TypeError:
            # method exists, we just called it wrong, on purpose
            self._method = 'flock'

        self._lock_fd = None
        self._path = path

    def open(self, flags='w', lock_timeout=0):
        '''
        Try to open this file with an exclusive lock, within a timeout.
        Please note that currently file locking is very limited on POSIX and unix systems,
        specially if you are using network or shared filesystems.
        It will fail across users, threads and/or processes under many circumstances,
        so try to limit scope as much as possible.

        We don't allow indefinite waiting for a lock as it is too easy to lead to deadlocks,
        the caller can easily implement such, but that we cannot control.

        :kw flags:
            open() flags, defaults to 'w'
        :kw lock_timeout:
            Number of seconds to wait for lock acquisition, fail if timeout is reached.
        :returns: True
        '''
        l_wait = 0.1
        self._lock_fd = open(self._path, flags)

        e_secs = 0
        exc = None
        while True:
            if e_secs >= lock_timeout:
                self._lock_fd.close()
                # note: switch to TimeoutError once older python is dropped
                raise OSError('Could not lock "%s" within %s seconds: %s' % (self._path, lock_timeout, to_native(exc)))
            try:
                self._method(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except (IOError, OSError) as e:
                # IOError is needed for python <= 3.3 support
                # TODO: for certain versions we could capture errno and break early
                # in case of non locking related errors
                time.sleep(l_wait)
                e_secs += l_wait
                exc = e

        return self

    def close(self):
        '''
        Make sure lock file is available for everyone and Unlock the file descriptor
        '''
        if self._lock_fd:
            try:
                self._method(self._lock_fd, fcntl.LOCK_UN)
                self._lock_fd.close()
            except ValueError:  # file wasn't opened, let context manager fail gracefully
                pass

    def _method(args, kwargs):
        do = getattr(fcntl, self._method)
        return do(*args, **kwargs)

    def __getattr__(self, name):

        if hasattr(self, name):
            a = getattr(self, name)
        else:
            a = getattr(self._lock_fd, name)

        return a
