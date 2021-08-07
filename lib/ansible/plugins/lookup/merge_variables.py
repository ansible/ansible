# (c) 2020 Thales Netherlands
# (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    name: merge_variables
    author:
      - Roy Lenferink (@rlenferink) <lenferinkroy@gmail.com>
      - Mark Ettema (@m-a-r-k-e) <dev@markettema.nl>
    version_added: "2.12"
    short_description: merge variables with a certain suffix
    description:
        - This lookup returns the merged result of all variables in scope that matches the given suffix optionally
          starting with an initial value.
    options:
      _terms:
        description:
          - The suffix of the variable name (all available variables will be checked with endswith(suffix))
        required: true
      initial_value:
        description:
          - An initial value to start with
        required: false
      override_warning:
        description:
          - Print a warning when a key will be overwritten
        default: false
      override_error:
        description:
          - Return error when a key will be overwritten
        default: false
"""

EXAMPLES = """
# Some example variables, they can be defined anywhere as long as they are in scope
test_init_list:
  - "list init item 1"
  - "list init item 2"

testa__test_list:
  - "test a item 1"

testb__test_list:
  - "test b item 1"

testa__test_dict:
  ports:
    - 1

testb__test_dict:
  ports:
    - 3


# Merging variables that ends with '__test_dict' and store the result in a variable 'example_a'
example_a: "{{ lookup('merge_variables', '__test_dict') }}"

# The variable example_a now contains:
# ports:
#   - 1
#   - 3


# Merging variables that ends with '__test_list', starting with an initial value and store the result
# in a variable 'example_b'
example_b: "{{ lookup('merge_variables', '__test_list', initial_value=test_init_list) }}"

# The variable example_b now contains:
#   - "list init item 1"
#   - "list init item 2"
#   - "test a item 1"
#   - "test b item 1"
"""

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.utils.display import Display

display = Display()


def _verify_and_get_type(variable):
    if isinstance(variable, list):
        return "list"
    elif isinstance(variable, dict):
        return "dict"
    else:
        raise AnsibleError("Not supported type detected, variable must be a list or a dict")


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        self.set_options(direct=kwargs)
        initial_value = self.get_option("initial_value", None)
        self._override_warning = boolean(self.get_option('override_warning', False))
        self._override_error = boolean(self.get_option('override_error', False))

        ret = []
        for term in terms:
            ret.append(self._merge_vars(term, initial_value, variables))

        return ret

    def _merge_vars(self, search_suffix, initial_value, variables):
        display.v("Merge variables with suffix: {0}".format(search_suffix))
        var_merge_names = sorted([key for key in variables.keys() if key.endswith(search_suffix)])
        display.v("The following variables will be merged: {0}".format(var_merge_names))

        prev_var_type = None
        result = None

        if initial_value is not None:
            display.v("Start merge with initial value: {0}".format(initial_value))
            prev_var_type = _verify_and_get_type(initial_value)
            result = initial_value

        for var_name in var_merge_names:
            var_value = self._templar.template(variables[var_name])  # Render jinja2 templates
            var_type = _verify_and_get_type(var_value)

            if prev_var_type is None:
                prev_var_type = var_type
            elif prev_var_type != var_type:
                raise AnsibleError("Unable to merge, not all variables are of the same type")

            if result is None:
                result = var_value
                continue

            if var_type == "dict":
                result = self._merge_dict(var_value, result, [var_name])
            else:  # var_type == "list"
                result += var_value

        return result

    def _merge_dict(self, src, dest, path):
        for key, value in src.items():
            if isinstance(value, dict):
                node = dest.setdefault(key, {})
                self._merge_dict(value, node, path + [key])
            elif isinstance(value, list) and key in dest:
                dest[key] += value
            else:
                if (key in dest) and dest[key] != value:
                    msg = "The key '{0}' with value '{1}' will be overwritten with value '{2}' from '{3}.{0}'".format(
                        key, dest[key], value, ".".join(path))

                    if self._override_error:
                        raise AnsibleError(msg)
                    if self._override_warning:
                        display.warning(msg)

                dest[key] = value

        return dest
