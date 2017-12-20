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

from errno import EEXIST
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_bytes, to_native, to_text


__all__ = ['unfrackpath', 'makedirs_safe']


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

    if basedir is None:
        basedir = os.getcwd()
    elif os.path.isfile(basedir):
        basedir = os.path.dirname(basedir)

    final_path = os.path.expanduser(os.path.expandvars(to_bytes(path, errors='surrogate_or_strict')))

    if not os.path.isabs(final_path):
        final_path = os.path.join(to_bytes(basedir, errors='surrogate_or_strict'), final_path)

    if follow:
        final_path = os.path.realpath(final_path)

    return to_text(os.path.normpath(final_path), errors='surrogate_or_strict')


def makedirs_safe(path, mode=None):
    '''Safe way to create dirs in muliprocess/thread environments.

    :arg path: A byte or text string representing a directory to be created
    :kwarg mode: If given, the mode to set the directory to
    :raises AnsibleError: If the directory cannot be created and does not already exists.
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
