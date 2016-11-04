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
from ansible.utils.unicode import to_bytes

__all__ = ['unfrackpath']

def unfrackpath(path, follow=True):
    '''
    Returns a path that is free of symlinks (if follow=True), environment variables, relative path traversals and symbols (~)

    :arg path: A byte or text string representing a path to be canonicalized
    :raises UnicodeDecodeError: If the canonicalized version of the path
        contains non-utf8 byte sequences.
    :rtype: A text string (unicode on pyyhon2, str on python3).
    :returns: An absolute path with symlinks, environment variables, and tilde
        expanded.  Note that this does not check whether a path exists.

    example::
        '$HOME/../../var/mail' becomes '/var/spool/mail'
    '''

    if follow:
        final_path = os.path.normpath(os.path.realpath(os.path.expanduser(os.path.expandvars(path))))
    else:
        final_path = os.path.normpath(os.path.abspath(os.path.expanduser(os.path.expandvars(path))))

    return final_path

def makedirs_safe(path, mode=None):
    '''Safe way to create dirs in muliprocess/thread environments'''
    if not os.path.exists(to_bytes(path, errors='strict')):
        try:
            if mode:
                os.makedirs(path, mode)
            else:
                os.makedirs(path)
        except OSError as e:
            if e.errno != EEXIST:
                raise
