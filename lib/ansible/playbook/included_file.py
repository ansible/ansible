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

import os

from ansible.playbook.task_include import TaskInclude
from ansible.playbook.role_include import IncludeRole
from ansible.template import Templar

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class IncludedFile:

    def __init__(self, filename, args, task, is_role=False):
        self._filename = filename
        self._args = args
        self._task = task
        self._hosts = []
        self._is_role = is_role

    def add_host(self, host):
        if host not in self._hosts:
            self._hosts.append(host)
            return
        raise ValueError()

    def __eq__(self, other):
        return other._filename == self._filename and other._args == self._args and other._task._parent._uuid == self._task._parent._uuid

    def __repr__(self):
        return "%s (%s): %s" % (self._filename, self._args, self._hosts)

    @staticmethod
    def process_include_results(results, iterator, loader, variable_manager):
        included_files = []
        task_vars_cache = {}

        for res in results:

            original_host = res._host
            original_task = res._task

            if original_task.action in ('include', 'include_tasks', 'include_role'):
                if original_task.loop:
                    if 'results' not in res._result:
                        continue
                    include_results = res._result['results']
                else:
                    include_results = [res._result]

                for include_result in include_results:
                    # if the task result was skipped or failed, continue
                    if 'skipped' in include_result and include_result['skipped'] or 'failed' in include_result and include_result['failed']:
                        continue

                    cache_key = (iterator._play, original_host, original_task)
                    try:
                        task_vars = task_vars_cache[cache_key]
                    except KeyError:
                        task_vars = task_vars_cache[cache_key] = variable_manager.get_vars(play=iterator._play, host=original_host, task=original_task)
                    templar = Templar(loader=loader, variables=task_vars)

                    include_variables = include_result.get('include_variables', dict())
                    loop_var = 'item'
                    index_var = None
                    if original_task.loop_control:
                        loop_var = original_task.loop_control.loop_var
                        index_var = original_task.loop_control.index_var
                    if loop_var in include_result:
                        task_vars[loop_var] = include_variables[loop_var] = include_result[loop_var]
                    if index_var and index_var in include_result:
                        task_vars[index_var] = include_variables[index_var] = include_result[index_var]
                    if '_ansible_item_label' in include_result:
                        task_vars['_ansible_item_label'] = include_variables['_ansible_item_label'] = include_result['_ansible_item_label']
                    if original_task.no_log and '_ansible_no_log' not in include_variables:
                        task_vars['_ansible_no_log'] = include_variables['_ansible_no_log'] = original_task.no_log

                    if original_task.action in ('include', 'include_tasks'):
                        include_file = None
                        if original_task:
                            if original_task.static:
                                continue

                            if original_task._parent:
                                # handle relative includes by walking up the list of parent include
                                # tasks and checking the relative result to see if it exists
                                parent_include = original_task._parent
                                cumulative_path = None
                                while parent_include is not None:
                                    if not isinstance(parent_include, TaskInclude):
                                        parent_include = parent_include._parent
                                        continue
                                    if isinstance(parent_include, IncludeRole):
                                        parent_include_dir = parent_include._role_path
                                    else:
                                        parent_include_dir = os.path.dirname(templar.template(parent_include.args.get('_raw_params')))
                                    if cumulative_path is not None and not os.path.isabs(cumulative_path):
                                        cumulative_path = os.path.join(parent_include_dir, cumulative_path)
                                    else:
                                        cumulative_path = parent_include_dir
                                    include_target = templar.template(include_result['include'])
                                    if original_task._role:
                                        new_basedir = os.path.join(original_task._role._role_path, 'tasks', cumulative_path)
                                        candidates = [loader.path_dwim_relative(original_task._role._role_path, 'tasks', include_target),
                                                      loader.path_dwim_relative(new_basedir, 'tasks', include_target)]
                                        for include_file in candidates:
                                            try:
                                                # may throw OSError
                                                os.stat(include_file)
                                                # or select the task file if it exists
                                                break
                                            except OSError:
                                                pass
                                    else:
                                        include_file = loader.path_dwim_relative(loader.get_basedir(), cumulative_path, include_target)

                                    if os.path.exists(include_file):
                                        break
                                    else:
                                        parent_include = parent_include._parent

                        if include_file is None:
                            if original_task._role:
                                include_target = templar.template(include_result['include'])
                                include_file = loader.path_dwim_relative(original_task._role._role_path, 'tasks', include_target)
                            else:
                                include_file = loader.path_dwim(include_result['include'])

                        include_file = templar.template(include_file)
                        inc_file = IncludedFile(include_file, include_variables, original_task)
                    else:
                        # template the included role's name here
                        role_name = include_variables.pop('name', include_variables.pop('role', None))
                        if role_name is not None:
                            role_name = templar.template(role_name)

                        new_task = original_task.copy()
                        new_task._role_name = role_name
                        for from_arg in new_task.FROM_ARGS:
                            if from_arg in include_variables:
                                from_key = from_arg.replace('_from', '')
                                new_task._from_files[from_key] = templar.template(include_variables.pop(from_arg))

                        inc_file = IncludedFile(role_name, include_variables, new_task, is_role=True)

                    idx = 0
                    orig_inc_file = inc_file
                    while 1:
                        try:
                            pos = included_files[idx:].index(orig_inc_file)
                            # pos is relative to idx since we are slicing
                            # use idx + pos due to relative indexing
                            inc_file = included_files[idx + pos]
                        except ValueError:
                            included_files.append(orig_inc_file)
                            inc_file = orig_inc_file

                        try:
                            inc_file.add_host(original_host)
                        except ValueError:
                            # The host already exists for this include, advance forward, this is a new include
                            idx += pos + 1
                        else:
                            break

        return included_files
