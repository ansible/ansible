# (c) 2016, Evan Kaufman <ekaufman@digitalflophouse.com>
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

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase

class LookupModule(LookupBase):

    @staticmethod
    def _flatten_nested_hash_to_list(terms, result=None, stack=None, level=None):
        result = [] if result is None else result
        stack = {} if stack is None else stack
        level = 0 if level is None else level

        for key, val in terms.iteritems():
            stack['key_%s' % level] = key
            if type(val) is dict:
                LookupModule._flatten_nested_hash_to_list(terms=val, result=result, stack=stack.copy(), level=level+1)
            else:
                stack['value'] = val
                result.append(stack.copy())
        return result

    def run(self, terms, variables=None, **kwargs):
        if not isinstance(terms, dict):
            raise AnsibleError("with_nested_dict expects a dict")

        return self._flatten_nested_hash_to_list(terms)

