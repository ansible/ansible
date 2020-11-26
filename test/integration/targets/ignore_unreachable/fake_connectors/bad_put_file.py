from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import ansible.plugins.connection.local as ansible_local
from ansible.errors import AnsibleConnectionFailure

from ansible.utils.display import Display
display = Display()


class Connection(ansible_local.Connection):
    def put_file(self, in_path, out_path):
        display.debug('Intercepted call to send data')
        raise AnsibleConnectionFailure('BADLOCAL Error: this is supposed to fail')
