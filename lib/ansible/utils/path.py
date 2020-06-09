# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import shutil

from errno import EEXIST, ENOENT
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_bytes, to_native, to_text


__all__ = ['unfrackpath', 'makedirs_safe', 'cs_exists', 'cs_isdir', 'cs_isfile']

if not os.path.exists(__file__):
    raise Exception('unable to determine filesystem case-sensitivity ({0} does not exist)'.format(__file__))

_is_case_insensitive_fs = os.path.exists(__file__.upper())


def unfrackpath(path, follow=True, basedir=None):
    '''
    Returns a path that is free of symlinks (if follow=True), environment variables, relative path traversals and symbols (~)

    :arg path: A byte or text string representing a path to be canonicalized
    :arg follow: A boolean to indicate of symlinks should be resolved or not
    :raises UnicodeDecodeError: If the canonicalized version of the path
        contains non-utf8 byte sequences.
    :rtype: A text string (unicode on pyyhon2, str on python3).
    :returns: An absolute path with symlinks, environment variables, and tilde
        expanded.  Note that this does not check whether a path exists.

    example::
        '$HOME/../../var/mail' becomes '/var/spool/mail'
    '''

    b_basedir = to_bytes(basedir, errors='surrogate_or_strict', nonstring='passthru')

    if b_basedir is None:
        b_basedir = to_bytes(os.getcwd(), errors='surrogate_or_strict')
    elif os.path.isfile(b_basedir):
        b_basedir = os.path.dirname(b_basedir)

    b_final_path = os.path.expanduser(os.path.expandvars(to_bytes(path, errors='surrogate_or_strict')))

    if not os.path.isabs(b_final_path):
        b_final_path = os.path.join(b_basedir, b_final_path)

    if follow:
        b_final_path = os.path.realpath(b_final_path)

    return to_text(os.path.normpath(b_final_path), errors='surrogate_or_strict')


def makedirs_safe(path, mode=None):
    '''
    A *potentially insecure* way to ensure the existence of a directory chain. The "safe" in this function's name
    refers only to its ability to ignore `EEXIST` in the case of multiple callers operating on the same part of
    the directory chain. This function is not safe to use under world-writable locations when the first level of the
    path to be created contains a predictable component. Always create a randomly-named element first if there is any
    chance the parent directory might be world-writable (eg, /tmp) to prevent symlink hijacking and potential
    disclosure or modification of sensitive file contents.

    :arg path: A byte or text string representing a directory chain to be created
    :kwarg mode: If given, the mode to set the directory to
    :raises AnsibleError: If the directory cannot be created and does not already exist.
    :raises UnicodeDecodeError: if the path is not decodable in the utf-8 encoding.
    '''

    rpath = unfrackpath(path)
    b_rpath = to_bytes(rpath)
    if not os.path.exists(b_rpath):
        try:
            if mode:
                os.makedirs(b_rpath, mode)
            else:
                os.makedirs(b_rpath)
        except OSError as e:
            if e.errno != EEXIST:
                raise AnsibleError("Unable to create local directories(%s): %s" % (to_native(rpath), to_native(e)))


def basedir(source):
    """ returns directory for inventory or playbook """
    source = to_bytes(source, errors='surrogate_or_strict')
    dname = None
    if os.path.isdir(source):
        dname = source
    elif source in [None, '', '.']:
        dname = os.getcwd()
    elif os.path.isfile(source):
        dname = os.path.dirname(source)

    if dname:
        # don't follow symlinks for basedir, enables source re-use
        dname = os.path.abspath(dname)

    return to_text(dname, errors='surrogate_or_strict')


def cleanup_tmp_file(path, warn=False):
    """
    Removes temporary file or directory. Optionally display a warning if unable
    to remove the file or directory.

    :arg path: Path to file or directory to be removed
    :kwarg warn: Whether or not to display a warning when the file or directory
        cannot be removed
    """
    try:
        if os.path.exists(path):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                elif os.path.isfile(path):
                    os.unlink(path)
            except Exception as e:
                if warn:
                    # Importing here to avoid circular import
                    from ansible.utils.display import Display
                    display = Display()
                    display.display(u'Unable to remove temporary file {0}'.format(to_text(e)))
    except Exception:
        pass


def is_subpath(child, parent):
    """
    Compares paths to check if one is contained in the other
    :arg: child: Path to test
    :arg parent; Path to test against
     """
    test = False

    abs_child = unfrackpath(child, follow=False)
    abs_parent = unfrackpath(parent, follow=False)

    c = abs_child.split(os.path.sep)
    p = abs_parent.split(os.path.sep)

    try:
        test = c[:len(p)] == p
    except IndexError:
        # child is shorter than parent so cannot be subpath
        pass

    return test


def _explicit_case_sensitive_exists(path):
    """
    Standalone case-sensitive existence check for case-insensitive filesystems. This assumes the parent
    dir exists and is otherwise accessible by the caller.
    :param path: a bytes or text path string to check for existence
    :return: True if the path exists and the paths pass a case-sensitive comparison
    """
    parent, leaf = os.path.split(path)

    if not leaf:
        # root directory or '.', of course it exists
        return True

    # ensure that the leaf matches, and that the parent dirs match (recursively)
    return any(p for p in os.listdir(parent) if p == leaf) and cs_isdir(parent)


def cs_open(file, *args, **kwargs):
    """
    A replacement for open that behaves case-sensitively on case-insensitive filesystems (passes through all args to underlying platform open)
    :param file: a bytes or text path string to open
    :return: a file descriptor if the file exists and the path passes a case-sensitive comparison
    """
    fd = open(file, *args, **kwargs)
    try:
        if _is_case_insensitive_fs and not _explicit_case_sensitive_exists(file):
            try:
                extype = FileNotFoundError
            except NameError:
                extype = IOError
            raise extype(ENOENT, os.strerror(ENOENT), file)
    except Exception:
        fd.close()
        raise

    return fd


def cs_exists(path):
    """
    A replacement for os.path.exists that behaves case-sensitive on case-insensitive filesystems
    :param path: a bytes or text path string to check for existence
    :return: True if the path exists and the paths pass a case-sensitive comparison
    """
    raw_exists = os.path.exists(path)
    if not _is_case_insensitive_fs or not raw_exists:
        return raw_exists

    # we're on a case-insensitive filesystem and the file exists, verify its case matches
    return _explicit_case_sensitive_exists(path)


def cs_isdir(path):
    """
    A replacement for os.path.isdir that behaves case-sensitive on case-insensitive filesystems
    :param path: a bytes or text path string to check if isdir
    :return: True if the path is a dir (or resolves to one) and the paths pass a case-sensitive comparison
    """
    return os.path.isdir(path) and (not _is_case_insensitive_fs or _explicit_case_sensitive_exists(path))


def cs_isfile(path):
    """
    A replacement for os.path.isfile that behaves case-sensitive on case-insensitive filesystems
    :param path: a bytes or text path string to check if isfile
    :return: True if the path is a file (or resolves to one) and the paths pass a case-sensitive comparison
    """
    return os.path.isfile(path) and (not _is_case_insensitive_fs or _explicit_case_sensitive_exists(path))
