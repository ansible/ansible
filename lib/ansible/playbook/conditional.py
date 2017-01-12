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

from jinja2.exceptions import UndefinedError

from ansible.compat.six import text_type
from ansible.errors import AnsibleError, AnsibleUndefinedVariable
from ansible.playbook.attribute import FieldAttribute
from ansible.template import Templar
from ansible.module_utils._text import to_native

LOOKUP_REGEX = re.compile(r'lookup\s*\(')
VALID_VAR_REGEX = re.compile("^[_A-Za-z][_a-zA-Z0-9]*$")

class Conditional:

    '''
    This is a mix-in class, to be used with Base to allow the object
    to be run conditionally when a condition is met or skipped.
    '''

    _when = FieldAttribute(isa='list', default=[])

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
            setattr(self, name, [ value ])

    def _get_attr_when(self):
        '''
        Override for the 'tags' getattr fetcher, used from Base.
        '''
        when = self._attributes['when']
        if when is None:
            when = []
        if hasattr(self, '_get_parent_attribute'):
            when = self._get_parent_attribute('when', extend=True, prepend=True)
        return when

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
            raise AnsibleError("The conditional check '%s' failed. The error was: %s" % (to_native(conditional), to_native(e)), obj=ds)

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

            # now we generated the "presented" string, which is a jinja2 if/else block
            # used to evaluate the conditional. First, we do some low-level jinja2 parsing
            # involving the AST format of the statement to ensure we don't do anything
            # unsafe (using the disable_lookup flag above)
            e = templar.environment.overlay()
            e.filters.update(templar._get_filters())
            e.tests.update(templar._get_tests())

            presented = "{%% if %s %%} True {%% else %%} False {%% endif %%}" % conditional
            res = e._parse(presented, None, None)
            res = e._generate(res, None, None, defer_init=True)
            parsed = ast.parse(res, mode='exec')

            class CleansingNodeVisitor(ast.NodeVisitor):
                def generic_visit(self, node, inside_call=False):
                    if isinstance(node, ast.Call):
                        inside_call = True
                    elif isinstance(node, ast.Str):
                        # calling things with a dunder is generally bad at this point...
                        if inside_call and disable_lookups and node.s.startswith("__"):
                            raise AnsibleError("Invalid access found in the presented conditional: '%s'" % conditional)
                    # iterate over all child nodes
                    for child_node in ast.iter_child_nodes(node):
                        self.generic_visit(child_node, inside_call=inside_call)

            cnv = CleansingNodeVisitor()
            cnv.visit(parsed)

            # and finally we templated the presented string and look at the resulting string
            val = templar.template(presented, disable_lookups=disable_lookups).strip()
            if val == "True":
                return True
            elif val == "False":
                return False
            else:
                raise AnsibleError("unable to evaluate conditional: %s" % original)
        except (AnsibleUndefinedVariable, UndefinedError) as e:
            # the templating failed, meaning most likely a
            # variable was undefined. If we happened to be
            # looking for an undefined variable, return True,
            # otherwise fail
            if "is undefined" in original or "is not defined" in original or "not is defined" in original:
                return True
            elif "is defined" in original or "is not undefined" in original or "not is undefined" in original:
                return False
            else:
                raise AnsibleUndefinedVariable("error while evaluating conditional (%s): %s" % (original, e))

