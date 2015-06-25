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
    def process_include_results(results, tqm, iterator, loader):
        included_files = []

        for res in results:
            if res._host in tqm._failed_hosts:
                raise AnsibleError("host is failed, not including files")

            if res._task.action == 'include':
                if res._task.loop:
                    include_results = res._result['results']
                else:
                    include_results = [ res._result ]

                for include_result in include_results:
                    # if the task result was skipped or failed, continue
                    if 'skipped' in include_result and include_result['skipped'] or 'failed' in include_result:
                        continue

                    original_task = iterator.get_original_task(res._host, res._task)
                    if original_task and original_task._role:
                        include_file = loader.path_dwim_relative(original_task._role._role_path, 'tasks', include_result['include'])
                    else:
                        include_file = loader.path_dwim(res._task.args.get('_raw_params'))

                    include_variables = include_result.get('include_variables', dict())
                    if 'item' in include_result:
                        include_variables['item'] = include_result['item']

                    inc_file = IncludedFile(include_file, include_variables, original_task)

                    try:
                        pos = included_files.index(inc_file)
                        inc_file = included_files[pos]
                    except ValueError:
                        included_files.append(inc_file)

                    inc_file.add_host(res._host)

        return included_files
