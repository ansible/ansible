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

from ansible._internal._templating._engine import TemplateEngine
from ansible.errors import AnsibleError
from ansible.playbook.attribute import NonInheritableFieldAttribute
from ansible.playbook.base import FieldAttributeBase
from ansible.utils.vars import validate_variable_name


class LoopControl(FieldAttributeBase):

    loop_var = NonInheritableFieldAttribute(isa='string', default='item', always_post_validate=True)
    index_var = NonInheritableFieldAttribute(isa='string', always_post_validate=True)
    label = NonInheritableFieldAttribute(isa='string')
    pause = NonInheritableFieldAttribute(isa='float', default=0, always_post_validate=True)
    extended = NonInheritableFieldAttribute(isa='bool', always_post_validate=True)
    extended_allitems = NonInheritableFieldAttribute(isa='bool', default=True, always_post_validate=True)
    break_when = NonInheritableFieldAttribute(isa='list', default=list, always_post_validate=True)

    def __init__(self):
        super(LoopControl, self).__init__()

    @staticmethod
    def load(data, variable_manager=None, loader=None):
        t = LoopControl()
        return t.load_data(data, variable_manager=variable_manager, loader=loader)

    def post_validate(self, templar: TemplateEngine) -> None:
        super().post_validate(templar)

        try:
            validate_variable_name(self.loop_var)
        except AnsibleError as ex:
            raise AnsibleError("Invalid 'loop_var'.") from ex

        if self.index_var is not None:
            try:
                validate_variable_name(self.index_var)
            except AnsibleError as ex:
                raise AnsibleError("Invalid 'index_var'.") from ex

    def _post_validate_break_when(self, attr, value, templar):
        """
        break_when is evaluated after the execution of the loop is complete,
        and should not be templated during the regular post_validate step.
        """
        return value
