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

from ansible.errors import AnsibleParserError
from ansible.playbook.attribute import FieldAttribute
from ansible.playbook.block import Block
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

    BASE = frozenset(('file', '_raw_params'))  # directly assigned
    OTHER_ARGS = frozenset(('apply',))  # assigned to matching property
    VALID_ARGS = BASE.union(OTHER_ARGS)  # all valid args

    # =================================================================================
    # ATTRIBUTES

    _static = FieldAttribute(isa='bool', default=None)

    def __init__(self, block=None, role=None, task_include=None):
        super(TaskInclude, self).__init__(block=block, role=role, task_include=task_include)
        self.statically_loaded = False

    @staticmethod
    def load(data, block=None, role=None, task_include=None, variable_manager=None, loader=None):
        ti = TaskInclude(block=block, role=role, task_include=task_include)
        task = ti.load_data(data, variable_manager=variable_manager, loader=loader)

        # Validate options
        my_arg_names = frozenset(task.args.keys())

        # validate bad args, otherwise we silently ignore
        bad_opts = my_arg_names.difference(TaskInclude.VALID_ARGS)
        if bad_opts and task.action in ('include_tasks', 'import_tasks'):
            raise AnsibleParserError('Invalid options for %s: %s' % (task.action, ','.join(list(bad_opts))), obj=data)

        if not task.args.get('_raw_params'):
            task.args['_raw_params'] = task.args.pop('file')

        apply_attrs = task.args.pop('apply', {})
        if apply_attrs and task.action != 'include_tasks':
            raise AnsibleParserError('Invalid options for %s: apply' % task.action, obj=data)
        elif apply_attrs:
            apply_attrs['block'] = []
            p_block = Block.load(
                apply_attrs,
                play=block._play,
                parent_block=block,
                role=role,
                task_include=task_include,
                use_handlers=block._use_handlers,
                variable_manager=variable_manager,
                loader=loader,
            )
            task._parent = p_block

        return task

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
