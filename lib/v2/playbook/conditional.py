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

import v2.config as C
from v2.utils import template
from v2.utils import list_union

class Conditional(object):
    def __init__(self, basedir, conditionals=[]):
        self.basedir = basedir
        self.conditionals = conditionals

    def push(self, conditional):
        if conditional not in self.conditionals:
            self.conditionals.append(conditional)

    def get_conditionals(self):
        # return a full slice to make sure the reference
        # doesn't get mangled by other users of the result
        return self.conditionals[:]

    def merge(self, conditional):
        if isinstance(conditional, basestring):
            conditional = Conditional(self.basedir, [conditional])
        elif isinstance(conditional, list):
            conditional = Conditional(self.basedir, conditional)
        elif not isinstance(conditional, Conditional):
            raise AnsibleError('expected a Conditional() class, instead got a %s' % type(conditional))
        self.conditionals = list_union(self.conditionals, conditional.get_conditonals())

    def evaluate(self, inject):
        for conditional in self.conditional:
            if not self._do_evaluate(conditional, inject):
                return False
        return True

    def _do_evaluate(self, conditional, inject):
        # allow variable names
        if conditional in inject and '-' not in str(inject[conditional]):
            conditional = inject[conditional]
        conditional = template.template(self.basedir, conditional, inject, fail_on_undefined=C.fail_on_undefined)
        original = str(conditional).replace("jinja2_compare ","")
        # a Jinja2 evaluation that results in something Python can eval!
        presented = "{%% if %s %%} True {%% else %%} False {%% endif %%}" % conditional
        conditional = template.template(self.basedir, presented, inject)
        val = conditional.strip()
        if val == presented:
            # the templating failed, meaning most likely a
            # variable was undefined. If we happened to be
            # looking for an undefined variable, return True,
            # otherwise fail
            if "is undefined" in conditional:
                return True
            elif "is defined" in conditional:
                return False
            else:
                raise errors.AnsibleError("error while evaluating conditional: %s" % original)
        elif val == "True":
            return True
        elif val == "False":
            return False
        else:
            raise errors.AnsibleError("unable to evaluate conditional: %s" % original)

