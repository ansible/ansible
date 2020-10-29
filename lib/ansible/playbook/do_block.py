# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2020, Estelle Poulin <dev@inspiredby.es>
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
from ansible.module_utils._text import to_text
from ansible.playbook.task_include import TaskInclude
from ansible.template import Templar
from ansible.utils.display import Display

display = Display()


class DoBlock:

    def __init__(self, block, args, vars, task):
        self._block = block
        self._args = args
        self._vars = vars
        self._task = task
        self._hosts = []

    def add_host(self, host):
        if host not in self._hosts:
            self._hosts.append(host)
            return
        raise ValueError()

    def __eq__(self, other):
        return (other._args == self._args and
                other._vars == self._vars and
                other._task._uuid == self._task._uuid and
                other._task._parent._uuid == self._task._parent._uuid)

    def __repr__(self):
        return "do_block (args=%s vars=%s): %s" % (self._args, self._vars, self._hosts)

    @staticmethod
    def process_do_results(results, iterator, loader, variable_manager):
        do_blocks = []
        task_vars_cache = {}

        for res in results:

            original_host = res._host
            original_task = res._task

            if original_task.action in ('do'):
                if original_task.loop:
                    if 'results' not in res._result:
                        continue
                    do_results = res._result['results']
                else:
                    do_results = [res._result]

                for do_result in do_results:
                    # if the task result was skipped or failed, continue
                    if 'skipped' in do_result and do_result['skipped'] or 'failed' in do_result and do_result['failed']:
                        continue

                    cache_key = (iterator._play, original_host, original_task)
                    try:
                        task_vars = task_vars_cache[cache_key]
                    except KeyError:
                        task_vars = task_vars_cache[cache_key] = variable_manager.get_vars(play=iterator._play, host=original_host, task=original_task)

                    do_args = do_result.get('do_args', dict())
                    special_vars = {}
                    loop_var = do_result.get('ansible_loop_var', 'item')
                    index_var = do_result.get('ansible_index_var')
                    if loop_var in do_result:
                        task_vars[loop_var] = special_vars[loop_var] = do_result[loop_var]
                    if index_var and index_var in do_result:
                        task_vars[index_var] = special_vars[index_var] = do_result[index_var]
                    if '_ansible_item_label' in do_result:
                        task_vars['_ansible_item_label'] = special_vars['_ansible_item_label'] = do_result['_ansible_item_label']
                    if 'ansible_loop' in do_result:
                        task_vars['ansible_loop'] = special_vars['ansible_loop'] = do_result['ansible_loop']
                    if original_task.no_log and '_ansible_no_log' not in do_args:
                        task_vars['_ansible_no_log'] = special_vars['_ansible_no_log'] = original_task.no_log

                    # get search path for this task to pass to lookup plugins that may be used in pathing to
                    # the do block
                    task_vars['ansible_search_path'] = original_task.get_search_path()

                    # ensure basedir is always in (dwim already searches here but we need to display it)
                    if loader.get_basedir() not in task_vars['ansible_search_path']:
                        task_vars['ansible_search_path'].append(loader.get_basedir())

                    do_block = original_task

                    do_blk = DoBlock(do_block, do_args, special_vars, original_task)

                    idx = 0
                    orig_do_blk = do_blk
                    while 1:
                        try:
                            pos = do_blocks[idx:].index(orig_do_blk)
                            # pos is relative to idx since we are slicing
                            # use idx + pos due to relative indexing
                            do_blk = do_blocks[idx + pos]
                        except ValueError:
                            do_blocks.append(orig_do_blk)
                            do_blk = orig_do_blk

                        try:
                            do_blk.add_host(original_host)
                        except ValueError:
                            # The host already exists for this do block, advance forward, this is a new do block
                            idx += pos + 1
                        else:
                            break

        return do_blocks
