# (c) 2020, Felix Fontein <felix@fontein.de>
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


def add_internal_fqcns(names):
    """
    Given a sequence of action/module names, returns a list of these names
    with the same names with the prefixes `ansible.builtin.` and
    `ansible.legacy.` added for all names that are not already FQCNs.
    """
    result = []
    for name in names:
        result.append(name)
        if '.' not in name:
            result.append('ansible.builtin.%s' % name)
            result.append('ansible.legacy.%s' % name)
    return result
