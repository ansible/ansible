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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils._text import to_bytes as _to_bytes, to_text, to_native

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


__all__ = ('to_bytes', 'to_unicode', 'to_str', 'unicode_wrap')


###
### Backwards compat
###

def to_bytes(*args, **kwargs):
    display.deprecated(u'ansible.utils.unicode.to_bytes is deprecated.  Use ansible.module_utils._text.to_bytes instead', version=u'2.4')
    if 'errors' not in kwargs:
        kwargs['errors'] = 'replace'
    return _to_bytes(*args, **kwargs)


def to_unicode(*args, **kwargs):
    display.deprecated(u'ansible.utils.unicode.to_unicode is deprecated.  Use ansible.module_utils._text.to_text instead', version=u'2.4')
    if 'errors' not in kwargs:
        kwargs['errors'] = 'replace'
    return to_text(*args, **kwargs)


def to_str(*args, **kwargs):
    display.deprecated(u'ansible.utils.unicode.to_str is deprecated.  Use ansible.module_utils._text.to_native instead', version=u'2.4')
    if 'errors' not in kwargs:
        kwargs['errors'] = 'replace'
    return to_native(*args, **kwargs)

### End Backwards compat


def unicode_wrap(func, *args, **kwargs):
    """If a function returns a string, force it to be a text string.

    Use with partial to ensure that filter plugins will return text values.
    """
    return to_text(func(*args, **kwargs), nonstring='passthru')
