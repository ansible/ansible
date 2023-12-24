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

from __future__ import annotations

import os
from os.path import isdir, isfile, isabs, exists, lexists, islink, samefile, ismount

from ansible import errors
from ansible.module_utils.parsing.convert_bool import boolean


def empty(path, _trim=False):
    """Test if a directory or file is empty"""
    trim = boolean(_trim)

    if os.path.isdir(path):
        with os.scandir(path) as it:
            return not any(it)

    elif os.path.isfile(path):
        if not trim:
            return os.path.getsize(path) == 0

        with open(path, "r") as f:
            return not any(line.strip() for line in f)
    else:
        raise errors.AnsibleFilterError(
            "Path %s is neither a directory nor a file." % path
        )

    return False


class TestModule(object):
    ''' Ansible file jinja2 tests '''

    def tests(self):
        return {
            # file testing
            'directory': isdir,
            'is_dir': isdir,
            'file': isfile,
            'is_file': isfile,
            'link': islink,
            'is_link': islink,
            'exists': exists,
            'link_exists': lexists,

            # path testing
            'abs': isabs,
            'is_abs': isabs,
            'same_file': samefile,
            'is_same_file': samefile,
            'mount': ismount,
            'is_mount': ismount,

            "empty": empty,
            "is_empty": empty,
        }
