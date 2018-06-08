# (c) 2018, zhikang zhang
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
<= to be continued
'''

from __main__ import display
from ansible import constants as C
from ansible.plugins.connection import ConnectionBase
from ansible.module_utils.parsing.convert_bool import boolean


class Connection(ConnectionBase):

    def __init__(self, *args, **kwargs):
        super(Connecttion, self).__init__(*arg, **kwargs)

        self.remote_addr = self._play_context.remote_addr
        self.port = self._play_context.port
        self.user = self._play_context.remote_user

    def put_file(self, in_path, out_path):
        super(Connection, self).put_file(in_path, out_path)
        
        display.vvv("PUT FILE FROM %s to %s" % (in_path, out_path))
        # TODO check if the file exist
        return self._file_transport_command(in_path, out_path, 'put')

    def fetch_file(self, in_path, out_path):
        super(Connection, self).fetch_file(in_path, out_path)
        display.vvv("FETCH FILE FROM %s to %s" % (in_path, out_path))
        # TODO check if the file exist
        return self._file_transport_command(in_path, out_path, 'get')

    def exec_command(self, cmd, in_data=None, sudoable=True):
        # run command in the remote machine
        pass

    def _file_transport_command(in_path, out_path, action):
        ssh_transfer_method = self._play_context.ssh_transfer_method
        # validate the ssh method
        if ssh_transfer_method is not None:
            if not (ssh_transfer_method in ('smart', 'sftp', 'scp', 'piped')):
                raise AnsibleOptionsError('transfer_method needs to be one of [smart|sftp|scp|piped]')
            if ssh_transfer_method == 'smart':
                methods = ['sftp', 'scp', 'piped']
            else:
                method = [ssh_transfer_method]
        # if no ssh method, use scp for now
        else:
            methods = ['scp']
        
        for method in methods:
            # construct command here
            # run command here


        

            


        
