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

from ansible.errors import *
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

    def evaluate_conditional(self, all_vars):
        '''
        Loops through the conditionals set on this object, returning
        False if any of them evaluate as such.
        '''

        templar = Templar(loader=self._loader, variables=all_vars, fail_on_undefined=False)
        for conditional in self.when:
            if not self._check_conditional(conditional, templar, all_vars):
                return False
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

        if conditional in all_vars and '-' not in unicode(all_vars[conditional]):
            conditional = all_vars[conditional]

        conditional = templar.template(conditional)
        if not isinstance(conditional, basestring) or conditional == "":
            return conditional

        # a Jinja2 evaluation that results in something Python can eval!
        presented = "{%% if %s %%} True {%% else %%} False {%% endif %%}" % conditional
        conditional = templar.template(presented)

        val = conditional.strip()
        if val == presented:
            # the templating failed, meaning most likely a
            # variable was undefined. If we happened to be
            # looking for an undefined variable, return True,
            # otherwise fail
            if "is undefined" in original:
                return True
            elif "is defined" in original:
                return False
            else:
                raise AnsibleError("error while evaluating conditional: %s (%s)" % (original, presented))
        elif val == "True":
            return True
        elif val == "False":
            return False
        else:
            raise AnsibleError("unable to evaluate conditional: %s" % original)

