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
from ansible.playbook.task import Task

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

__all__ = ['TaskInclude']


class TaskInclude(Task):

    """
    A task include is derived from a regular task to handle the special
    circumstances related to the `- include: ...` task.
    """

    # =================================================================================
    # ATTRIBUTES

    _static = FieldAttribute(isa='bool', default=None)

    def __init__(self, block=None, role=None, task_include=None):
        super(TaskInclude, self).__init__(block=block, role=role, task_include=task_include)
        self.statically_loaded = False

    @staticmethod
    def load(data, block=None, role=None, task_include=None, variable_manager=None, loader=None):
        t = TaskInclude(block=block, role=role, task_include=task_include)
        return t.load_data(data, variable_manager=variable_manager, loader=loader)

    def copy(self, exclude_parent=False, exclude_tasks=False):
        new_me = super(TaskInclude, self).copy(exclude_parent=exclude_parent, exclude_tasks=exclude_tasks)
        new_me.statically_loaded = self.statically_loaded
        return new_me

    def get_vars(self):
        '''
        We override the parent Task() classes get_vars here because
        we need to include the args of the include into the vars as
        they are params to the included tasks. But ONLY for 'include'
        '''
        if self.action != 'include':
            all_vars = super(TaskInclude, self).get_vars()
        else:
            all_vars = dict()
            if self._parent:
                all_vars.update(self._parent.get_vars())

            all_vars.update(self.vars)
            all_vars.update(self.args)

            if 'tags' in all_vars:
                del all_vars['tags']
            if 'when' in all_vars:
                del all_vars['when']

        return all_vars
