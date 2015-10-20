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

from os.path import isdir, isfile, isabs, exists, lexists, islink, samefile, ismount
from ansible import errors

class TestModule(object):
    ''' Ansible file jinja2 tests '''

    def tests(self):
        return {
            # file testing
            'is_dir'  : isdir,
            'is_file' : isfile,
            'is_link' : islink,
            'exists' : exists,
            'link_exists' : lexists,

            # path testing
            'is_abs' : isabs,
            'is_same_file' : samefile,
            'is_mount' : ismount,
        }
