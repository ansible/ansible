# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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

import sys
import os
from ansible import errors
from ansible import __version__
import ansible.constants as C

def path_dwim(basedir, given):
    '''
    make relative paths work like folks expect.
    '''

    if given.startswith("/"):
        return os.path.abspath(given)
    elif given.startswith("~"):
        return os.path.abspath(os.path.expanduser(given))
    else:
        return os.path.abspath(os.path.join(basedir, given))

def path_dwim_relative(original, dirname, source, playbook_base, check=True):
    ''' find one file in a directory one level up in a dir named dirname relative to current '''
    # (used by roles code)

    basedir = os.path.dirname(original)
    if os.path.islink(basedir):
        basedir = unfrackpath(basedir)
        template2 = os.path.join(basedir, dirname, source)
    else:
        template2 = os.path.join(basedir, '..', dirname, source)
    source2 = path_dwim(basedir, template2)
    if os.path.exists(source2):
        return source2
    obvious_local_path = path_dwim(playbook_base, source)
    if os.path.exists(obvious_local_path):
        return obvious_local_path
    if check:
        raise errors.AnsibleError("input file not found at %s or %s" % (source2, obvious_local_path))
    return source2 # which does not exist

def unfrackpath(path):
    '''
    returns a path that is free of symlinks, environment
    variables, relative path traversals and symbols (~)
    example:
    '$HOME/../../var/mail' becomes '/var/spool/mail'
    '''
    return os.path.normpath(os.path.realpath(os.path.expandvars(os.path.expanduser(path))))

