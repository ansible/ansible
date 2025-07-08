# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = """
    author: Ansible Core Team
    name: paramiko
    short_description: Run tasks via Python SSH (paramiko)
    description:
        - Use the Python SSH implementation (Paramiko) to connect to targets
        - The paramiko transport is provided because many distributions, in particular EL6 and before do not support ControlPersist
          in their SSH implementations.
        - This is needed on the Ansible control machine to be reasonably efficient with connections.
          Thus paramiko is faster for most users on these platforms.
          Users with ControlPersist capability can consider using -c ssh or configuring the transport in the configuration file.
        - This plugin also borrows a lot of settings from the ssh plugin as they both cover the same protocol.
    version_added: "0.1"
    options:
      remote_addr:
        description:
            - Address of the remote target
        default: inventory_hostname
        type: string
        vars:
            - name: inventory_hostname
            - name: ansible_host
            - name: ansible_ssh_host
            - name: ansible_paramiko_host
      port:
          description: Remote port to connect to.
          type: int
          default: 22
          ini:
            - section: defaults
              key: remote_port
            - section: paramiko_connection
              key: remote_port
              version_added: '2.15'
          env:
            - name: ANSIBLE_REMOTE_PORT
            - name: ANSIBLE_REMOTE_PARAMIKO_PORT
              version_added: '2.15'
          vars:
            - name: ansible_port
            - name: ansible_ssh_port
            - name: ansible_paramiko_port
              version_added: '2.15'
          keyword:
            - name: port
      remote_user:
        description:
            - User to login/authenticate as
            - Can be set from the CLI via the C(--user) or C(-u) options.
        type: string
        vars:
            - name: ansible_user
            - name: ansible_ssh_user
            - name: ansible_paramiko_user
        env:
            - name: ANSIBLE_REMOTE_USER
            - name: ANSIBLE_PARAMIKO_REMOTE_USER
              version_added: '2.5'
        ini:
            - section: defaults
              key: remote_user
            - section: paramiko_connection
              key: remote_user
              version_added: '2.5'
        keyword:
            - name: remote_user
      password:
        description:
          - Secret used to either login the ssh server or as a passphrase for ssh keys that require it
          - Can be set from the CLI via the C(--ask-pass) option.
        type: string
        vars:
            - name: ansible_password
            - name: ansible_ssh_pass
            - name: ansible_ssh_password
            - name: ansible_paramiko_pass
            - name: ansible_paramiko_password
              version_added: '2.5'
      use_rsa_sha2_algorithms:
        description:
            - Whether or not to enable RSA SHA2 algorithms for pubkeys and hostkeys
            - On paramiko versions older than 2.9, this only affects hostkeys
            - For behavior matching paramiko<2.9 set this to V(False)
        vars:
            - name: ansible_paramiko_use_rsa_sha2_algorithms
        ini:
            - {key: use_rsa_sha2_algorithms, section: paramiko_connection}
        env:
            - {name: ANSIBLE_PARAMIKO_USE_RSA_SHA2_ALGORITHMS}
        default: True
        type: boolean
        version_added: '2.14'
      host_key_auto_add:
        description: 'Automatically add host keys'
        env: [{name: ANSIBLE_PARAMIKO_HOST_KEY_AUTO_ADD}]
        ini:
          - {key: host_key_auto_add, section: paramiko_connection}
        type: boolean
      look_for_keys:
        default: True
        description: 'False to disable searching for private key files in ~/.ssh/'
        env: [{name: ANSIBLE_PARAMIKO_LOOK_FOR_KEYS}]
        ini:
        - {key: look_for_keys, section: paramiko_connection}
        type: boolean
      proxy_command:
        default: ''
        description:
            - Proxy information for running the connection via a jumphost.
        type: string
        env: [{name: ANSIBLE_PARAMIKO_PROXY_COMMAND}]
        ini:
          - {key: proxy_command, section: paramiko_connection}
        vars:
          - name: ansible_paramiko_proxy_command
            version_added: '2.15'
      pty:
        default: True
        description: 'SUDO usually requires a PTY, True to give a PTY and False to not give a PTY.'
        env:
          - name: ANSIBLE_PARAMIKO_PTY
        ini:
          - section: paramiko_connection
            key: pty
        type: boolean
      record_host_keys:
        default: True
        description: 'Save the host keys to a file'
        env: [{name: ANSIBLE_PARAMIKO_RECORD_HOST_KEYS}]
        ini:
          - section: paramiko_connection
            key: record_host_keys
        type: boolean
      host_key_checking:
        description: 'Set this to "False" if you want to avoid host key checking by the underlying tools Ansible uses to connect to the host'
        type: boolean
        default: True
        env:
          - name: ANSIBLE_HOST_KEY_CHECKING
          - name: ANSIBLE_SSH_HOST_KEY_CHECKING
            version_added: '2.5'
          - name: ANSIBLE_PARAMIKO_HOST_KEY_CHECKING
            version_added: '2.5'
        ini:
          - section: defaults
            key: host_key_checking
          - section: paramiko_connection
            key: host_key_checking
            version_added: '2.5'
        vars:
          - name: ansible_host_key_checking
            version_added: '2.5'
          - name: ansible_ssh_host_key_checking
            version_added: '2.5'
          - name: ansible_paramiko_host_key_checking
            version_added: '2.5'
      use_persistent_connections:
        description: 'Toggles the use of persistence for connections'
        type: boolean
        default: False
        env:
          - name: ANSIBLE_USE_PERSISTENT_CONNECTIONS
        ini:
          - section: defaults
            key: use_persistent_connections
      banner_timeout:
        type: float
        default: 30
        version_added: '2.14'
        description:
          - Configures, in seconds, the amount of time to wait for the SSH
            banner to be presented. This option is supported by paramiko
            version 1.15.0 or newer.
        ini:
          - section: paramiko_connection
            key: banner_timeout
        env:
          - name: ANSIBLE_PARAMIKO_BANNER_TIMEOUT
      timeout:
        type: int
        default: 10
        description: Number of seconds until the plugin gives up on failing to establish a TCP connection.
        ini:
          - section: defaults
            key: timeout
          - section: ssh_connection
            key: timeout
            version_added: '2.11'
          - section: paramiko_connection
            key: timeout
            version_added: '2.15'
        env:
          - name: ANSIBLE_TIMEOUT
          - name: ANSIBLE_SSH_TIMEOUT
            version_added: '2.11'
          - name: ANSIBLE_PARAMIKO_TIMEOUT
            version_added: '2.15'
        vars:
          - name: ansible_ssh_timeout
            version_added: '2.11'
          - name: ansible_paramiko_timeout
            version_added: '2.15'
        cli:
          - name: timeout
      private_key_file:
          description:
              - Path to private key file to use for authentication.
          type: string
          ini:
            - section: defaults
              key: private_key_file
            - section: paramiko_connection
              key: private_key_file
              version_added: '2.15'
          env:
            - name: ANSIBLE_PRIVATE_KEY_FILE
            - name: ANSIBLE_PARAMIKO_PRIVATE_KEY_FILE
              version_added: '2.15'
          vars:
            - name: ansible_private_key_file
            - name: ansible_ssh_private_key_file
            - name: ansible_paramiko_private_key_file
              version_added: '2.15'
          cli:
            - name: private_key_file
              option: '--private-key'
