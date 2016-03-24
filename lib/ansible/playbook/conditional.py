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

from jinja2.exceptions import UndefinedError

from ansible.compat.six import text_type
from ansible.errors import AnsibleError, AnsibleUndefinedVariable
from ansible.playbook.attribute import FieldAttribute
from ansible.template import Templar

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
            for conditional in self.when:
                if not self._check_conditional(conditional, templar, all_vars):
                    return False
        except Exception as e:
            raise AnsibleError("The conditional check '%s' failed. The error was: %s" % (conditional, e), obj=ds)

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

        if conditional in all_vars and '-' not in text_type(all_vars[conditional]):
            conditional = all_vars[conditional]

        # make sure the templar is using the variables specified with this method
        templar.set_available_variables(variables=all_vars)

        try:
            conditional = templar.template(conditional)
            if not isinstance(conditional, text_type) or conditional == "":
                return conditional

            # a Jinja2 evaluation that results in something Python can eval!
            presented = "{%% if %s %%} True {%% else %%} False {%% endif %%}" % conditional
            conditional = templar.template(presented)
            val = conditional.strip()
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
            if "is undefined" in original:
                return True
            elif "is defined" in original:
                return False
            else:
                raise AnsibleError("error while evaluating conditional (%s): %s" % (original, e))

