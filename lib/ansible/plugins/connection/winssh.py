# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import xmltodict
import os

from ansible.module_utils.basic import to_bytes, to_native
from ansible.errors import AnsibleFileNotFound
from ansible.plugins.connection.ssh import Connection as SSHConnection

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class Connection(SSHConnection):
    ''' ssh based connections '''

    transport = 'winssh'
    module_implementation_preferences = ('.ps1', '.exe', '')
    become_methods = ['runas']
    allow_executable = False
    has_pipelining = True
    allow_extras = True

    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)

        self.always_pipeline_modules = True
        self.has_native_async = True

    #
    # Main public methods
    #
    def exec_command(self, cmd, in_data=None, sudoable=True):
        ''' run a command on the remote host '''

        super(SSHConnection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        cmd_parts = self._shell._encode_script(cmd, as_list=True, strict_mode=False, preserve_rc=False)
        display.vvv("EXEC (via pipeline wrapper)")

        ssh_executable = self._play_context.ssh_executable

        if not in_data and sudoable:
            args = (ssh_executable, '-tt', self.host, ' '.join(cmd_parts))
        else:
            args = (ssh_executable, self.host, ' '.join(cmd_parts))
        cmd = self._build_command(*args)
        orig = self._play_context.become
        self._play_context.become = False
        (returncode, stdout, stderr) = self._run(cmd, in_data, sudoable=sudoable)
        self._play_context.become = orig

        # parse just stderr from CLIXML output
        if self.is_clixml(stderr):
            try:
                stderr = self.parse_clixml_stream(stderr)
            except:
                # unsure if we're guaranteed a valid xml doc- use raw output in case of error
                pass

        return (returncode, stdout, stderr)

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to remote '''
        super(SSHConnection, self).put_file(in_path, out_path)

        display.vvv(u"PUT {0} TO {1}".format(in_path, out_path), host=self.host)
        if not os.path.exists(to_bytes(in_path, errors='surrogate_or_strict')):
            raise AnsibleFileNotFound("file or module does not exist: {0}".format(to_native(in_path)))

        # SFTP only works for Windows when path is in form /C:/folder/path, convert it before sending to
        # the usual SSH put_file
        out_path = "/%s" % out_path[1:len(out_path) - 1].replace("\\", "/")

        return super(Connection, self).put_file(in_path, out_path)


    def is_clixml(self, value):
        return value.startswith(b"#< CLIXML")

    # hacky way to get just stdout- not always sure of doc framing here, so use with care
    def parse_clixml_stream(self, clixml_doc, stream_name='Error'):
        clear_xml = clixml_doc.replace(b'#< CLIXML\r\n', b'')
        doc = xmltodict.parse(clear_xml)
        lines = [l.get('#text', '').replace('_x000D__x000A_', '') for l in doc.get('Objs', {}).get('S', {}) if l.get('@S') == stream_name]
        return '\r\n'.join(lines)
