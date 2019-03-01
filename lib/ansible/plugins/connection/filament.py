# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    author: jillr <@jillr>
    connection: filament
    short_description: filament
    description:
        - filament
    version_added: "2.0"
    options:
      foo:
        vars:
            - name: ansible_host
"""

from ansible.errors import AnsibleError, AnsibleConnectionFailure, AnsibleFileNotFound
from ansible.module_utils._text import to_bytes, to_text
from ansible.plugins.connection import ConnectionBase
import subprocess
import shutil


class Connection(ConnectionBase):
    """ filament connections """
    transport = "filament"
    has_pipelining = True

    def _connect(self):
        self._connected = True
        return self

    def exec_command(self, cmd, in_data=None, sudoable=False):
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        p = subprocess.Popen(
            cmd,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        stdout, stderr = p.communicate(in_data)
        rc = p.returncode

        return rc, stdout, stderr

    def put_file(self, in_path, out_path):
        super(Connection, self).put_file(in_path, out_path)

        shutil.copyfile(
            to_bytes(in_path, errors='surrogate_or_strict'),
            to_bytes(out_path, errors='surrogate_or_strict')
        )

    def fetch_file(self, in_path, out_path):
        super(Connection, self).fetch_file(in_path, out_path)

        self.put_file(in_path, out_path)

    def close(self):
        self._connected = False
