# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    name: nested
    version_added: "1.1"
    short_description: composes a list with nested elements of other lists
    description:
        - Takes the input lists and returns a list with elements that are lists composed of the elements of the input lists
    options:
      _raw:
         description:
           - a set of lists
         required: True
"""

EXAMPLES = """
- name: give users access to multiple databases
  community.mysql.mysql_user:
    name: "{{ item[0] }}"
    priv: "{{ item[1] }}.*:ALL"
    append_privs: yes
    password: "foo"
  with_nested:
    - [ 'alice', 'bob' ]
    - [ 'clientdb', 'employeedb', 'providerdb' ]
# As with the case of 'with_items' above, you can use previously defined variables.:

- name: here, 'users' contains the above list of employees
  community.mysql.mysql_user:
    name: "{{ item[0] }}"
    priv: "{{ item[1] }}.*:ALL"
    append_privs: yes
    password: "foo"
  with_nested:
    - "{{ users }}"
    - [ 'clientdb', 'employeedb', 'providerdb' ]
"""

RETURN = """
  _list:
    description:
      - A list composed of lists paring the elements of the input lists
    type: list
"""

from jinja2.exceptions import UndefinedError

from ansible.errors import AnsibleError, AnsibleUndefinedVariable
from ansible.plugins.lookup import LookupBase
from ansible.utils.listify import listify_lookup_plugin_terms


class LookupModule(LookupBase):

    def _lookup_variables(self, terms, variables):
        results = []
        for x in terms:
            try:
                intermediate = listify_lookup_plugin_terms(x, templar=self._templar, fail_on_undefined=True)
            except UndefinedError as e:
                raise AnsibleUndefinedVariable("One of the nested variables was undefined. The error was: %s" % e)
            results.append(intermediate)
        return results

    def run(self, terms, variables=None, **kwargs):

        terms = self._lookup_variables(terms, variables)

        my_list = terms[:]
        my_list.reverse()
        result = []
        if len(my_list) == 0:
            raise AnsibleError("with_nested requires at least one element in the nested list")
        result = my_list.pop()
        while len(my_list) > 0:
            result2 = self._combine(result, my_list.pop())
            result = result2
        new_result = []
        for x in result:
            new_result.append(self._flatten(x))
        return new_result
