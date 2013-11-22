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

    def _process_origin(self, host, path, user):

        if not host in ['127.0.0.1', 'localhost']:
            return '%s@%s:%s' % (user, host, path)
        else:
            return path

    def setup(self, module_name, inject):
        ''' Always default to localhost as delegate if None defined '''
        if inject.get('delegate_to') is None:
            inject['delegate_to'] = '127.0.0.1'
            inject['ansible_connection'] = 'local'
            # If sudo is active, disable from the connection set self.sudo to True.
            if self.runner.sudo:
                self.runner.sudo = False

    def run(self, conn, tmp, module_name, module_args,
        inject, complex_args=None, **kwargs):

        ''' generates params and passes them on to the rsync module '''

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

        # edge case: explicit delegate and dest_host are the same
        if dest_host == inject['delegate_to']:
            dest_host = '127.0.0.1'

        if options.get('mode', 'push') == 'pull':
            (dest_host, src_host) = (src_host, dest_host)
        if not dest_host is src_host:
            user = inject.get('ansible_ssh_user',
                              self.runner.remote_user)
            private_key = inject.get('ansible_ssh_private_key_file', self.runner.private_key_file)
            if not private_key is None:
                options['private_key'] = private_key
            src = self._process_origin(src_host, src, user)
            dest = self._process_origin(dest_host, dest, user)

        options['src'] = src
        options['dest'] = dest
        if 'mode' in options:
            del options['mode']

        rsync_path = options.get('rsync_path', None)
        if not rsync_path and self.runner.sudo:
            rsync_path = 'sudo rsync'

        # make sure rsync path is quoted.
        if rsync_path:
            options['rsync_path'] = '"' + rsync_path + '"'

        module_items = ' '.join(['%s=%s' % (k, v) for (k,
                v) in options.items()])
        return self.runner._execute_module(conn, tmp, 'synchronize',
                module_items, inject=inject)

