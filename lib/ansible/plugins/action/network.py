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
from ansible.module_utils._text import to_text, to_bytes
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

        if config_module and self._task.args.get('backup') and not result.get('failed'):
            self._handle_backup_option(result, task_vars)

        return result

    def _handle_backup_option(self, result, task_vars):

        filename = None
        backup_path = None
        try:
            content = result['__backup__']
        except KeyError:
            raise AnsibleError('Failed while reading configuration backup')

        backup_options = self._task.args.get('backup_options')
        if backup_options:
            filename = backup_options.get('filename')
            backup_path = backup_options.get('dir_path')

        if not backup_path:
            cwd = self._get_working_path()
            backup_path = os.path.join(cwd, 'backup')
        if not filename:
            tstamp = time.strftime("%Y-%m-%d@%H:%M:%S", time.localtime(time.time()))
            filename = '%s_config.%s' % (task_vars['inventory_hostname'], tstamp)

        dest = os.path.join(backup_path, filename)
        backup_path = os.path.expanduser(os.path.expandvars(to_bytes(backup_path, errors='surrogate_or_strict')))

        if not os.path.exists(backup_path):
            os.makedirs(backup_path)

        new_task = self._task.copy()
        for item in self._task.args:
            if not item.startswith('_'):
                new_task.args.pop(item, None)

        new_task.args.update(
            dict(
                content=content,
                dest=dest,
            ),
        )
        copy_action = self._shared_loader_obj.action_loader.get('copy',
                                                                task=new_task,
                                                                connection=self._connection,
                                                                play_context=self._play_context,
                                                                loader=self._loader,
                                                                templar=self._templar,
                                                                shared_loader_obj=self._shared_loader_obj)
        copy_result = copy_action.run(task_vars=task_vars)
        if copy_result.get('failed'):
            result['failed'] = copy_result['failed']
            result['msg'] = copy_result.get('msg')
            return

        result['backup_path'] = copy_result['dest']
        if copy_result.get('changed', False):
            result['changed'] = copy_result['changed']

        if backup_options and backup_options.get('filename'):
            result['date'] = time.strftime('%Y-%m-%d', time.gmtime(os.stat(result['backup_path']).st_ctime))
            result['time'] = time.strftime('%H:%M:%S', time.gmtime(os.stat(result['backup_path']).st_ctime))

        else:
            result['date'] = tstamp.split('@')[0]
            result['time'] = tstamp.split('@')[1]
            result['shortname'] = result['backup_path'][::-1].split('.', 1)[1][::-1]
            result['filename'] = result['backup_path'].split('/')[-1]

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

    def _handle_src_option(self, convert_data=True):
        src = self._task.args.get('src')
        working_path = self._get_working_path()

        if os.path.isabs(src) or urlsplit('src').scheme:
            source = src
        else:
            source = self._loader.path_dwim_relative(working_path, 'templates', src)
            if not source:
                source = self._loader.path_dwim_relative(working_path, src)

        if not os.path.exists(source):
            raise AnsibleError('path specified in src not found')

        try:
            with open(source, 'r') as f:
                template_data = to_text(f.read())
        except IOError as e:
            raise AnsibleError("unable to load src file {0}, I/O error({1}): {2}".format(source, e.errno, e.strerror))

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
