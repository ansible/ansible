# (c) 2018, zhikang zhang
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    connection: filament_connection
    short_description: connect remote via ssh
    description:
        - Practice plugin, use ssh to connect remote.
    author: ansible (@core)
    version_added: historical
    options:
      host:
          description: Hostname/ip to connect to.
          default: inventory_hostname
          vars:
               - name: ansible_host
               - name: ansible_ssh_host
      host_key_checking:
          description: Determines if ssh should check host keys
          type: boolean
          ini:
              - section: defaults
                key: 'host_key_checking'
              - section: ssh_connection
                key: 'host_key_checking'
                version_added: '2.5'
          env:
              - name: ANSIBLE_HOST_KEY_CHECKING
              - name: ANSIBLE_SSH_HOST_KEY_CHECKING
                version_added: '2.5'
          vars:
              - name: ansible_host_key_checking
                version_added: '2.5'
              - name: ansible_ssh_host_key_checking
                version_added: '2.5'
      password:
          description: Authentication password for the C(remote_user). Can be supplied as CLI option.
          vars:
              - name: ansible_password
              - name: ansible_ssh_pass
      ssh_args:
          description: Arguments to pass to all ssh cli tools
          default: '-C -o ControlMaster=auto -o ControlPersist=60s'
          ini:
              - section: 'ssh_connection'
                key: 'ssh_args'
          env:
              - name: ANSIBLE_SSH_ARGS
      ssh_common_args:
          description: Common extra args for all ssh CLI tools
          vars:
              - name: ansible_ssh_common_args
      ssh_executable:
          default: ssh
          description:
            - This defines the location of the ssh binary. It defaults to `ssh` which will use the first ssh binary available in $PATH.
            - This option is usually not required, it might be useful when access to system ssh is restricted,
              or when using ssh wrappers to connect to remote hosts.
          env: [{name: ANSIBLE_SSH_EXECUTABLE}]
          ini:
          - {key: ssh_executable, section: ssh_connection}
          #const: ANSIBLE_SSH_EXECUTABLE
          version_added: "2.2"
      sftp_executable:
          default: sftp
          description:
            - This defines the location of the sftp binary. It defaults to `sftp` which will use the first binary available in $PATH.
          env: [{name: ANSIBLE_SFTP_EXECUTABLE}]
          ini:
          - {key: sftp_executable, section: ssh_connection}
          version_added: "2.6"
      scp_executable:
          default: scp
          description:
            - This defines the location of the scp binary. It defaults to `scp` which will use the first binary available in $PATH.
          env: [{name: ANSIBLE_SCP_EXECUTABLE}]
          ini:
          - {key: scp_executable, section: ssh_connection}
          version_added: "2.6"
      scp_extra_args:
          description: Extra exclusive to the 'scp' CLI
          vars:
              - name: ansible_scp_extra_args
      sftp_extra_args:
          description: Extra exclusive to the 'sftp' CLI
          vars:
              - name: ansible_sftp_extra_args
      ssh_extra_args:
          description: Extra exclusive to the 'ssh' CLI
          vars:
              - name: ansible_ssh_extra_args
      retries:
          # constant: ANSIBLE_SSH_RETRIES
          description: Number of attempts to connect.
          default: 3
          type: integer
          env:
            - name: ANSIBLE_SSH_RETRIES
          ini:
            - section: connection
              key: retries
            - section: ssh_connection
              key: retries
      port:
          description: Remote port to connect to.
          type: int
          default: 22
          ini:
            - section: defaults
              key: remote_port
          env:
            - name: ANSIBLE_REMOTE_PORT
          vars:
            - name: ansible_port
            - name: ansible_ssh_port
      remote_user:
          description:
              - User name with which to login to the remote server, normally set by the remote_user keyword.
              - If no user is supplied, Ansible will let the ssh client binary choose the user as it normally
          ini:
            - section: defaults
              key: remote_user
          env:
            - name: ANSIBLE_REMOTE_USER
          vars:
            - name: ansible_user
            - name: ansible_ssh_user
      pipelining:
          default: ANSIBLE_PIPELINING
          description:
            - Pipelining reduces the number of SSH operations required to execute a module on the remote server,
              by executing many Ansible modules without actual file transfer.
            - This can result in a very significant performance improvement when enabled.
            - However this conflicts with privilege escalation (become).
              For example, when using sudo operations you must first disable 'requiretty' in the sudoers file for the target hosts,
              which is why this feature is disabled by default.
          env:
            - name: ANSIBLE_PIPELINING
            #- name: ANSIBLE_SSH_PIPELINING
          ini:
            - section: defaults
              key: pipelining
            #- section: ssh_connection
            #  key: pipelining
          type: boolean
          vars:
            - name: ansible_pipelining
            - name: ansible_ssh_pipelining
      private_key_file:
          description:
              - Path to private key file to use for authentication
          ini:
            - section: defaults
              key: private_key_file
          env:
            - name: ANSIBLE_PRIVATE_KEY_FILE
          vars:
            - name: ansible_private_key_file
            - name: ansible_ssh_private_key_file
      control_path:
        description:
          - This is the location to save ssh's ControlPath sockets, it uses ssh's variable substitution.
          - Since 2.3, if null, ansible will generate a unique hash. Use `%(directory)s` to indicate where to use the control dir path setting.
        env:
          - name: ANSIBLE_SSH_CONTROL_PATH
        ini:
          - key: control_path
            section: ssh_connection
      control_path_dir:
        default: ~/.ansible/cp
        description:
          - This sets the directory to use for ssh control path if the control path setting is null.
          - Also, provides the `%(directory)s` variable for the control path setting.
        env:
          - name: ANSIBLE_SSH_CONTROL_PATH_DIR
        ini:
          - section: ssh_connection
            key: control_path_dir
      sftp_batch_mode:
        default: 'yes'
        description: 'TODO: write it'
        env: [{name: ANSIBLE_SFTP_BATCH_MODE}]
        ini:
        - {key: sftp_batch_mode, section: ssh_connection}
        type: bool
      scp_if_ssh:
        default: smart
        description:
          - "Prefered method to use when transfering files over ssh"
          - When set to smart, Ansible will try them until one succeeds or they all fail
          - If set to True, it will force 'scp', if False it will use 'sftp'
        env: [{name: ANSIBLE_SCP_IF_SSH}]
        ini:
        - {key: scp_if_ssh, section: ssh_connection}
      use_tty:
        version_added: '2.5'
        default: 'yes'
        description: add -tt to ssh commands to force tty allocation
        env: [{name: ANSIBLE_SSH_USETTY}]
        ini:
        - {key: usetty, section: ssh_connection}
        type: bool
        yaml: {key: connection.usetty}
