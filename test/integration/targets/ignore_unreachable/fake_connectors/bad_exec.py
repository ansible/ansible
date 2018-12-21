import ansible.plugins.connection.local as ansible_local
from ansible.errors import AnsibleConnectionFailure

from ansible.utils.display import Display
display = Display()


class Connection(ansible_local.Connection):
    def exec_command(self, cmd, in_data=None, sudoable=True):
        display.debug('Intercepted call to exec remote command')
        raise AnsibleConnectionFailure('BADLOCAL Error: this is supposed to fail')
