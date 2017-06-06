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

Would be flattened into an array of dicts, each with a value and list of keys (ordered by their nesting level from shallow to deep):

    [
        { 'nested': ['2016', 'January',  '1'],  'value': 'New Years Day' },
        { 'nested': ['2016', 'January',  '19'], 'value': 'Martin Luther King Day' },
        { 'nested': ['2016', 'February', '14'], 'value': 'Valentines Day' },
        { 'nested': ['2016', 'February', '16'], 'value': 'Presidents Day' },
        ...
    ]

The nested keys and value of each are then exposed to an iterative task:

    - name: Print holidays for this month
      debug:
        msg: "Remember {{ item.value }} on {{ item.nested[1] }} {{ '%02d' | format(item.nested[2]|int) }}, {{ item.nested[0] }}"
      when: item.nested[1] == "January"
      with_nested_dict: "{{ holidays_by_year_month_day }}"

"""


class LookupModule(LookupBase):

    @staticmethod
    def _flatten_nested_hash_to_list(terms, result=None, stack=None):
        result = list() if result is None else result
        stack = dict(nested=list()) if stack is None else stack

        for key, val in terms.items():
            working = LookupModule._stack_copy(stack)

            working['nested'].append(key)
            if type(val) is dict:
                LookupModule._flatten_nested_hash_to_list(terms=val, result=result, stack=LookupModule._stack_copy(working))
            else:
                working['value'] = val
                result.append(working)

        return result

    @staticmethod
    def _stack_copy(stack):
        copied = stack.copy()
        copied['nested'] = list(stack['nested'])
        return copied

    def run(self, terms, variables=None, **kwargs):
        if not isinstance(terms, dict):
            raise AnsibleError("with_nested_dict expects a dict")

        return self._flatten_nested_hash_to_list(terms)
