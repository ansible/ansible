# (c) 2018, Ansible Inc,
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import copy
import os
import time
import uuid
import hashlib
import sys

from ansible.module_utils._text import to_text, to_bytes
from ansible.module_utils.connection import Connection
from ansible.errors import AnsibleError
from ansible.plugins.action import ActionBase
from ansible.module_utils.six.moves.urllib.parse import urlsplit

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        changed = True
        socket_path = None
        play_context = copy.deepcopy(self._play_context)
        play_context.network_os = self._get_network_os(task_vars)

        result = super(ActionModule, self).run(task_vars=task_vars)

        if play_context.connection != 'network_cli':
            # It is supported only with network_cli
            result['failed'] = True
            result['msg'] = ('please use network_cli connection type for net_put module')
            return result

        try:
            src = self._task.args.get('src')
        except KeyError as exc:
            return {'failed': True, 'msg': 'missing required argument: %s' % exc}

        src_file_path_name = src

        # Get destination file if specified
        dest = self._task.args.get('dest')

        # Get proto
        proto = self._task.args.get('protocol')
        if proto is None:
            proto = 'scp'

        # Get mode if set
        mode = self._task.args.get('mode')
        if mode is None:
            mode = 'binary'

        if mode == 'text':
            try:
                self._handle_template()
            except ValueError as exc:
                return dict(failed=True, msg=to_text(exc))

            # Now src has resolved file write to disk in current diectory for scp
            src = self._task.args.get('src')
            filename = str(uuid.uuid4())
            cwd = self._loader.get_basedir()
            output_file = os.path.join(cwd, filename)
            try:
                with open(output_file, 'wb') as f:
                    f.write(to_bytes(src, encoding='utf-8'))
            except Exception:
                os.remove(output_file)
                raise
        else:
            try:
                output_file = self._get_binary_src_file(src)
            except ValueError as exc:
                return dict(failed=True, msg=to_text(exc))

        if socket_path is None:
            socket_path = self._connection.socket_path

        conn = Connection(socket_path)
        sock_timeout = conn.get_option('persistent_command_timeout')

        if dest is None:
            dest = src_file_path_name

        try:
            changed = self._handle_existing_file(conn, output_file, dest, proto, sock_timeout)
            if changed is False:
                result['changed'] = False
                result['destination'] = dest
                return result
        except Exception as exc:
            result['msg'] = ('Warning: Exc %s idempotency check failed. Check'
                             'dest' % exc)

        try:
            out = conn.copy_file(
                source=output_file, destination=dest,
                proto=proto, timeout=sock_timeout
            )
        except Exception as exc:
            if to_text(exc) == "No response from server":
                if play_context.network_os == 'iosxr':
                    # IOSXR sometimes closes socket prematurely after completion
                    # of file transfer
                    result['msg'] = 'Warning: iosxr scp server pre close issue. Please check dest'
            else:
                result['failed'] = True
                result['msg'] = ('Exception received : %s' % exc)

        if mode == 'text':
            # Cleanup tmp file expanded wih ansible vars
            os.remove(output_file)

        result['changed'] = changed
        result['destination'] = dest
        return result

    def _handle_existing_file(self, conn, source, dest, proto, timeout):
        cwd = self._loader.get_basedir()
        filename = str(uuid.uuid4())
        source_file = os.path.join(cwd, filename)
        try:
            out = conn.get_file(
                source=dest, destination=source_file,
                proto=proto, timeout=timeout
            )
        except Exception as exc:
            if (to_text(exc)).find("No such file or directory") > 0:
                return True
            else:
                try:
                    os.remove(source_file)
                except OSError as osex:
                    raise Exception(osex)

        try:
            with open(source, 'r') as f:
                new_content = f.read()
            with open(source_file, 'r') as f:
                old_content = f.read()
        except (IOError, OSError) as ioexc:
            raise IOError(ioexc)

        sha1 = hashlib.sha1()
        old_content_b = to_bytes(old_content, errors='surrogate_or_strict')
        sha1.update(old_content_b)
        checksum_old = sha1.digest()

        sha1 = hashlib.sha1()
        new_content_b = to_bytes(new_content, errors='surrogate_or_strict')
        sha1.update(new_content_b)
        checksum_new = sha1.digest()
        os.remove(source_file)
        if checksum_old == checksum_new:
            return False
        else:
            return True

    def _get_working_path(self):
        cwd = self._loader.get_basedir()
        if self._task._role is not None:
            cwd = self._task._role._role_path
        return cwd

    def _handle_template(self):
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
        self._task.args['src'] = self._templar.template(
            template_data,
            convert_data=False
        )

        return dict(failed=False, msg='successfully loaded file')

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
            raise AnsibleError('ansible_network_os must be specified on this host to use platform agnostic modules')

        return network_os

    def _get_binary_src_file(self, src):
        working_path = self._get_working_path()

        if os.path.isabs(src) or urlsplit('src').scheme:
            source = src
        else:
            source = self._loader.path_dwim_relative(working_path, 'templates', src)
            if not source:
                source = self._loader.path_dwim_relative(working_path, src)

        if not os.path.exists(source):
            raise ValueError('path specified in src not found')

        return source
