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
from ansible.utils.unicode import to_bytes, to_str

__all__ = ['unfrackpath', 'makedirs_safe']

def unfrackpath(path):
    '''
    returns a path that is free of symlinks, environment
    variables, relative path traversals and symbols (~)
    example:
    '$HOME/../../var/mail' becomes '/var/spool/mail'
    '''
    return os.path.normpath(os.path.realpath(os.path.expandvars(os.path.expanduser(to_bytes(path, errors='strict')))))

def makedirs_safe(path, mode=None):
    '''Safe way to create dirs in muliprocess/thread environments'''

    rpath = unfrackpath(path)
    if not os.path.exists(rpath):
        try:
            if mode:
                os.makedirs(rpath, mode)
            else:
                os.makedirs(rpath)
        except OSError as e:
            if e.errno != EEXIST:
                raise AnsibleError("Unable to create local directories(%s): %s" % (rpath, to_str(e)))
