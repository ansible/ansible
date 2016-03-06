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

from ansible.errors import AnsibleError
from ansible.template import Templar

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

class IncludedFile:

    def __init__(self, filename, args, task):
        self._filename = filename
        self._args     = args
        self._task     = task
        self._hosts    = []

    def add_host(self, host):
        if host not in self._hosts:
            self._hosts.append(host)

    def __eq__(self, other):
        return other._filename == self._filename and other._args == self._args

    def __repr__(self):
        return "%s (%s): %s" % (self._filename, self._args, self._hosts)

    @staticmethod
    def process_include_results(results, tqm, iterator, inventory, loader, variable_manager):
        included_files = []

        def get_original_host(host):
            if host.name in inventory._hosts_cache:
                return inventory._hosts_cache[host.name]
            else:
                return inventory.get_host(host.name)

        for res in results:

            if res._task.action == 'include':
                if res._task.loop:
                    if 'results' not in res._result:
                        continue
                    include_results = res._result['results']
                else:
                    include_results = [ res._result ]

                for include_result in include_results:
                    # if the task result was skipped or failed, continue
                    if 'skipped' in include_result and include_result['skipped'] or 'failed' in include_result:
                        continue

                    original_host = get_original_host(res._host)
                    original_task = iterator.get_original_task(original_host, res._task)

                    task_vars = variable_manager.get_vars(loader=loader, play=iterator._play, host=original_host, task=original_task)
                    templar = Templar(loader=loader, variables=task_vars)

                    include_variables = include_result.get('include_variables', dict())
                    if 'item' in include_result:
                        task_vars['item'] = include_variables['item'] = include_result['item']

                    if original_task:
                        if original_task._task_include:
                            # handle relative includes by walking up the list of parent include
                            # tasks and checking the relative result to see if it exists
                            parent_include = original_task._task_include
                            cumulative_path = None
                            while parent_include is not None:
                                parent_include_dir = templar.template(os.path.dirname(parent_include.args.get('_raw_params')))
                                if cumulative_path is None:
                                    cumulative_path = parent_include_dir
                                elif not os.path.isabs(cumulative_path):
                                    cumulative_path = os.path.join(parent_include_dir, cumulative_path)
                                include_target = templar.template(include_result['include'])
                                if original_task._role:
                                    new_basedir = os.path.join(original_task._role._role_path, 'tasks', cumulative_path)
                                    include_file = loader.path_dwim_relative(new_basedir, 'tasks', include_target)
                                else:
                                    include_file = loader.path_dwim_relative(loader.get_basedir(), cumulative_path, include_target)

                                if os.path.exists(include_file):
                                    break
                                else:
                                    parent_include = parent_include._task_include
                        elif original_task._role:
                            include_target = templar.template(include_result['include'])
                            include_file = loader.path_dwim_relative(original_task._role._role_path, 'tasks', include_target)
                        else:
                            include_file = loader.path_dwim(include_result['include'])
                    else:
                        include_file = loader.path_dwim(include_result['include'])

                    include_file = templar.template(include_file)
                    inc_file = IncludedFile(include_file, include_variables, original_task)

                    try:
                        pos = included_files.index(inc_file)
                        inc_file = included_files[pos]
                    except ValueError:
                        included_files.append(inc_file)

                    inc_file.add_host(original_host)

        return included_files
