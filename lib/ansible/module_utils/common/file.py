# Copyright (c) 2018, Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import stat
import re
import time
import fcntl

from contextlib import contextmanager
from ansible.module_utils._text import to_bytes
from ansible.module_utils.six import PY3

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


@contextmanager
def lock(path, lock_timeout=15):
    '''
    Context for lock acquisition
    '''
    fd = set_lock(path, lock_timeout)
    yield fd
    unlock(fd)

def set_lock(path, lock_timeout=15):
    '''
    Set lock on given path via fcntl.flock(), note that using
    locks does not guarantee exclusiveness unless all accessing
    processes honor locks.

    :kw path: Path (file) to lock
    :kw lock_timeout:
        Wait n seconds for lock acquisition, fail if timeout is reached.
        0 = Do not wait, fail if lock cannot be acquired immediately,
        Less than 0 or None = wait indefinitely until lock is released
        Default is wait 15s.
    :returns: True
    '''
    b_lock_path = to_bytes(path, errors='surrogate_or_strict')
    l_wait = 0.01
    r_exception = IOError
    if not os.path.exists(b_lock_path):
        raise IOError('{0} does not exist'.format(path))

    if PY3:
        r_exception = BlockingIOError

    fd = open(b_lock_path, 'ab+')

    fcntl.lockf(fd, fcntl.LOCK_EX)
    return fd

    if lock_timeout is None or lock_timeout < 0:
        fcntl.lockf(fd, fcntl.LOCK_EX)
        return fd

    if lock_timeout > 0:
        e_secs = 0
        while e_secs <= lock_timeout:
            try:
                fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return fd
            except r_exception:
                time.sleep(l_wait)
                e_secs += l_wait
                continue

        fd.close()
        raise LockTimeout('{0} sec'.format(lock_timeout))

def unlock(fd):
    '''
    Make sure lock file is available for everyone and Unlock the file descriptor
    locked by set_lock

    :returns: True
    '''
    if not fd:
        return

    try:
        fcntl.lockf(fd, fcntl.LOCK_UN)
        fd.close()
    except ValueError:  # file wasn't opened, let context manager fail gracefully
        pass
