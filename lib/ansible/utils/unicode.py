# (c) 2012-2014, Toshio Kuratomi <a.badger@gmail.com>
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

from ansible.module_utils.common.text.converters import to_text


__all__ = ('unicode_wrap',)


def unicode_wrap(func, *args, **kwargs):
    """If a function returns a string, force it to be a text string.

    Use with partial to ensure that filter plugins will return text values.
    """
    return to_text(func(*args, **kwargs), nonstring='passthru')