'''

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleConnectionFailure, AnsibleFileNotFound
from ansible.compat import selectors
from ansible.module_utils.six import PY3, text_type, binary_type
from ansible.module_utils.six.moves import shlex_quote
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.plugins.connection import ConnectionBase
from ansible.module_utils.parsing.convert_bool import boolean, BOOLEANS
import epdb
import errno
import fcntl
import hashlib
import os
import pty
import subprocess
import time

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

SSHPASS_AVAILABLE = None


class Connection(ConnectionBase):

    transport = 'filament_connection'
    has_pipeline = True
    allow_extras = True

    def _connect(self):
        return self

    def close(self):
        self._connected = False

    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)

        self.host = self._play_context.remote_addr
        self.port = self._play_context.port
        self.user = self._play_context.remote_user

    def _add_args(self, b_command, b_args, explanation):
        b_command += b_args

    def _bare_run(self, cmd, in_data, sudoable=True, checkrc=True):
        epdb.st()
        # if cmd is already string, convert it to binary string
        if isinstance(cmd, (text_type, binary_type)):
            cmd = to_bytes(cmd)
        # if it's a list, convert all elements in this list
        else:
            cmd = list(map(to_bytes, cmd))

        if not in_data:
            try:
                # try just use old pipes
                #master, slave = pty.openpty()
                # use the pipe defined in _file_transport to pass the password
                if PY3 and self._play_context.password:
                    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, pass_fds=self.sshpass_pipe)
                else:
                    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdin = p.stdin
            except (OSError, IOError):
                p = None

        # inject the password
        if self._play_context.password:
            # close the reading pipe
            os.close(self.sshpass_pipe[0])
            try:
                # write password to pipe
                os.write(self.sshpass_pipe[1], to_bytes(self._play_context.password) + b'\n')
            except OSError as e:
                # if the error is related to pipe, ignore it
                if e.errno != errno.EPIPE:
                    raise
            # close the writing pipe too
            os.close(self.sshpass_pipe[1])

        states = ['awaiting_prompt', 'awaiting_escalation', 'ready_to_send', 'awaiting_exit']

        # inital state is readt_to_send, this will only work when in_data is not None
        # in_data is responsible for sending files
        state = states.index('ready_to_send')
        if to_bytes(self.get_option('ssh_executable')) in cmd and sudoable:
            # if we want to escalation with password, wait for a prompt
            if self._play_context.prompt:
                state = states.index('awaiting_prompt')

        b_stdout = b_stderr = b''
        b_tmp_stdout = b_tmp_stderr = b''

        # no idea what this for
        timeout = 2 + self._play_context.timeout
        for fd in (p.stdout, p.stderr):
            fcntl.fcntl(fd, fcntl.F_SETFL, fcntl.fcntl(fd, fcntl.F_GETFL) | os.O_NONBLOCK)
        
        # event-driven
        selector = selectors.DefaultSelector()
        selector.register(p.stdout, selectors.EVENT_READ)
        selector.register(p.stderr, selectors.EVENT_READ)

        # if in_data is not None, send or fetch file directly
        if states[state] == 'ready_to_send' and in_data:
            self._send_initial_data(stdin, in_data)
            # state become exit
            state += 1
        
        try:
            while True:
                poll = p.poll()
                events = selector.select(timeout)
                
                if not events:
                    if state <= (states.index('awaiting_escalation')):
                        if poll is not None:
                            break
                        self._terminate_process(p)
                        raise AnsibleError('Timeout!')

                for key, event in events:
                    # if the stdout is ready to read
                    if key.fileobj == p.stdout:
                        b_chunk = p.stdout.read()
                        if b_chunk == b'':
                            # stdout is finished, stop wathcing it
                            selector.unregister(p.stdout)
                        b_tmp_stdout += b_chunk
                    elif key.fileobj == p.stderr:
                        b_chunk = p.stderr.read()
                        if b_chunk == b'':
                            selector.unregister(p.stderr)
                        b_tmp_stderr += b_chunk

                # refresh output
                if b_tmp_stdout:
                    b_stdout += b_tmp_stdout
                    b_tmp_stdout = b''
                if b_tmp_stderr:
                    b_stderr += b_tmp_stderr
                    b_tmp_stderr = b''

                # some code handle the output and prompt
                # balabalabala
                # some code handle escalation
                # balabalabala

                # now if we ready to handle file, send or fetch file
                if states[state] == 'ready_to_send':
                    if in_data:
                        self._send_initial_data(stdin, in_data)
                    state += 1
                
                if poll is not None:
                    if not selector.get_map() or not events:
                        break
                    timeout = 0
                    continue

                elif not selector.get_map():
                    p.wait()
                    break
        
        finally:
            # quit the poll loop, close lisenter
            selector.close()
            stdin.close()

        # some code handle return code from process
        # balabala

        return (p.returncode, b_stdout, b_stderr)

    @staticmethod
    def _sshpass_available():
        global SSHPASS_AVAILABLE

        if SSHPASS_AVAILABLE is None:
            try:
                p = subprocess.Popen(["sshpass"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                p.communicate()
                SSHPASS_AVAILABLE = True
            except OSError:
                SSHPASS_AVAILABLE = False
        return SSHPASS_AVAILABLE

    def put_file(self, in_path, out_path):
        epdb.st()
        super(Connection, self).put_file(in_path, out_path)
        
        display.vvv("PUT FILE FROM %s to %s" % (in_path, out_path))
        if not os.path.exists(to_bytes(in_path)):
            raise AnsibleFileNotFound('File does not exist!')
        return self._file_transport_command(in_path, out_path, 'put')

    def fetch_file(self, in_path, out_path):
        epdb.st()
        super(Connection, self).fetch_file(in_path, out_path)
        display.vvv("FETCH FILE FROM %s to %s" % (in_path, out_path))
        return self._file_transport_command(in_path, out_path, 'get')

    def exec_command(self, cmd, in_data=None, sudoable=True):
        epdb.st()
        # run command in the remote machine
        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)
        ssh_executable = self._play_context.ssh_executable
        use_tty = self.get_option('use_tty')
        if not in_data and sudoable and use_tty:
            args = (ssh_executable, '-tt', self.host, cmd)
        else:
            args = (ssh_executable, self.host, cmd)

        # build the command
        cmd = self._build_command(*args)
        # run command
        (returncode, stdout, stderr) = self._bare_run(cmd, in_data, sudoable)

        return (returncode, stdout, stderr)

    def _build_command(self, binary, *other_args):
        epdb.st()
        # the whole command
        b_command = []
        # if need password but does not support sshpass, raise error
        if self._play_context.password:
            if not self._sshpass_available():
                raise AnsibleError('No sshpass!')
            # open the pipe to pass password
            self.sshpass_pipe = os.pipe()
            # sshpass command
            b_command += [b'sshpass', b'-d', to_bytes(self.sshpass_pipe[0])]
            # worker command
            b_command += [to_bytes(binary)]

        # speical case for sftp, mainly for file transfer
        if binary == 'sftp' and C.DEFAULT_SFTP_BATCH_MODE:
            if self._play_context.password:
                b_args = [b'-o', b'BatchMode=no']
                self._add_args(b_command, b_args, u'disable batch mode for sshpass')
            b_command += [b'-b', b'-']

        # add all arguments from ansible.cfg
        if self._play_context.ssh_args:
            b_args = [to_bytes(a, errors='surrogate_or_strict') for a in
                      self._split_ssh_args(self._play_context.ssh_args)]
            self._add_args(b_command, b_args, u"ansible.cfg set ssh_args")
        
        # some othe checking code
        # balabalabalabala

        # add private key arg
        key = self._play_context.private_key_file
        if key:
            b_args = (b"-o", b'IdentityFile="' + to_bytes(os.path.expanduser(key), errors='surrogate_or_strict') + b'"')
            self._add_args(b_command, b_args, u"ANSIBLE_PRIVATE_KEY_FILE/private_key_file/ansible_ssh_private_key_file set")

        # add remote user arg
        user = self._play_context.remote_user
        if user:
            self._add_args(b_command, (b"-o", b"User=" + to_bytes(self._play_context.remote_user, errors='surrogate_or_strict')), u"ANSIBLE_REMOTE_USER/remote_user/ansible_user/user/-u set")
        
        # add common or binary arguments
        for opt in (u'ssh_common_args', u'{0}_extra_args'.format(binary)):
            attr = getattr(self._play_context, opt, None)
            if attr is not None:
                b_args = [to_bytes(a, errors='surrogate_or_strict') for a in self._split_ssh_args(attr)]
                self._add_args(b_command, b_args, u"PlayContext set %s" % opt)

        # add other args
        if other_args:
            b_command += [to_bytes(a) for a in other_args]

        return b_command



    def _file_transport_command(self, in_path, out_path, sftp_action):
        epdb.set_trace()
        host = '[%s]' % self.host
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
            # use sftp to handle file
            if method == 'sftp':
                # build the basic command
                cmd = self._build_command(self.get_option('sftp_executable'), to_bytes(host))
                # build the file transfer command
                in_data = u"{0} {1} {2}\n".format(sftp_action, shlex_quote(in_path), shlex_quote(out_path))
                in_data = to_bytes(in_data)
                # run the command
                (returncode, stdout, stderr) = self._bare_run(cmd, in_data, checkrc=False)
            # use scp to handle file
            elif method == 'scp':
                scp = self.get_option('scp_executable')
                if sftp_action == 'get':
                    cmd = self._build_command(scp, u'{0}:{1}'.format(host, shlex_quote(in_path)), out_path)
                else:
                    cmd = self._build_command(scp, in_path, u'{0}:{1}'.format(host, shlex_quote(out_path)))
                (returncode, stdout, stderr) = self._bare_run(cmd, None, checkrc=False)
            # use pipe to handle file
            elif method == 'piped':
                # not handle this now
                pass

            if returncode == 0:
                return (returncode, stdout, stderr)
        
        # if tried all methods and still can't transfer, raise error
        raise AnsibleError('Failed to transfer file!')


