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
import hashlib
import tempfile

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
    """ Class for file locking, to avoid race conditions between multiple ansible processes.
        Keep in mind this is advisory locking only (ansible's internal agreement). Any other process that doesn't
        respect or know about our locking strategy can still read/write/remove original file.
        In Python fcntl.lockf function should be used, which actually calls fcntl system API.
        You can read more at https://apenwarr.ca/log/20101213
    """
    def __init__(self, path, lock_timeout=15, check_mode=False):
        self.lock_directory = None
        self.lock_file = None
        self.path = path
        self.lock_timeout = lock_timeout
        self.check_mode = check_mode

    def __enter__(self):
        """" Set lock
             We are setting lock on separate .lock file. Cannot lock original file, as ansible modules usually use
             atomic_move function that changes inode, on which lock actually relies.
         """
        if self.check_mode:
            return True
        else:
            # The default umask is 0o22 which turns off write permission of group and others
            os.umask(0)

            # Assure directory for .lock files
            # On linux this is /tmp/
            # On macos /var/folders/**/***/T/ which only has current user permissions (multi-user locking won't work)
            sys_temp = tempfile.gettempdir()
            self.lock_directory = os.path.join(sys_temp, 'ansible-locks')
            try:
                os.mkdir(self.lock_directory, 0o777)
            except OSError as exc:
                if exc.errno == errno.EEXIST and os.path.isdir(self.lock_directory):
                    pass
                else:
                    raise

            # Generate .lock filename based on 'path', as we cannot rely on inode
            lock_file_name = hashlib.sha256(self.path.encode('utf-8')).hexdigest()[:10]
            lock_file_path = os.path.join(self.lock_directory, '{0}.lock'.format(lock_file_name))

            # Open fd with low-level call, so we can set permission bits to allow multi-user functionality
            # Modify/change timestamp also has to update, so systemd-tempfiles service doesn't delete it
            self.lock_file = os.open(lock_file_path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o666)

            # Try to acquire lock (immediately)
            if self.lock_timeout <= 0:  # Also catches None
                fcntl.flock(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True

            # Try until timeout is reached
            wait_interval = 0.1
            total_wait = 0
            while total_wait <= self.lock_timeout:
                try:
                    fcntl.flock(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    return True
                except (IOError, OSError):
                    time.sleep(wait_interval)
                    total_wait += wait_interval
                    continue
            os.close(self.lock_file)
            raise LockTimeout('Waited {0} seconds for lock on {1}'.format(total_wait, self.path))

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Remove lock
            Fcntl releases lock automatically when file descriptor is closed. So even if process crashes or is killed,
            we are sure deadlock is avoided. As a good programming practice, we still unlock and close on exit if
            everything goes well.
            We should not remove .lock file, as second process might opened it already and has file handler in memory.
            In that moment third process will see that file doesn't exist, create it and lock it. Both second and third
            process will gain exclusive lock (although on files with different inodes).
        """
        try:
            fcntl.lockf(self.lock_file, fcntl.LOCK_UN)
            self.lock_file.close()
        except (TypeError, AttributeError):
            # Lock file wasn't opened in check_mode
            pass
