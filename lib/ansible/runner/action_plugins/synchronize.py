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

import os.path

from ansible import utils
from ansible.runner.return_data import ReturnData
import ansible.utils.template as template

class ActionModule(object):

    def __init__(self, runner):
        self.runner = runner
        self.inject = None

    def _get_absolute_path(self, path=None):
        if 'vars' in self.inject:
            if '_original_file' in self.inject['vars']:
                # roles
                original_path = path
                path = utils.path_dwim_relative(self.inject['_original_file'], 'files', path, self.runner.basedir)
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

    def _process_remote(self, host, path, user):
        transport = self.runner.transport
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

    def setup(self, module_name, inject):
        ''' Always default to localhost as delegate if None defined '''
   
        self.inject = inject
    
        # Store original transport and sudo values.
        self.original_transport = inject.get('ansible_connection', self.runner.transport)
        self.original_become = self.runner.become
        self.transport_overridden = False

        if inject.get('delegate_to') is None:
            inject['delegate_to'] = '127.0.0.1'
            # IF original transport is not local, override transport and disable sudo.
            if self.original_transport != 'local':
                inject['ansible_connection'] = 'local'
                self.transport_overridden = True
                self.runner.become = False

    def run(self, conn, tmp, module_name, module_args,
        inject, complex_args=None, **kwargs):

        ''' generates params and passes them on to the rsync module '''

        self.inject = inject

        # load up options
        options = {}
        if complex_args:
            options.update(complex_args)
        options.update(utils.parse_kv(module_args))

        src = options.get('src', None)
        dest = options.get('dest', None)

        src = template.template(self.runner.basedir, src, inject)
        dest = template.template(self.runner.basedir, dest, inject)

        try:
            options['local_rsync_path'] = inject['ansible_rsync_path']
        except KeyError:
            pass

        # from the perspective of the rsync call the delegate is the localhost
        src_host = '127.0.0.1'
        dest_host = inject.get('ansible_ssh_host', inject['inventory_hostname'])

        # allow ansible_ssh_host to be templated
        dest_host = template.template(self.runner.basedir, dest_host, inject, fail_on_undefined=True)
        dest_is_local = dest_host in ['127.0.0.1', 'localhost']

        # CHECK FOR NON-DEFAULT SSH PORT
        dest_port = options.get('dest_port')
        inv_port = inject.get('ansible_ssh_port', inject['inventory_hostname'])
        if inv_port != dest_port and inv_port != inject['inventory_hostname']:
            options['dest_port'] = inv_port

        # edge case: explicit delegate and dest_host are the same
        if dest_host == inject['delegate_to']:
            dest_host = '127.0.0.1'

        # SWITCH SRC AND DEST PER MODE
        if options.get('mode', 'push') == 'pull':
            (dest_host, src_host) = (src_host, dest_host)

        # CHECK DELEGATE HOST INFO
        use_delegate = False
        if conn.delegate != conn.host:
            if 'hostvars' in inject:
                if conn.delegate in inject['hostvars'] and self.original_transport != 'local':
                    # use a delegate host instead of localhost
                    use_delegate = True

        # COMPARE DELEGATE, HOST AND TRANSPORT
        process_args = False
        if not dest_host is src_host and self.original_transport != 'local':
            # interpret and inject remote host info into src or dest
            process_args = True

        # MUNGE SRC AND DEST PER REMOTE_HOST INFO
        if process_args or use_delegate:

            user = None
            if utils.boolean(options.get('set_remote_user', 'yes')):
                if use_delegate:
                    user = inject['hostvars'][conn.delegate].get('ansible_ssh_user')

                if not use_delegate or not user:
                    user = inject.get('ansible_ssh_user',
                                    self.runner.remote_user)

            if use_delegate:
                # FIXME
                private_key = inject.get('ansible_ssh_private_key_file', self.runner.private_key_file)
            else:
                private_key = inject.get('ansible_ssh_private_key_file', self.runner.private_key_file)

            private_key = template.template(self.runner.basedir, private_key, inject, fail_on_undefined=True)

            if not private_key is None:
                private_key = os.path.expanduser(private_key)
                options['private_key'] = private_key

            # use the mode to define src and dest's url
            if options.get('mode', 'push') == 'pull':
                # src is a remote path: <user>@<host>, dest is a local path
                src = self._process_remote(src_host, src, user)
                dest = self._process_origin(dest_host, dest, user)
            else:
                # src is a local path, dest is a remote path: <user>@<host>
                src = self._process_origin(src_host, src, user)
                dest = self._process_remote(dest_host, dest, user)

        options['src'] = src
        options['dest'] = dest
        if 'mode' in options:
            del options['mode']

        # Allow custom rsync path argument.
        rsync_path = options.get('rsync_path', None)

        # If no rsync_path is set, sudo was originally set, and dest is remote then add 'sudo rsync' argument.
        if not rsync_path and self.transport_overridden and self.original_become and not dest_is_local and self.runner.become_method == 'sudo':
            rsync_path = 'sudo rsync'

        # make sure rsync path is quoted.
        if rsync_path:
            options['rsync_path'] = '"' + rsync_path + '"'

        module_args = ""
        if self.runner.noop_on_check(inject):
            module_args = "CHECKMODE=True"

        # run the module and store the result
        result = self.runner._execute_module(conn, tmp, 'synchronize', module_args, complex_args=options, inject=inject)

        # reset the sudo property
        self.runner.become = self.original_become

        return result

