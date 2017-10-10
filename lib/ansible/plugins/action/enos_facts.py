# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by
# Ansible still belong to the author of the module, and may assign their own
# license to the complete work.
#
# Copyright (C) 2018 Lenovo, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Contains Action Plugin methods for ENOS Modules
# Lenovo Networking

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import copy

from ansible import constants as C
from ansible.plugins.action.normal import ActionModule as _ActionModule
from ansible.plugins.loader import connection_loader, module_loader
from ansible.utils.path import unfrackpath
from ansible.module_utils.basic import AnsibleFallbackNotFound
from enos import enos_argument_spec
from ansible.module_utils.six import iteritems

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class ActionModule(_ActionModule):

    def run(self, tmp=None, task_vars=None):

        if self._play_context.connection != 'local':
            return dict(
                failed=True,
                msg='invalid connection specified, expected connection=local, '
                    'got %s' % self._play_context.connection
            )
        provider = self.load_provider()

        pc = copy.deepcopy(self._play_context)
        pc.connection = 'network_cli'
        pc.network_os = 'enos'
        pc.remote_addr = provider['host'] or self._play_context.remote_addr
        display.vvvv('remote_addr: %s' % pc.remote_addr)
        pc.port = provider['port'] or self._play_context.port or 22
        pc.remote_user = provider['username'] or self._play_context.connection_user
        pc.password = provider['password'] or self._play_context.password
        pc.private_key_file = provider['ssh_keyfile'] or self._play_context.private_key_file
        pc.timeout = int(provider['timeout'] or C.PERSISTENT_COMMAND_TIMEOUT)

        pc.become = provider['authorize'] or True
        pc.become_pass = provider['auth_pass']

        display.vvv('using connection plugin %s' % pc.connection, pc.remote_addr)
        connection = self._shared_loader_obj.connection_loader.get('persistent', pc, sys.stdin)

        socket_path = connection.run()
        display.vvvv('socket_path: %s' % socket_path, pc.remote_addr)
        # while(socket_path is None and count < 2):
        #    socket_path = self._shared_loader_obj.connection_loader.get('persistent', pc, sys.stdin).run()
        #    count = count+1
        # display.vvvv('Again socket_path: %s' % socket_path, pc.remote_addr)
        if not socket_path:
            return {'failed': True,
                    'msg': 'unable to open shell. Please see: ' +
                           'https://docs.ansible.com/ansible/network_debug_troubleshooting.html#unable-to-open-shell'}

        # make sure we are in the right cli context which should be
        # enable mode and not config module
        # rc, out, err = connection.exec_command('prompt()')#'show run'
        # if str(out).strip().endswith(')#'):
        #    display.vvvv('wrong context, sending exit to device', self._play_context.remote_addr)
        #    connection.exec_command('exit')
        rc, out, err = connection.exec_command('prompt()')
        while str(out).strip().endswith(')#'):
            display.vvvv('wrong context, sending exit to device', self._play_context.remote_addr)
            connection.exec_command('exit')
            rc, out, err = connection.exec_command('prompt()')

        task_vars['ansible_socket'] = socket_path

        if self._play_context.become_method == 'enable':
            self._play_context.become = False
            self._play_context.become_method = None

        result = super(ActionModule, self).run(tmp, task_vars)
        return result

    def load_provider(self):
        provider = self._task.args.get('provider', {})
        for key, value in iteritems(enos_argument_spec):
            if key != 'provider' and key not in provider:
                if key in self._task.args:
                    provider[key] = self._task.args[key]
                elif 'fallback' in value:
                    provider[key] = self._fallback(value['fallback'])
                elif key not in provider:
                    provider[key] = None
        return provider

    def _fallback(self, fallback):
        strategy = fallback[0]
        args = []
        kwargs = {}

        for item in fallback[1:]:
            if isinstance(item, dict):
                kwargs = item
            else:
                args = item
        try:
            return strategy(*args, **kwargs)
        except AnsibleFallbackNotFound:
            pass
