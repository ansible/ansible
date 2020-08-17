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
import tempfile
import traceback
import fcntl
import sys

from contextlib import contextmanager
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.common.sys_info import (
    selinux_context,
    selinux_enabled,
    selinux_mls_enabled,
)
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


def _unsafe_writes(src, dest):
    """
    Sadly there are some situations where we cannot ensure atomicity, but only
    if the user insists and we get the appropriate error we update the file
    unsafely
    """

    try:
        out_dest = in_src = None
        try:
            out_dest = open(dest, 'wb')
            in_src = open(src, 'rb')
            shutil.copyfileobj(in_src, out_dest)
        finally:  # assuring closed files in 2.4 compatible way
            if out_dest:
                out_dest.close()
            if in_src:
                in_src.close()
    except (shutil.Error, OSError, IOError) as e:
        raise
        self.fail_json(msg='Could not write data to file (%s) from (%s): %s' % (dest, src, to_native(e)),
                       exception=traceback.format_exc())


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


def move_and_set_attributes(src, dest, unsafe_writes=False):
    """
    Atomically move a file and set the specified permissions on the dest.
    If
    """
    move_file(src, dest, unsafe_writes=unsafe_writes)
    set_fs_attributes_if_different()
    pass


def move_file(src, dest, unsafe_writes=False):
    """
    Move a file atomically, preserving the source attributes in the destination.

    :arg src:
    :arg dest:
    :kwarg unsafe_writes:
    """

    b_src = to_bytes(src, errors='surrogate_or_strict')
    b_dest = to_bytes(dest, errors='surrogate_or_strict')

    try:
        # Optimistically try a rename, solves some corner cases and can avoid useless work,
        # throws exception if not atomic.
        os.rename(b_src, b_dest)
    except (IOError, OSError) as e:
        # only try workarounds for errno 18 (cross device), 1 (not permitted),  13 (permission
        # denied) and 26 (text file busy) which happens on vagrant synced folders and other
        # 'exotic' non posix file systems
        if e.errno not in [errno.EPERM, errno.EXDEV, errno.EACCES, errno.ETXTBSY, errno.EBUSY]:
            raise
    else:
        # Success!
        return

    #
    # The rest of this function is to simulate a rename with a copy
    #

    # Gather metadata about the src file so we can replicate it at the destination
    src_stat = os.stat(b_src)

    context = None
    if selinux_enabled():
        context = selinux_context(src)

    #
    # Create a temporary file in the destination directory that we can rename at the end
    #

    # Use bytes here.  In the shippable CI, this fails with
    # a UnicodeError with surrogateescape'd strings for an unknown
    # reason (doesn't happen in a local Ubuntu16.04 VM)
    b_dest_dir = os.path.dirname(b_dest)
    b_suffix = os.path.basename(b_dest)
    error_msg = None
    tmp_dest_name = None
    try:
        # The temp file is created such that only the user can read and write it.
        tmp_dest_fd, tmp_dest_name = tempfile.mkstemp(prefix=b'.ansible_tmp',
                                                      dir=b_dest_dir, suffix=b_suffix)
    except (OSError, IOError) as e:
        error_msg = ('The destination directory (%s) is not writable by the current user.'
                     ' Error was: %s' % (os.path.dirname(dest), to_native(e)))
    except TypeError:
        # We expect that this is happening because python3.4.x and
        # below can't handle byte strings in mkstemp().  Traceback
        # would end in something like:
        #     file = _os.path.join(dir, pre + name + suf)
        # TypeError: can't concat bytes to str
        error_msg = ('Failed creating tmp file for atomic move.  This usually happens when'
                     ' using Python3 less than Python3.5. Please use Python2.x or Python3.5'
                     ' or greater.')
    if error_msg:
        if unsafe_writes:
            return self._unsafe_writes(b_src, b_dest)
        else:
            raise IOError(error_msg)

    b_tmp_dest_name = to_bytes(tmp_dest_name, errors='surrogate_or_strict')

    try:
        # close tmp file handle before file operations to prevent text file busy errors on
        # vboxfs synced folders (windows host)
        os.close(tmp_dest_fd)

        # leaves tmp file behind when sudo and not root
        try:
            shutil.move(b_src, b_tmp_dest_name)
        except OSError:
            # cleanup will happen by 'rm' of tmpdir
            # copy2 will preserve some metadata
            shutil.copy2(b_src, b_tmp_dest_name)

        # Flags have to be copied manually and aren't supported on all platforms
        if hasattr(os, 'chflags') and hasattr(src_stat, 'st_flags'):
            try:
                os.chflags(b_tmp_dest_name, src_stat.st_flags)
            except OSError as e:
                for err in 'EOPNOTSUPP', 'ENOTSUP':
                    if hasattr(errno, err) and e.errno == getattr(errno, err):
                        break
                else:
                    raise

        # SELinux contexts have to be set manually
        if context:
            self.set_context_if_different(b_tmp_dest_name, context, False)

        # Copy2 does not set owner and group so we have to do it here
        try:
            tmp_stat = os.stat(b_tmp_dest_name)
            if src_stat and (tmp_stat.st_uid != src_stat.st_uid
                             or tmp_stat.st_gid != src_stat.st_gid):
                os.chown(b_tmp_dest_name, src_stat.st_uid, src_stat.st_gid)
        except OSError as e:
            # Allow EPERM to pass in case we're an unprivileged user (historical.  May want
            # to change this so the caller decides what to do.)
            if e.errno != errno.EPERM:
                raise

        # Try to rename our temporary file to the real destination
        try:
            os.rename(b_tmp_dest_name, b_dest)
        except (shutil.Error, OSError, IOError) as e:
            if unsafe_writes and e.errno == errno.EBUSY:
                return self._unsafe_writes(b_tmp_dest_name, b_dest)
            raise
    finally:
        self.cleanup(b_tmp_dest_name)

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
