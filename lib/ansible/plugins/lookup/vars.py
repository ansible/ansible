# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: vars
    author: Ansible Core
    version_added: "2.5"
    short_description: Lookup templated value of variables
    description:
      - Retrieves the value of an Ansible variable.
    options:
      _terms:
        description: The variable names to look up.
        required: True
      regex:
        description: If the variable name to lookup is a regular expression
        default: False
      rtype:
        description: What variable type to return, supported values are 'dict' or 'list'
        default: 'list'
      default:
        description:
            - What to return if a variable is undefined.
            - If no default is set, it will result in an error if any of the variables is undefined.
"""

EXAMPLES = """
- name: Show value of 'variablename'
  debug: msg="{{ lookup('vars', 'variabl' + myvar)}}"
  vars:
    variablename: hello
    myvar: ename

- name: Show default empty since i dont have 'variablnotename'
  debug: msg="{{ lookup('vars', 'variabl' + myvar, default='')}}"
  vars:
    variablename: hello
    myvar: notename

- name: Produce an error since i dont have 'variablnotename'
  debug: msg="{{ lookup('vars', 'variabl' + myvar)}}"
  ignore_errors: True
  vars:
    variablename: hello
    myvar: notename

- name: find several related variables
  debug: msg="{{ lookup('vars', 'ansible_play_hosts', 'ansible_play_batch', 'ansible_play_hosts_all') }}"

- name: alternate way to find some 'prefixed vars' in loop
  debug: msg="{{ lookup('vars', 'ansible_play_' + item) }}"
  loop:
    - hosts
    - batch
    - hosts_all

- name: find variables matching a regular expression
  debug: msg="{{ lookup('vars', 'ansible_play_hosts.*', regex=true) }}"

- name: find variables matching a regular expression, return dict instead of list
  debug: msg="{{ lookup('vars', 'ansible_play_hosts.*', regex=true, rtype='dict') }}"
"""

RETURN = """
_value:
  description:
    - value of the variables requested.
"""

import re
import collections
from ansible.errors import AnsibleError, AnsibleUndefinedVariable
from ansible.module_utils.six import string_types
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        if variables is not None:
            self._templar.set_available_variables(variables)
        myvars = getattr(self._templar, '_available_variables', {})

        self.set_options(direct=kwargs)
        default = self.get_option('default')
        is_regex = self.get_option('regex')
        rtype = self.get_option('rtype')

        if is_regex:
            r = re.compile(terms[0])
            lvars = filter(r.match, myvars)
        else:
            lvars = terms

        ret = collections.OrderedDict()

        for term in lvars:
            if not isinstance(term, string_types):
                raise AnsibleError('Invalid setting identifier, "%s" is not a string, its a %s' % (term, type(term)))

            try:
                try:
                    value = myvars[term]
                except KeyError:
                    try:
                        value = myvars['hostvars'][myvars['inventory_hostname']][term]
                    except KeyError:
                        raise AnsibleUndefinedVariable('No variable found with this name: %s' % term)

                ret[term] = self._templar.template(value, fail_on_undefined=True)
            except AnsibleUndefinedVariable:
                if default is None:
                    raise

        if default is not None and len(ret) == 0:
            ret['default'] = default

        if rtype == 'dict':
            return dict(ret)
        else:
            return list(ret.values())
