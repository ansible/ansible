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
import re
import uuid
import hashlib

from ansible.module_utils._text import to_text, to_bytes
from ansible.module_utils.connection import Connection
from ansible.plugins.action.network import ActionModule as NetworkActionModule
from ansible.module_utils.six.moves.urllib.parse import urlsplit
from ansible.utils.display import Display

display = Display()


class ActionModule(NetworkActionModule):

    def run(self, tmp=None, task_vars=None):
        socket_path = None
        play_context = copy.deepcopy(self._play_context)
        play_context.network_os = self._get_network_os(task_vars)

        result = super(ActionModule, self).run(task_vars=task_vars)

        if play_context.connection != 'network_cli':
            # It is supported only with network_cli
            result['failed'] = True
            result['msg'] = ('please use network_cli connection type for net_get module')
            return result

        try:
            src = self._task.args.get('src')
        except KeyError as exc:
            return {'failed': True, 'msg': 'missing required argument: %s' % exc}

        # Get destination file if specified
        dest = self._task.args.get('dest')

        if dest is None:
            dest = self._get_default_dest(src)
        else:
            dest = self._handle_dest_path(dest)

        # Get proto
        proto = self._task.args.get('protocol')
        if proto is None:
            proto = 'scp'

        sock_timeout = play_context.timeout

        if socket_path is None:
            socket_path = self._connection.socket_path

        conn = Connection(socket_path)

        try:
            changed = self._handle_existing_file(conn, src, dest, proto, sock_timeout)
            if changed is False:
                result['changed'] = False
                result['destination'] = dest
                return result
        except Exception as exc:
            result['msg'] = ('Warning: exception %s idempotency check failed. Check '
                             'dest' % exc)

        try:
            out = conn.get_file(
                source=src, destination=dest,
                proto=proto, timeout=sock_timeout
            )
        except Exception as exc:
            result['failed'] = True
            result['msg'] = ('Exception received : %s' % exc)

        result['changed'] = True
        result['destination'] = dest
        return result

    def _handle_dest_path(self, dest):
        working_path = self._get_working_path()

        if os.path.isabs(dest) or urlsplit('dest').scheme:
            dst = dest
        else:
            dst = self._loader.path_dwim_relative(working_path, '', dest)

        return dst

    def _get_src_filename_from_path(self, src_path):
        filename_list = re.split('/|:', src_path)
        return filename_list[-1]

    def _get_default_dest(self, src_path):
        dest_path = self._get_working_path()
        src_fname = self._get_src_filename_from_path(src_path)
        filename = '%s/%s' % (dest_path, src_fname)
        return filename

    def _handle_existing_file(self, conn, source, dest, proto, timeout):
        if not os.path.exists(dest):
            return True
        cwd = self._loader.get_basedir()
        filename = str(uuid.uuid4())
        tmp_dest_file = os.path.join(cwd, filename)
        try:
            out = conn.get_file(
                source=source, destination=tmp_dest_file,
                proto=proto, timeout=timeout
            )
        except Exception as exc:
            os.remove(tmp_dest_file)
            raise Exception(exc)

        try:
            with open(tmp_dest_file, 'r') as f:
                new_content = f.read()
            with open(dest, 'r') as f:
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
        os.remove(tmp_dest_file)
        if checksum_old == checksum_new:
            return False
        else:
            return True
