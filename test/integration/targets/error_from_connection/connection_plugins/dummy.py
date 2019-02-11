from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    author:
        - John Doe
    connection: dummy
    short_description: defective connection plugin
    description:
        - defective connection plugin
    version_added: "2.0"
    options: {}
"""
import ansible.constants as C
from ansible.errors import AnsibleError
from ansible.plugins.connection import ConnectionBase


class Connection(ConnectionBase):

    transport = 'dummy'
    has_pipelining = True

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        raise AnsibleError('an error with {{ some Jinja }}')

    def transport(self):
        pass

    def _connect(self):
        pass

    def exec_command(self, cmd, in_data=None, sudoable=True):
        pass

    def put_file(self, in_path, out_path):
        pass

    def fetch_file(self, in_path, out_path):
        pass

    def close(self):
        pass
