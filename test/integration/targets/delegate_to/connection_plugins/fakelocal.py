# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = """
    connection: fakelocal
    short_description: dont execute anything
    description:
        - This connection plugin just verifies parameters passed in
    author: ansible (@core)
    version_added: histerical
    options:
      password:
          description: Authentication password for the C(remote_user). Can be supplied as CLI option.
          vars:
              - name: ansible_password
      remote_user:
          description:
              - User name with which to login to the remote server, normally set by the remote_user keyword.
          ini:
            - section: defaults
              key: remote_user
          vars:
              - name: ansible_user
"""

from ansible.errors import AnsibleConnectionFailure
from ansible.plugins.connection import ConnectionBase
from ansible.utils.display import Display

display = Display()


class Connection(ConnectionBase):
    """ Local based connections """

    transport = 'fakelocal'
    has_pipelining = True

    def __init__(self, *args, **kwargs):

        super(Connection, self).__init__(*args, **kwargs)
        self.cwd = None

    def _connect(self):
        """ verify """

        if self.get_option('remote_user') == 'invaliduser' and self.get_option('password') == 'badpassword':
            raise AnsibleConnectionFailure('Got invaliduser and badpassword')

        if not self._connected:
            display.vvv(u"ESTABLISH FAKELOCAL CONNECTION FOR USER: {0}".format(self._play_context.remote_user), host=self._play_context.remote_addr)
            self._connected = True
        return self

    def exec_command(self, cmd, in_data=None, sudoable=True):
        """ run a command on the local host """

        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        return 0, '{"msg": "ALL IS GOOD"}', ''

    def put_file(self, in_path, out_path):
        """ transfer a file from local to local """

        super(Connection, self).put_file(in_path, out_path)

    def fetch_file(self, in_path, out_path):
        """ fetch a file from local to local -- for compatibility """

        super(Connection, self).fetch_file(in_path, out_path)

    def close(self):
        """ terminate the connection; nothing to do here """
        self._connected = False
