# Copyright (c) 2018, Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import fcntl
import grp
import os
import pwd
import re
import stat
import sys
import time

from contextlib import contextmanager
from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.common.warnings import deprecate, warn
from ansible.module_utils.common.selinux import is_selinux_enabled, get_selinux_context

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

_cleanup_files = set()


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


def remove_file(path, fail=False):
    '''
    Will try to remove a file if it exists/is visible for the current user,
    It will write an error

    :path: Byte string containing the path to remove
    :fail: If it should raise an exception on failiure, otherwise it will warn
    '''
    if os.path.exists(path):
        try:
            os.unlink(path)
        except OSError as e:
            if fail:
                raise
            warn("could not cleanup %s: %s" % (to_text(path), to_text(e)))


def add_to_file_cleanup(path):
    ''' Add path to cleanup global for later removal '''

    b_path = to_bytes(path, errors='surrogate_or_strict')
    if os.path.exists(b_path):
        global _cleanup_files
        _cleanup_files.add(b_path)


def cleanup_files():
    ''' Remove all files that were queued up in cleanup global '''

    for rmfile in _cleanup_files:
        remove_file(rmfile, False)


def get_path_uid_and_gid(path, expand=True):
    ''' get uid and gid ownership from path '''

    b_path = to_bytes(path, errors='surrogate_or_strict')
    if expand:
        b_path = os.path.expanduser(os.path.expandvars(b_path))
    st = os.lstat(b_path)
    uid = st.st_uid
    gid = st.st_gid

    return (uid, gid)


def get_path_type(path):
    ''' return type of file from given path byte string '''
    ptype = None
    if os.path.islink(path):
        ptype = 'link'
    elif os.path.isdir(path):
        ptype = 'directory'
    elif os.stat(path).st_nlink > 1:
        ptype = 'hard'
    else:
        ptype = 'file'

    return ptype


def get_info_from_path(path):
    '''
    for results that are files, supplement the info about the file
    in the return path with stats about the file path.
    '''

    b_path = os.path.expanduser(os.path.expandvars(to_bytes(path, errors='surrogate_or_strict')))
    info = {}

    if os.path.exists(b_path):

        st = os.lstat(b_path)

        info['uid'] = st.st_uid
        info['gid'] = st.st_gid
        try:
            user = pwd.getpwuid(info['uid'])[0]
        except KeyError:
            user = to_text(info['uid'])
        try:
            group = grp.getgrgid(info['gid'])[0]
        except KeyError:
            group = to_text(info['gid'])
        info['owner'] = user
        info['group'] = group

        info['mode'] = '0%03o' % stat.S_IMODE(st[stat.ST_MODE])
        info['size'] = st[stat.ST_SIZE]
        info['state'] = get_path_type(b_path)
        if is_selinux_enabled():
            info['secontext'] = ':'.join(get_selinux_context(path))

    return info


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
        deprecate("FileLock is not reliable and has never been used in core for that reason. There is no current alternative that works across POSIX targets",
                  version='2.16')
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
