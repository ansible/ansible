#
# (c) 2018 Red Hat Inc.
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
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import time
import glob
import re

from ansible.errors import AnsibleError
from ansible.module_utils._text import to_text
from ansible.module_utils.six.moves.urllib.parse import urlsplit
from ansible.plugins.action.normal import ActionModule as _ActionModule
from ansible.utils.display import Display

display = Display()

PRIVATE_KEYS_RE = re.compile('__.+__')


class ActionModule(_ActionModule):

    def run(self, task_vars=None):
        config_module = hasattr(self, '_config_module') and self._config_module
        if config_module and self._task.args.get('src'):
            self._handle_src_option()

        result = super(ActionModule, self).run(task_vars=task_vars)

        if config_module and self._task.args.get('backup'):
            self._handle_backup_option(result, task_vars['inventory_hostname'], result.get('__backup__', False))

        return result

    def _handle_src_option(self):
        try:
            self._handle_template()
        except ValueError as exc:
            return dict(failed=True, msg=to_text(exc))

    def _handle_backup_option(self, result, hostname, backup):
        if backup:
            # User requested backup and no error occurred in module.
            # NOTE: If there is a parameter error, _backup key may not be in results.
            filepath = self._write_backup(hostname, backup)
            result['backup_path'] = filepath

        # strip out any keys that have two leading and two trailing
        # underscore characters
        for key in list(result.keys()):
            if PRIVATE_KEYS_RE.match(key):
                del result[key]

    def _get_working_path(self):
        cwd = self._loader.get_basedir()
        if self._task._role is not None:
            cwd = self._task._role._role_path
        return cwd

    def _write_backup(self, host, contents, encoding='utf-8'):
        cwd = self._get_working_path()

        backup_path = os.path.join(cwd, 'backup')
        if not os.path.exists(backup_path):
            os.mkdir(backup_path)
        for existing_backup in glob.glob('%s/%s_config.*' % (backup_path, host)):
            os.remove(existing_backup)
        tstamp = time.strftime("%Y-%m-%d@%H:%M:%S", time.localtime(time.time()))
        filename = '%s/%s_config.%s' % (backup_path, host, tstamp)
        open(filename, 'w').write(to_text(contents, encoding=encoding))

        return filename

    def _handle_template(self, convert_data=True):
        src = self._task.args.get('src')
        working_path = self._get_working_path()

        if os.path.isabs(src) or urlsplit('src').scheme:
            source = src
        else:
            source = self._loader.path_dwim_relative(working_path, 'templates', src)
            if not source:
                source = self._loader.path_dwim_relative(working_path, src)

        if not os.path.exists(source):
            raise ValueError('path specified in src not found')

        try:
            with open(source, 'r') as f:
                template_data = to_text(f.read())
        except IOError:
            return dict(failed=True, msg='unable to load src file')

        # Create a template search path in the following order:
        # [working_path, self_role_path, dependent_role_paths, dirname(source)]
        searchpath = [working_path]
        if self._task._role is not None:
            searchpath.append(self._task._role._role_path)
            if hasattr(self._task, "_block:"):
                dep_chain = self._task._block.get_dep_chain()
                if dep_chain is not None:
                    for role in dep_chain:
                        searchpath.append(role._role_path)
        searchpath.append(os.path.dirname(source))
        self._templar.environment.loader.searchpath = searchpath
        self._task.args['src'] = self._templar.template(template_data, convert_data=convert_data)

    def _get_network_os(self, task_vars):
        if 'network_os' in self._task.args and self._task.args['network_os']:
            display.vvvv('Getting network OS from task argument')
            network_os = self._task.args['network_os']
        elif self._play_context.network_os:
            display.vvvv('Getting network OS from inventory')
            network_os = self._play_context.network_os
        elif 'network_os' in task_vars.get('ansible_facts', {}) and task_vars['ansible_facts']['network_os']:
            display.vvvv('Getting network OS from fact')
            network_os = task_vars['ansible_facts']['network_os']
        else:
            raise AnsibleError('ansible_network_os must be specified on this host')

        return network_os
