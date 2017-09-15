# (c) 2017, Yannig Perre <yannig.perre@gmail.com>
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


def getmountfrompath(path, mounts):
    '''return the closest corresponding mount for a given path'''
    current_string_length = 0
    current_mount = None
    for mount in mounts:
        if mount['mount'].startswith('/'):
            if current_string_length < len(mount['mount']) and path.startswith(mount['mount']):
                current_string_length = len(mount['mount'])
                current_mount = mount
    return current_mount


class FilterModule(object):
    ''' Ansible filesystem jinja2 filters '''

    def filters(self):
        return {
            'getmountfrompath': getmountfrompath,
        }
