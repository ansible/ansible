# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2015, 2017 Toshio Kuratomi <tkuratomi@ansible.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: dummy
    short_description: a non connection connection
    description:
        - This connection plugin pretends to do stuff, but does nothing
    author: ansible (@core)
    version_added: 2.16
    options:
        remote_user:
            description: normally YOU, does not matter, not really used
            env:
                - name: USER
        remote_addr:
            description: dummy host that doesn't exist
            default: ansible_dummy_host
    extends_documentation_fragment:
        - connection_pipelining
    notes:
        - All settings are ignored except for giving messages in verbose
'''


from ansible.module_utils._text import to_text
from ansible.plugins.connection import ConnectionBase
from ansible.utils.display import Display

display = Display()


class Connection(ConnectionBase):

    transport = 'dummy'
    has_pipelining = True

    def __init__(self, *args, **kwargs):

        super(Connection, self).__init__(*args, **kwargs)

    def _connect(self):
        ''' nothing to do here '''
        if not self._connected:
            display.vvv(u"ESTABLISH DUMMY CONNECTION FOR USER: {0}".format(self._get_option('remote_user')), host=self.get_option('remote_addr'))
            self._connected = True
        return self

    def exec_command(self, cmd, in_data=None, sudoable=True):
        ''' dont run command anywhere '''

        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        display.vvv(u"EXEC {0}".format(to_text(cmd)), host=self.get_option('remote_addr'))

        return (0, '', '')

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to local '''

        super(Connection, self).put_file(in_path, out_path)

        display.vvv(u"PUT {0} TO {1}".format(in_path, out_path), host=self.get_option('remote_addr'))

    def fetch_file(self, in_path, out_path):
        ''' fetch a file from local to local -- for compatibility '''

        super(Connection, self).fetch_file(in_path, out_path)

        display.vvv(u"FETCH {0} TO {1}".format(in_path, out_path), host=self.get_option('remote_addr'))

    def close(self):
        ''' terminate the connection; nothing to do here '''
        self._connected = False
