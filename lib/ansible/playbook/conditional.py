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

from __future__ import annotations

import typing as t

from ansible.errors import AnsibleError
from ansible.playbook.attribute import FieldAttribute
from ansible._internal._templating._engine import TemplateEngine
from ansible.utils.display import Display

display = Display()


class Conditional:
    """
    This is a mix-in class, to be used with Base to allow the object
    to be run conditionally when a condition is met or skipped.
    """

    when = FieldAttribute(isa='list', default=list, extend=True, prepend=True)

    def __init__(self, loader=None):
        # when used directly, this class needs a loader, but we want to
        # make sure we don't trample on the existing one if this class
        # is used as a mix-in with a playbook base class
        if not hasattr(self, '_loader'):
            if loader is None:
                raise AnsibleError("a loader must be specified when using Conditional() directly")
            else:
                self._loader = loader
        super().__init__()

    def _validate_when(self, attr, name, value):
        if not isinstance(value, list):
            setattr(self, name, [value])

    def evaluate_conditional(self, templar: TemplateEngine, all_vars: dict[str, t.Any]) -> bool:
        """Loops through the conditionals set on this object, returning False if any of them evaluate as such."""
        return self.evaluate_conditional_with_result(templar, all_vars)[0]

    def evaluate_conditional_with_result(self, templar: TemplateEngine, all_vars: dict[str, t.Any]) -> tuple[bool, t.Optional[str]]:
        """Loops through the conditionals set on this object, returning False if any of them evaluate as such, as well as the condition that was False."""
        # DTFIX-MERGE: need a better API pattern for this (previously directly patching available_variables)
        conditional_templar = TemplateEngine(templar._loader, all_vars)

        for conditional in self.when:
            if not conditional_templar.evaluate_conditional(conditional):
                return False, conditional

        return True, None
