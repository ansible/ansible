# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

__all__ = ['LookupBase']

class LookupBase:
    def __init__(self, loader=None, **kwargs):
        self._loader = loader

    def _flatten(self, terms):
        ret = []
        for term in terms:
            if isinstance(term, (list, tuple)):
                ret.extend(term)
            else:
                ret.append(term)
        return ret

    def _combine(self, a, b):
        results = []
        for x in a:
            for y in b:
                results.append(self._flatten([x,y]))
        return results

    def _flatten_hash_to_list(self, terms):
        ret = []
        for key in terms:
            ret.append({'key': key, 'value': terms[key]})
        return ret