"""

import os
import socket
import tempfile
import traceback
import fcntl
import re
import typing as t

from ansible.module_utils.compat.version import LooseVersion
from binascii import hexlify

from ansible.errors import (
    AnsibleAuthenticationFailure,
    AnsibleConnectionFailure,
    AnsibleError,
    AnsibleFileNotFound,
)

from ansible.module_utils.common.text.converters import to_bytes, to_native, to_text
from ansible.module_utils.compat.paramiko import _PARAMIKO_IMPORT_ERR as PARAMIKO_IMPORT_ERR, _paramiko as paramiko
from ansible.plugins.connection import ConnectionBase
from ansible.utils.display import Display
from ansible.utils.path import makedirs_safe
from ansible.module_utils._internal import _deprecator

display = Display()


AUTHENTICITY_MSG = """
paramiko: The authenticity of host '%s' can't be established.
The %s key fingerprint is %s.
Are you sure you want to continue connecting (yes/no)?
"""

# SSH Options Regex
SETTINGS_REGEX = re.compile(r'(\w+)(?:\s*=\s*|\s+)(.+)')

MissingHostKeyPolicy: type = object
if paramiko:
    MissingHostKeyPolicy = paramiko.MissingHostKeyPolicy


class MyAddPolicy(MissingHostKeyPolicy):
    """
    Based on AutoAddPolicy in paramiko so we can determine when keys are added

    and also prompt for input.

    Policy for automatically adding the hostname and new host key to the
    local L{HostKeys} object, and saving it.  This is used by L{SSHClient}.
    """

    def __init__(self, connection: Connection) -> None:
        self.connection = connection
        self._options = connection._options

    def missing_host_key(self, client, hostname, key) -> None:

        if all((self.connection.get_option('host_key_checking'), not self.connection.get_option('host_key_auto_add'))):

            fingerprint = hexlify(key.get_fingerprint())
            ktype = key.get_name()

            if self.connection.get_option('use_persistent_connections') or self.connection.force_persistence:
                # don't print the prompt string since the user cannot respond
                # to the question anyway
                raise AnsibleError(AUTHENTICITY_MSG[1:92] % (hostname, ktype, fingerprint))

            inp = to_text(
                display.prompt_until(AUTHENTICITY_MSG % (hostname, ktype, fingerprint), private=False),
                errors='surrogate_or_strict'
            )

            if inp not in ['yes', 'y', '']:
                raise AnsibleError("host connection rejected by user")

        key._added_by_ansible_this_time = True

        # existing implementation below:
        client._host_keys.add(hostname, key.get_name(), key)

        # host keys are actually saved in close() function below
        # in order to control ordering.


# keep connection objects on a per host basis to avoid repeated attempts to reconnect

SSH_CONNECTION_CACHE: dict[str, paramiko.client.SSHClient] = {}
SFTP_CONNECTION_CACHE: dict[str, paramiko.sftp_client.SFTPClient] = {}


class Connection(ConnectionBase):
    """ SSH based connections with Paramiko """

    transport = 'paramiko'
    _log_channel: str | None = None

    def __init__(self, *args, **kwargs):
        display.deprecated(  # pylint: disable=ansible-deprecated-unnecessary-collection-name
            msg='The paramiko connection plugin is deprecated.',
            version='2.21',
            deprecator=_deprecator.ANSIBLE_CORE_DEPRECATOR,  # entire plugin being removed; this improves the messaging
        )

        super().__init__(*args, **kwargs)

    def _cache_key(self) -> str:
        return "%s__%s__" % (self.get_option('remote_addr'), self.get_option('remote_user'))

    def _connect(self) -> Connection:
        cache_key = self._cache_key()
        if cache_key in SSH_CONNECTION_CACHE:
            self.ssh = SSH_CONNECTION_CACHE[cache_key]
        else:
            self.ssh = SSH_CONNECTION_CACHE[cache_key] = self._connect_uncached()

        self._connected = True
        return self

    def _set_log_channel(self, name: str) -> None:
        """Mimic paramiko.SSHClient.set_log_channel"""
        self._log_channel = name

    def _parse_proxy_command(self, port: int = 22) -> dict[str, t.Any]:
        proxy_command = self.get_option('proxy_command') or None

        sock_kwarg = {}
        if proxy_command:
            replacers = {
                '%h': self.get_option('remote_addr'),
                '%p': port,
                '%r': self.get_option('remote_user')
            }
            for find, replace in replacers.items():
                proxy_command = proxy_command.replace(find, str(replace))
            try:
                sock_kwarg = {'sock': paramiko.ProxyCommand(proxy_command)}
                display.vvv("CONFIGURE PROXY COMMAND FOR CONNECTION: %s" % proxy_command, host=self.get_option('remote_addr'))
            except AttributeError:
                display.warning('Paramiko ProxyCommand support unavailable. '
                                'Please upgrade to Paramiko 1.9.0 or newer. '
                                'Not using configured ProxyCommand')

        return sock_kwarg

    def _connect_uncached(self) -> paramiko.SSHClient:
        """ activates the connection object """

        if paramiko is None:
            raise AnsibleError("paramiko is not installed: %s" % to_native(PARAMIKO_IMPORT_ERR))

        port = self.get_option('port')
        display.vvv("ESTABLISH PARAMIKO SSH CONNECTION FOR USER: %s on PORT %s TO %s" % (self.get_option('remote_user'), port, self.get_option('remote_addr')),
                    host=self.get_option('remote_addr'))

        ssh = paramiko.SSHClient()

        # Set pubkey and hostkey algorithms to disable, the only manipulation allowed currently
        # is keeping or omitting rsa-sha2 algorithms
        # default_keys: t.Tuple[str] = ()
        paramiko_preferred_pubkeys = getattr(paramiko.Transport, '_preferred_pubkeys', ())
        paramiko_preferred_hostkeys = getattr(paramiko.Transport, '_preferred_keys', ())
        use_rsa_sha2_algorithms = self.get_option('use_rsa_sha2_algorithms')
        disabled_algorithms: t.Dict[str, t.Iterable[str]] = {}
        if not use_rsa_sha2_algorithms:
            if paramiko_preferred_pubkeys:
                disabled_algorithms['pubkeys'] = tuple(a for a in paramiko_preferred_pubkeys if 'rsa-sha2' in a)
            if paramiko_preferred_hostkeys:
                disabled_algorithms['keys'] = tuple(a for a in paramiko_preferred_hostkeys if 'rsa-sha2' in a)

        # override paramiko's default logger name
        if self._log_channel is not None:
            ssh.set_log_channel(self._log_channel)

        self.keyfile = os.path.expanduser("~/.ssh/known_hosts")

        if self.get_option('host_key_checking'):
            for ssh_known_hosts in ("/etc/ssh/ssh_known_hosts", "/etc/openssh/ssh_known_hosts"):
                try:
                    # TODO: check if we need to look at several possible locations, possible for loop
                    ssh.load_system_host_keys(ssh_known_hosts)
                    break
                except OSError:
                    pass  # file was not found, but not required to function
            ssh.load_system_host_keys()

        ssh_connect_kwargs = self._parse_proxy_command(port)

        ssh.set_missing_host_key_policy(MyAddPolicy(self))

        conn_password = self.get_option('password')

        allow_agent = True

        if conn_password is not None:
            allow_agent = False

        try:
            key_filename = None
            if self.get_option('private_key_file'):
                key_filename = os.path.expanduser(self.get_option('private_key_file'))

            # paramiko 2.2 introduced auth_timeout parameter
            if LooseVersion(paramiko.__version__) >= LooseVersion('2.2.0'):
                ssh_connect_kwargs['auth_timeout'] = self.get_option('timeout')

            # paramiko 1.15 introduced banner timeout parameter
            if LooseVersion(paramiko.__version__) >= LooseVersion('1.15.0'):
                ssh_connect_kwargs['banner_timeout'] = self.get_option('banner_timeout')

            ssh.connect(
                self.get_option('remote_addr').lower(),
                username=self.get_option('remote_user'),
                allow_agent=allow_agent,
                look_for_keys=self.get_option('look_for_keys'),
                key_filename=key_filename,
                password=conn_password,
                timeout=self.get_option('timeout'),
                port=port,
                disabled_algorithms=disabled_algorithms,
                **ssh_connect_kwargs,
            )
        except paramiko.ssh_exception.BadHostKeyException as e:
            raise AnsibleConnectionFailure('host key mismatch for %s' % e.hostname)
        except paramiko.ssh_exception.AuthenticationException as ex:
            raise AnsibleAuthenticationFailure() from ex
        except Exception as ex:
            msg = str(ex)
            if u"PID check failed" in msg:
                raise AnsibleError("paramiko version issue, please upgrade paramiko on the machine running ansible") from ex
            elif u"Private key file is encrypted" in msg:
                msg = 'ssh %s@%s:%s : %s\nTo connect as a different user, use -u <username>.' % (
                    self.get_option('remote_user'), self.get_options('remote_addr'), port, msg)
                raise AnsibleConnectionFailure(msg) from ex
            else:
                raise AnsibleConnectionFailure(msg) from ex

        return ssh

    def exec_command(self, cmd: str, in_data: bytes | None = None, sudoable: bool = True) -> tuple[int, bytes, bytes]:
        """ run a command on the remote host """

        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        if in_data:
            raise AnsibleError("Internal Error: this module does not support optimized module pipelining")

        bufsize = 4096

        try:
            self.ssh.get_transport().set_keepalive(5)
            chan = self.ssh.get_transport().open_session()
        except Exception as e:
            text_e = to_text(e)
            msg = u"Failed to open session"
            if text_e:
                msg += u": %s" % text_e
            raise AnsibleConnectionFailure(to_native(msg))

        # sudo usually requires a PTY (cf. requiretty option), therefore
        # we give it one by default (pty=True in ansible.cfg), and we try
        # to initialise from the calling environment when sudoable is enabled
        if self.get_option('pty') and sudoable:
            chan.get_pty(term=os.getenv('TERM', 'vt100'), width=int(os.getenv('COLUMNS', 0)), height=int(os.getenv('LINES', 0)))

        display.vvv("EXEC %s" % cmd, host=self.get_option('remote_addr'))

        cmd = to_bytes(cmd, errors='surrogate_or_strict')

        no_prompt_out = b''
        no_prompt_err = b''
        become_output = b''

        try:
            chan.exec_command(cmd)
            if self.become and self.become.expect_prompt():
                passprompt = False
                become_sucess = False
                while not (become_sucess or passprompt):
                    display.debug('Waiting for Privilege Escalation input')

                    chunk = chan.recv(bufsize)
                    display.debug("chunk is: %r" % chunk)
                    if not chunk:
                        if b'unknown user' in become_output:
                            n_become_user = to_native(self.become.get_option('become_user'))
                            raise AnsibleError('user %s does not exist' % n_become_user)
                        else:
                            break
                            # raise AnsibleError('ssh connection closed waiting for password prompt')
                    become_output += chunk

                    # need to check every line because we might get lectured
                    # and we might get the middle of a line in a chunk
                    for line in become_output.splitlines(True):
                        if self.become.check_success(line):
                            become_sucess = True
                            break
                        elif self.become.check_password_prompt(line):
                            passprompt = True
                            break

                if passprompt:
                    if self.become:
                        become_pass = self.become.get_option('become_pass')
                        chan.sendall(to_bytes(become_pass, errors='surrogate_or_strict') + b'\n')
                    else:
                        raise AnsibleError("A password is required but none was supplied")
                else:
                    no_prompt_out += become_output
                    no_prompt_err += become_output
        except socket.timeout:
            raise AnsibleError('ssh timed out waiting for privilege escalation.\n' + to_text(become_output))

        stdout = b''.join(chan.makefile('rb', bufsize))
        stderr = b''.join(chan.makefile_stderr('rb', bufsize))

        return (chan.recv_exit_status(), no_prompt_out + stdout, no_prompt_out + stderr)

    def put_file(self, in_path: str, out_path: str) -> None:
        """ transfer a file from local to remote """

        super(Connection, self).put_file(in_path, out_path)

        display.vvv("PUT %s TO %s" % (in_path, out_path), host=self.get_option('remote_addr'))

        if not os.path.exists(to_bytes(in_path, errors='surrogate_or_strict')):
            raise AnsibleFileNotFound("file or module does not exist: %s" % in_path)

        try:
            self.sftp = self.ssh.open_sftp()
        except Exception as e:
            raise AnsibleError("failed to open a SFTP connection (%s)" % e)

        try:
            self.sftp.put(to_bytes(in_path, errors='surrogate_or_strict'), to_bytes(out_path, errors='surrogate_or_strict'))
        except OSError as ex:
            raise AnsibleError(f"Failed to transfer file to {out_path!r}.") from ex

    def _connect_sftp(self) -> paramiko.sftp_client.SFTPClient:

        cache_key = "%s__%s__" % (self.get_option('remote_addr'), self.get_option('remote_user'))
        if cache_key in SFTP_CONNECTION_CACHE:
            return SFTP_CONNECTION_CACHE[cache_key]
        else:
            result = SFTP_CONNECTION_CACHE[cache_key] = self._connect().ssh.open_sftp()
            return result

    def fetch_file(self, in_path: str, out_path: str) -> None:
        """ save a remote file to the specified path """

        super(Connection, self).fetch_file(in_path, out_path)

        display.vvv("FETCH %s TO %s" % (in_path, out_path), host=self.get_option('remote_addr'))

        try:
            self.sftp = self._connect_sftp()
        except Exception as e:
            raise AnsibleError("failed to open a SFTP connection (%s)" % to_native(e))

        try:
            self.sftp.get(to_bytes(in_path, errors='surrogate_or_strict'), to_bytes(out_path, errors='surrogate_or_strict'))
        except OSError as ex:
            raise AnsibleError(f"Failed to transfer file from {in_path!r}.") from ex

    def _any_keys_added(self) -> bool:

        for hostname, keys in self.ssh._host_keys.items():
            for keytype, key in keys.items():
                added_this_time = getattr(key, '_added_by_ansible_this_time', False)
                if added_this_time:
                    return True
        return False

    def _save_ssh_host_keys(self, filename: str) -> None:
        """
        not using the paramiko save_ssh_host_keys function as we want to add new SSH keys at the bottom so folks
        don't complain about it :)
        """

        if not self._any_keys_added():
            return

        path = os.path.expanduser("~/.ssh")
        makedirs_safe(path)

        with open(filename, 'w') as f:

            for hostname, keys in self.ssh._host_keys.items():

                for keytype, key in keys.items():

                    # was f.write
                    added_this_time = getattr(key, '_added_by_ansible_this_time', False)
                    if not added_this_time:
                        f.write("%s %s %s\n" % (hostname, keytype, key.get_base64()))

            for hostname, keys in self.ssh._host_keys.items():

                for keytype, key in keys.items():
                    added_this_time = getattr(key, '_added_by_ansible_this_time', False)
                    if added_this_time:
                        f.write("%s %s %s\n" % (hostname, keytype, key.get_base64()))

    def reset(self) -> None:
        if not self._connected:
            return
        self.close()
        self._connect()

    def close(self) -> None:
        """ terminate the connection """

        cache_key = self._cache_key()
        SSH_CONNECTION_CACHE.pop(cache_key, None)
        SFTP_CONNECTION_CACHE.pop(cache_key, None)

        if hasattr(self, 'sftp'):
            if self.sftp is not None:
                self.sftp.close()

        if self.get_option('host_key_checking') and self.get_option('record_host_keys') and self._any_keys_added():

            # add any new SSH host keys -- warning -- this could be slow
            # (This doesn't acquire the connection lock because it needs
            # to exclude only other known_hosts writers, not connections
            # that are starting up.)
            lockfile = self.keyfile.replace("known_hosts", ".known_hosts.lock")
            dirname = os.path.dirname(self.keyfile)
            makedirs_safe(dirname)

            KEY_LOCK = open(lockfile, 'w')
            fcntl.lockf(KEY_LOCK, fcntl.LOCK_EX)

            try:
                # just in case any were added recently

                self.ssh.load_system_host_keys()
                self.ssh._host_keys.update(self.ssh._system_host_keys)

                # gather information about the current key file, so
                # we can ensure the new file has the correct mode/owner

                key_dir = os.path.dirname(self.keyfile)
                if os.path.exists(self.keyfile):
                    key_stat = os.stat(self.keyfile)
                    mode = key_stat.st_mode
                    uid = key_stat.st_uid
                    gid = key_stat.st_gid
                else:
                    mode = 33188
                    uid = os.getuid()
                    gid = os.getgid()

                # Save the new keys to a temporary file and move it into place
                # rather than rewriting the file. We set delete=False because
                # the file will be moved into place rather than cleaned up.

                tmp_keyfile = tempfile.NamedTemporaryFile(dir=key_dir, delete=False)
                os.chmod(tmp_keyfile.name, mode & 0o7777)
                os.chown(tmp_keyfile.name, uid, gid)

                self._save_ssh_host_keys(tmp_keyfile.name)
                tmp_keyfile.close()

                os.rename(tmp_keyfile.name, self.keyfile)

            except Exception:

                # unable to save keys, including scenario when key was invalid
                # and caught earlier
                traceback.print_exc()
            fcntl.lockf(KEY_LOCK, fcntl.LOCK_UN)

        self.ssh.close()
        self._connected = False
