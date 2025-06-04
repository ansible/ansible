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
from __future__ import annotations

from collections.abc import Iterable

from ansible.utils.display import Display

display = Display()

__all__ = ['listify_lookup_plugin_terms']


def listify_lookup_plugin_terms(terms, templar=None, fail_on_undefined=True):
    # deprecated: description="Calling listify_lookup_plugin_terms function is not necessary; the function should be deprecated." core_version="2.23"
    # display.deprecated(
    #     msg='The "listify_lookup_plugin_terms" function is not required for lookup terms to be templated.',
    #     version='2.27',
    #     help_text='If needed, implement custom `strip` or list-wrapping in the caller.',
    # )

    if isinstance(terms, str):
        terms = terms.strip()

    if isinstance(terms, str) or not isinstance(terms, Iterable):
        terms = [terms]

    return terms
