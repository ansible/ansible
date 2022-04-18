# (c) 2020, Ansible Project
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


def show_deprecation(display, name, deprecation):
    why = deprecation['why']
    if 'alternatives' in deprecation:
        alt = ', use %s instead' % deprecation['alternatives']
    else:
        alt = ''
    ver = deprecation.get('version')
    date = deprecation.get('date')
    collection_name = deprecation.get('collection_name')
    display.deprecated("%s option, %s%s" % (name, why, alt),
                       version=ver, date=date, collection_name=collection_name)
