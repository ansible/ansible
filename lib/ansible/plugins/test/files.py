# (c) 2015, Ansible, Inc
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from functools import partial
from os.path import isdir, isfile, isabs, exists, lexists, islink, samefile, ismount, expanduser, expandvars

from ansible import constants as C


def expand_path_wrap(func, *args):
    expanded_args = [expanduser(expandvars(a)) for a in args]
    return func(*expanded_args)


class TestModule(object):
    ''' Ansible file jinja2 tests '''

    def tests(self):
        tests = {
            # file testing
            'is_dir': isdir,
            'directory': isdir,
            'is_file': isfile,
            'file': isfile,
            'is_link': islink,
            'link': islink,
            'exists': exists,
            'link_exists': lexists,

            # path testing
            'is_abs': isabs,
            'abs': isabs,
            'is_same_file': samefile,
            'same_file': samefile,
            'is_mount': ismount,
            'mount': ismount,
        }

        if C.EXPAND_PATH_FILE_TESTS:
            return dict((k, partial(expand_path_wrap, v)) for k, v in tests.items())

        return tests
