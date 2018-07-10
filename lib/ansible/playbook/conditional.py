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

import ast
import re

from jinja2.compiler import generate
from jinja2.exceptions import UndefinedError

from ansible.errors import AnsibleError, AnsibleUndefinedVariable
from ansible.module_utils.six import text_type
from ansible.module_utils._text import to_native
from ansible.playbook.attribute import FieldAttribute

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


DEFINED_REGEX = re.compile(r'(hostvars\[.+\]|[\w_]+)\s+(not\s+is|is|is\s+not)\s+(defined|undefined)')
LOOKUP_REGEX = re.compile(r'lookup\s*\(')
VALID_VAR_REGEX = re.compile("^[_A-Za-z][_a-zA-Z0-9]*$")


class Conditional:

    '''
    This is a mix-in class, to be used with Base to allow the object
    to be run conditionally when a condition is met or skipped.
    '''

    _when = FieldAttribute(isa='list', default=[], extend=True, prepend=True)

    def __init__(self, loader=None):
        # when used directly, this class needs a loader, but we want to
        # make sure we don't trample on the existing one if this class
        # is used as a mix-in with a playbook base class
        if not hasattr(self, '_loader'):
            if loader is None:
                raise AnsibleError("a loader must be specified when using Conditional() directly")
            else:
                self._loader = loader
        super(Conditional, self).__init__()

    def _validate_when(self, attr, name, value):
        if not isinstance(value, list):
            setattr(self, name, [value])

    def extract_defined_undefined(self, conditional):
        results = []

        cond = conditional
        m = DEFINED_REGEX.search(cond)
        while m:
            results.append(m.groups())
            cond = cond[m.end():]
            m = DEFINED_REGEX.search(cond)

        return results

    def evaluate_conditional(self, templar, all_vars):
        '''
        Loops through the conditionals set on this object, returning
        False if any of them evaluate as such.
        '''

        # since this is a mix-in, it may not have an underlying datastructure
        # associated with it, so we pull it out now in case we need it for
        # error reporting below
        ds = None
        if hasattr(self, '_ds'):
            ds = getattr(self, '_ds')

        try:
            # this allows for direct boolean assignments to conditionals "when: False"
            if isinstance(self.when, bool):
                return self.when

            for conditional in self.when:
                if not self._check_conditional(conditional, templar, all_vars):
                    return False
        except Exception as e:
            raise AnsibleError(
                "The conditional check '%s' failed. The error was: %s" % (to_native(conditional), to_native(e)), obj=ds
            )

        return True

    def _check_conditional(self, conditional, templar, all_vars):
        '''
        This method does the low-level evaluation of each conditional
        set on this object, using jinja2 to wrap the conditionals for
        evaluation.
        '''

        original = conditional
        if conditional is None or conditional == '':
            return True

        if templar.is_template(conditional):
            display.warning('when statements should not include jinja2 '
                            'templating delimiters such as {{ }} or {%% %%}. '
                            'Found: %s' % conditional)

        # pull the "bare" var out, which allows for nested conditionals
        # and things like:
        # - assert:
        #     that:
        #     - item
        #   with_items:
        #   - 1 == 1
        if conditional in all_vars and VALID_VAR_REGEX.match(conditional):
            conditional = all_vars[conditional]

        # make sure the templar is using the variables specified with this method
        templar.set_available_variables(variables=all_vars)

        try:
            # if the conditional is "unsafe", disable lookups
            disable_lookups = hasattr(conditional, '__UNSAFE__')
            conditional = templar.template(conditional, disable_lookups=disable_lookups)
            if not isinstance(conditional, text_type) or conditional == "":
                return conditional

            # update the lookups flag, as the string returned above may now be unsafe
            # and we don't want future templating calls to do unsafe things
            disable_lookups |= hasattr(conditional, '__UNSAFE__')

            # First, we do some low-level jinja2 parsing involving the AST format of the
            # statement to ensure we don't do anything unsafe (using the disable_lookup flag above)
            class CleansingNodeVisitor(ast.NodeVisitor):
                def generic_visit(self, node, inside_call=False, inside_yield=False):
                    if isinstance(node, ast.Call):
                        inside_call = True
                    elif isinstance(node, ast.Yield):
                        inside_yield = True
                    elif isinstance(node, ast.Str):
                        if disable_lookups:
                            if inside_call and node.s.startswith("__"):
                                # calling things with a dunder is generally bad at this point...
                                raise AnsibleError(
                                    "Invalid access found in the conditional: '%s'" % conditional
                                )
                            elif inside_yield:
                                # we're inside a yield, so recursively parse and traverse the AST
                                # of the result to catch forbidden syntax from executing
                                parsed = ast.parse(node.s, mode='exec')
                                cnv = CleansingNodeVisitor()
                                cnv.visit(parsed)
                    # iterate over all child nodes
                    for child_node in ast.iter_child_nodes(node):
                        self.generic_visit(
                            child_node,
                            inside_call=inside_call,
                            inside_yield=inside_yield
                        )
            try:
                e = templar.environment.overlay()
                e.filters.update(templar._get_filters(e.filters))
                e.tests.update(templar._get_tests())

                res = e._parse(conditional, None, None)
                res = generate(res, e, None, None)
                parsed = ast.parse(res, mode='exec')

                cnv = CleansingNodeVisitor()
                cnv.visit(parsed)
            except Exception as e:
                raise AnsibleError("Invalid conditional detected: %s" % to_native(e))

            # and finally we generate and template the presented string and look at the resulting string
            presented = "{%% if %s %%} True {%% else %%} False {%% endif %%}" % conditional
            val = templar.template(presented, disable_lookups=disable_lookups).strip()
            if val == "True":
                return True
            elif val == "False":
                return False
            else:
                raise AnsibleError("unable to evaluate conditional: %s" % original)
        except (AnsibleUndefinedVariable, UndefinedError) as e:
            # the templating failed, meaning most likely a variable was undefined. If we happened
            # to be looking for an undefined variable, return True, otherwise fail
            try:
                # first we extract the variable name from the error message
                var_name = re.compile(r"'(hostvars\[.+\]|[\w_]+)' is undefined").search(str(e)).groups()[0]
                # next we extract all defined/undefined tests from the conditional string
                def_undef = self.extract_defined_undefined(conditional)
                # then we loop through these, comparing the error variable name against
                # each def/undef test we found above. If there is a match, we determine
                # whether the logic/state mean the variable should exist or not and return
                # the corresponding True/False
                for (du_var, logic, state) in def_undef:
                    # when we compare the var names, normalize quotes because something
                    # like hostvars['foo'] may be tested against hostvars["foo"]
                    if var_name.replace("'", '"') == du_var.replace("'", '"'):
                        # the should exist is a xor test between a negation in the logic portion
                        # against the state (defined or undefined)
                        should_exist = ('not' in logic) != (state == 'defined')
                        if should_exist:
                            return False
                        else:
                            return True
                # as nothing above matched the failed var name, re-raise here to
                # trigger the AnsibleUndefinedVariable exception again below
                raise
            except Exception as new_e:
                raise AnsibleUndefinedVariable("error while evaluating conditional (%s): %s" % (original, e))
