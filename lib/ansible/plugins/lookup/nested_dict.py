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

"""
Lookup plugin to flatten nested dictionaries for linear iteration
=================================================================

For example, a collection of holidays nested by year, month, and day:

    {
        '2016': {
            'January': {
                '1':  'New Years Day',
                '19': 'Martin Luther King Day',
            },
            'February': {
                '14': 'Valentines Day',
                '16': 'Presidents Day',
            },
            ...
        },
        ...
    }

Would be flattened into an array of shallow dicts, with each original key denoted by its nesting level:

    [
        { 'key_0': '2016', 'key_1': 'January',  'key_2': '1',  'val': 'New Years Day' },
        { 'key_0': '2016', 'key_1': 'January',  'key_2': '19', 'val': 'Martin Luther King Day' },
        { 'key_0': '2016', 'key_1': 'February', 'key_2': '14', 'val': 'Valentines Day' },
        { 'key_0': '2016', 'key_1': 'February', 'key_2': '16', 'val': 'Presidents Day' },
        ...
    ]

The nested keys and value of each are then exposed to an iterative task:

    - name:               "Remind us what holidays are this month"
      debug:
        msg:              "Remember {{val}} on {{key_1}} {{'%02d'|format(key_2)}} in the year {{key_0}}"
      when:               key_1 == current_month
      with_nested_dict:   holidays_by_year_month_day

"""
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

