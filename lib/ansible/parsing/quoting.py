# (c) 2014 James Cammarata, <jcammarata@ansible.com>
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


def is_quoted(data):
    if len(data) <= 1 or data[0] not in ('"', "'") or data[0] != data[-1]:
        return False
    return (len(data[:-1]) - len(data[:-1].rstrip('\\'))) % 2 == 0


def unquote(data):
    """ removes first and last quotes from a string, if the string starts and ends with the same quotes """
    if is_quoted(data):
        return data[1:-1]
    return data
