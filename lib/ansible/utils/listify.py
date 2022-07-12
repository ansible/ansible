# (c) 2014 Michael DeHaan, <michael@ansible.com>
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

from collections.abc import Iterable

from ansible.module_utils.six import string_types
from ansible.utils.display import Display

display = Display()

__all__ = ['listify_lookup_plugin_terms']


def listify_lookup_plugin_terms(terms, templar, loader=None, fail_on_undefined=True, convert_bare=False):

    if loader is not None:
        display.deprecated('"listify_lookup_plugin_terms" does not use "dataloader" anymore, the ability to pass it in will be removed in future versions.',
                           version='2.18')

    if isinstance(terms, string_types):
        terms = templar.template(terms.strip(), convert_bare=convert_bare, fail_on_undefined=fail_on_undefined)
    else:
        terms = templar.template(terms, fail_on_undefined=fail_on_undefined)

    if isinstance(terms, string_types) or not isinstance(terms, Iterable):
        terms = [terms]

    return terms
