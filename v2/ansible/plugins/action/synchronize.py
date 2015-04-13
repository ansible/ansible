#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012-2013, Timothy Appnel <tim@appnel.com>
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

import os.path

from ansible.plugins.action import ActionBase
from ansible.utils.boolean import boolean

class ActionModule(ActionBase):

    def _get_absolute_path(self, path):
        if self._task._role is not None:
            original_path = path
            path = self._loader.path_dwim_relative(self._task._role._role_path, 'files', path)
            if original_path and original_path[-1] == '/' and path[-1] != '/':
                # make sure the dwim'd path ends in a trailing "/"
                # if the original path did
                path += '/'

        return path

    def _process_origin(self, host, path, user):

        if not host in ['127.0.0.1', 'localhost']:
            if user:
                return '%s@%s:%s' % (user, host, path)
            else:
                return '%s:%s' % (host, path)
        else:
            if not ':' in path:
                if not path.startswith('/'):
                    path = self._get_absolute_path(path=path)
            return path

    def _process_remote(self, host, task, path, user):
        transport = self._connection_info.connection
        return_data = None
        if not host in ['127.0.0.1', 'localhost'] or transport != "local":
            if user:
                return_data = '%s@%s:%s' % (user, host, path)
            else:
                return_data = '%s:%s' % (host, path)
        else:
            return_data = path

        if not ':' in return_data:
            if not return_data.startswith('/'):
                return_data = self._get_absolute_path(path=return_data)

        return return_data

    def run(self, tmp=None, task_vars=dict()):
        ''' generates params and passes them on to the rsync module '''

        original_transport   = task_vars.get('ansible_connection', self._connection_info.connection)
        transport_overridden = False
        if task_vars.get('delegate_to') is None:
            task_vars['delegate_to'] = '127.0.0.1'
            # IF original transport is not local, override transport and disable sudo.
            if original_transport != 'local':
                task_vars['ansible_connection'] = 'local'
                transport_overridden = True
                self.runner.sudo = False

        src  = self._task.args.get('src', None)
        dest = self._task.args.get('dest', None)

        # FIXME: this doesn't appear to be used anywhere?
        local_rsync_path = task_vars.get('ansible_rsync_path')

        # from the perspective of the rsync call the delegate is the localhost
        src_host  = '127.0.0.1'
        dest_host = task_vars.get('ansible_ssh_host', task_vars.get('inventory_hostname'))

        # allow ansible_ssh_host to be templated
        dest_is_local = dest_host in ['127.0.0.1', 'localhost']

        # CHECK FOR NON-DEFAULT SSH PORT
        dest_port = self._task.args.get('dest_port')
        inv_port  = task_vars.get('ansible_ssh_port', task_vars.get('inventory_hostname'))
        if inv_port != dest_port and inv_port != task_vars.get('inventory_hostname'):
            dest_port = inv_port

        # edge case: explicit delegate and dest_host are the same
        if dest_host == task_vars.get('delegate_to'):
            dest_host = '127.0.0.1'

        # SWITCH SRC AND DEST PER MODE
        if self._task.args.get('mode', 'push') == 'pull':
            (dest_host, src_host) = (src_host, dest_host)

        # CHECK DELEGATE HOST INFO
        use_delegate = False
        # FIXME: not sure if this is in connection info yet or not...
        #if conn.delegate != conn.host:
        #    if 'hostvars' in task_vars:
        #        if conn.delegate in task_vars['hostvars'] and original_transport != 'local':
        #            # use a delegate host instead of localhost
        #            use_delegate = True

        # COMPARE DELEGATE, HOST AND TRANSPORT                             
        process_args = False
        if not dest_host is src_host and original_transport != 'local':
            # interpret and task_vars remote host info into src or dest
            process_args = True

        # MUNGE SRC AND DEST PER REMOTE_HOST INFO
        if process_args or use_delegate:

            user = None
            if boolean(task_vars.get('set_remote_user', 'yes')):
                if use_delegate:
                    user = task_vars['hostvars'][conn.delegate].get('ansible_ssh_user')

                if not use_delegate or not user:
                    user = task_vars.get('ansible_ssh_user', self.runner.remote_user)
                
            if use_delegate:
                # FIXME
                private_key = task_vars.get('ansible_ssh_private_key_file', self.runner.private_key_file)
            else:
                private_key = task_vars.get('ansible_ssh_private_key_file', self.runner.private_key_file)

            if private_key is not None:
                private_key = os.path.expanduser(private_key)
                
            # use the mode to define src and dest's url
            if self._task.args.get('mode', 'push') == 'pull':
                # src is a remote path: <user>@<host>, dest is a local path
                src  = self._process_remote(src_host, src, user)
                dest = self._process_origin(dest_host, dest, user)
            else:
                # src is a local path, dest is a remote path: <user>@<host>
                src  = self._process_origin(src_host, src, user)
                dest = self._process_remote(dest_host, dest, user)

        # Allow custom rsync path argument.
        rsync_path = self._task.args.get('rsync_path', None)

        # If no rsync_path is set, sudo was originally set, and dest is remote then add 'sudo rsync' argument.
        if not rsync_path and transport_overridden and self._connection_info.become and self._connection_info.become_method == 'sudo' and not dest_is_local:
            rsync_path = 'sudo rsync'

        # make sure rsync path is quoted.
        if rsync_path:
            self._task.args['rsync_path'] = '"%s"' % rsync_path

        # run the module and store the result
        result = self._execute_module('synchronize')

        return result

