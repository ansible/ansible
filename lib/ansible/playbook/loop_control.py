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

from ansible.playbook.attribute import FieldAttribute
from ansible.playbook.base import FieldAttributeBase


class LoopControl(FieldAttributeBase):

    _loop_var = FieldAttribute(isa='str', default='item', priority=10)
    _index_var = FieldAttribute(isa='str')
    _label = FieldAttribute(isa='str', priority=5)
    _pause = FieldAttribute(isa='float', default=0)
    _extended = FieldAttribute(isa='bool', default=False)

    def __init__(self):
        super(LoopControl, self).__init__()

    @staticmethod
    def load(data, variable_manager=None, loader=None):
        t = LoopControl()
        return t.load_data(data, variable_manager=variable_manager, loader=loader)

    def post_validate(self, templar):
        '''
        Override of base class post_validate, to also do final validation
        '''
        self.validate()

        super(LoopControl, self).post_validate(templar)

    def _validate_label(self, attr, name, value):
        ''' default to loop var '''
        if value is None:
            setattr(self, name, '{{%s}}' % self.loop_var)
