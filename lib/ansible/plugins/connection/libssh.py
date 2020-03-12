# (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    author: Ansible Core Team
    connection: libssh
    short_description: Run tasks via libssh (python extension)
    description:
        - Use the pylibssh python bindings to connect to targets
        - The python bindings use libssh C library (https://www.libssh.org/) to connect to targets
        - This plugin borrows a lot of settings from the ssh plugin as they both cover the same protocol.
    version_added: "2.10"
    options:
      remote_addr:
        description:
            - Address of the remote target
        default: inventory_hostname
        vars:
            - name: ansible_host
            - name: ansible_ssh_host
            - name: ansible_libssh_host
      remote_user:
        description:
            - User to login/authenticate as
            - Can be set from the CLI via the C(--user) or C(-u) options.
        vars:
            - name: ansible_user
            - name: ansible_ssh_user
            - name: ansible_libssh_user
        env:
            - name: ANSIBLE_REMOTE_USER
            - name: ANSIBLE_LIBSSH_REMOTE_USER
        ini:
            - section: defaults
              key: remote_user
            - section: libssh_connection
              key: remote_user
      password:
        description:
          - Secret used to either login the ssh server or as a passphrase for ssh keys that require it
          - Can be set from the CLI via the C(--ask-pass) option.
        vars:
            - name: ansible_password
            - name: ansible_ssh_pass
            - name: ansible_ssh_password
            - name: ansible_libssh_pass
            - name: ansible_libssh_password
      host_key_auto_add:
        description: 'TODO: write it'
        env: [{name: ANSIBLE_LIBSSH_HOST_KEY_AUTO_ADD}]
        ini:
          - {key: host_key_auto_add, section: libssh_connection}
        type: boolean
      look_for_keys:
        default: True
        description: 'TODO: write it'
        env: [{name: ANSIBLE_LIBSSH_LOOK_FOR_KEYS}]
        ini:
        - {key: look_for_keys, section: libssh_connection}
        type: boolean
      proxy_command:
        default: ''
        description:
            - Proxy information for running the connection via a jumphost
            - Also this plugin will scan 'ssh_args', 'ssh_extra_args' and 'ssh_common_args' from the 'ssh' plugin settings for proxy information if set.
        env: [{name: ANSIBLE_LIBSSH_PROXY_COMMAND}]
        ini:
          - {key: proxy_command, section: libssh_connection}
      pty:
        default: True
        description: 'TODO: write it'
        env:
          - name: ANSIBLE_LIBSSH_PTY
        ini:
          - section: libssh_connection
            key: pty
        type: boolean
      record_host_keys:
        default: True
        description: 'TODO: write it'
        env: [{name: ANSIBLE_LIBSSH_RECORD_HOST_KEYS}]
        ini:
          - section: libssh_connection
            key: record_host_keys
        type: boolean
      host_key_checking:
        description: 'Set this to "False" if you want to avoid host key checking by the underlying tools Ansible uses to connect to the host'
        type: boolean
        default: True
        env:
          - name: ANSIBLE_HOST_KEY_CHECKING
          - name: ANSIBLE_SSH_HOST_KEY_CHECKING
          - name: ANSIBLE_LIBSSH_HOST_KEY_CHECKING
        ini:
          - section: defaults
            key: host_key_checking
          - section: libssh_connection
            key: host_key_checking
        vars:
          - name: ansible_host_key_checking
          - name: ansible_ssh_host_key_checking
          - name: ansible_libssh_host_key_checking
      use_persistent_connections:
        description: 'Toggles the use of persistence for connections'
        type: boolean
        default: False
        env:
          - name: ANSIBLE_USE_PERSISTENT_CONNECTIONS
        ini:
          - section: defaults
            key: use_persistent_connections
# TODO:
#timeout=self._play_context.timeout,
"""
import os
import socket
import tempfile
import traceback
import fcntl
import sys
import re

from termios import tcflush, TCIFLUSH
from binascii import hexlify

from ansible.errors import (
    AnsibleConnectionFailure,
    AnsibleError,
    AnsibleFileNotFound,
)
from ansible.module_utils.six import iteritems
from ansible.module_utils.six.moves import input
from ansible.plugins.connection import ConnectionBase
from ansible.utils.display import Display
from ansible.utils.path import makedirs_safe
from ansible.module_utils._text import to_bytes, to_native, to_text
import logging
display = Display()

try:
    from pylibsshext.session import Session
    from pylibsshext.channel import Channel
    from pylibsshext.errors import LibsshSessionException
    HAS_PYLIBSSH = True
except ImportError:
    HAS_PYLIBSSH = False

# SSH Options Regex
SETTINGS_REGEX = re.compile(r'(\w+)(?:\s*=\s*|\s+)(.+)')

# keep connection objects on a per host basis to avoid repeated attempts to reconnect
SSH_CONNECTION_CACHE = {}
SFTP_CONNECTION_CACHE = {}


class Connection(ConnectionBase):
    ''' SSH based connections with Paramiko '''

    transport = 'libssh'
    _log_channel = None

    def _cache_key(self):
        return "%s__%s__" % (self._play_context.remote_addr, self._play_context.remote_user)

    def _connect(self):
        cache_key = self._cache_key()
        if cache_key in SSH_CONNECTION_CACHE:
            self.ssh = SSH_CONNECTION_CACHE[cache_key]
        else:
            self.ssh = SSH_CONNECTION_CACHE[cache_key] = self._connect_uncached()
        return self

    def _set_log_channel(self, name):
        self._log_channel = name

    def _get_proxy_command(self, port=22):
        proxy_command = None
        # Parse ansible_ssh_common_args, specifically looking for ProxyCommand
        ssh_args = [
            getattr(self._play_context, 'ssh_extra_args', '') or '',
            getattr(self._play_context, 'ssh_common_args', '') or '',
            getattr(self._play_context, 'ssh_args', '') or '',
        ]

        if ssh_args is not None:
            args = self._split_ssh_args(' '.join(ssh_args))
            for i, arg in enumerate(args):
                if arg.lower() == 'proxycommand':
                    # _split_ssh_args split ProxyCommand from the command itself
                    proxy_command = args[i + 1]
                else:
                    # ProxyCommand and the command itself are a single string
                    match = SETTINGS_REGEX.match(arg)
                    if match:
                        if match.group(1).lower() == 'proxycommand':
                            proxy_command = match.group(2)

                if proxy_command:
                    break

        proxy_command = proxy_command or self.get_option('proxy_command')

        if proxy_command:
            replacers = {
                '%h': self._play_context.remote_addr,
                '%p': port,
                '%r': self._play_context.remote_user
            }
            for find, replace in replacers.items():
                proxy_command = proxy_command.replace(find, str(replace))

        return proxy_command

    def _connect_uncached(self):
        ''' activates the connection object '''

        if not HAS_PYLIBSSH:
            raise AnsibleError("ansible-pylibssh is not installed")

        ssh_connect_kwargs = {}

        port = self._play_context.port or 22
        display.vvv("ESTABLISH LIBSSH CONNECTION FOR USER: %s on PORT %s TO %s" % (self._play_context.remote_user, port, self._play_context.remote_addr),
                    host=self._play_context.remote_addr)

        self.ssh = Session()

        if self._play_context.verbosity > 3:
           self.ssh.set_log_level(logging.INFO)

        self.keyfile = os.path.expanduser("~/.ssh/known_hosts")

        if self.get_option('host_key_checking'):
            for ssh_known_hosts in ("/etc/ssh/ssh_known_hosts", "/etc/openssh/ssh_known_hosts"):
                try:
                    # TODO: check if we need to look at several possible locations, possible for loop
                    self.ssh.load_system_host_keys(ssh_known_hosts)
                    break
                except IOError:
                    pass  # file was not found, but not required to function
            self.ssh.load_system_host_keys()

        proxy_command = self._get_proxy_command(port)

        try:
            key_filename = None
            if self._play_context.private_key_file:
                key_filename = os.path.expanduser(self._play_context.private_key_file)

            if proxy_command:
                ssh_connect_kwargs['proxycommand'] = proxy_command

            self.ssh.connect(
                host=self._play_context.remote_addr.lower(),
                user=self._play_context.remote_user,
                # look_for_keys=self.get_option('look_for_keys'),
                # key_filename=key_filename,
                password=self._play_context.password,
                timeout=self._play_context.timeout,
                port=port,
                **ssh_connect_kwargs
            )
        except LibsshSessionException as e:
            msg = "ssh connection failed: " + to_text(e)
            raise AnsibleConnectionFailure(msg)
        except Exception as e:
            raise AnsibleConnectionFailure(to_text(e))

        display.vvv("ssh connection is OK: " + str(self.ssh))
        return self.ssh

    def exec_command(self, cmd, in_data=None, sudoable=True):
        ''' run a command on the remote host '''

        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        if in_data:
            raise AnsibleError("Internal Error: this module does not support optimized module pipelining")

        bufsize = 4096

        try:
            chan = self.ssh.new_channel()
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
            chan.request_shell()

        display.vvv("EXEC %s" % cmd, host=self._play_context.remote_addr)

        cmd = to_bytes(cmd, errors='surrogate_or_strict')

        result = None
        no_prompt_out = b''
        no_prompt_err = b''
        become_output = b''
        out = b''
        err = b''

        try:
            if self.become and self.become.expect_prompt():
                passprompt = False
                become_sucess = False
                chan.sendall(cmd)

                while not (become_sucess or passprompt):
                    display.debug('Waiting for Privilege Escalation input')
                    chan.poll(timeout=self._play_context.timeout)
                    chunk = chan.recv(bufsize)
                    display.debug("chunk is: %s" % chunk)

                    if not chunk:
                        if b'unknown user' in become_output:
                            n_become_user = to_native(self.become.get_option('become_user',
                                                                             playcontext=self._play_context))
                            raise AnsibleError('user %s does not exist' % n_become_user)
                        else:
                            break
                            # raise AnsibleError('ssh connection closed waiting for password prompt')
                    become_output += chunk
                    # need to check every line because we might get lectured
                    # and we might get the middle of a line in a chunk
                    for l in become_output.splitlines(True):
                        if self.become.check_success(l):
                            become_sucess = True
                            break
                        elif self.become.check_password_prompt(l):
                            passprompt = True
                            break
                if passprompt:
                    if self.become:
                        become_pass = self.become.get_option('become_pass', playcontext=self._play_context)
                        chan.sendall(to_bytes(become_pass, errors='surrogate_or_strict') + b'\n')
                    else:
                        raise AnsibleError("A password is required but none was supplied")
                else:
                    no_prompt_out += become_output
                    no_prompt_err += become_output
            else:
                result = chan.exec_command(to_text(cmd, errors='surrogate_or_strict'))
        except socket.timeout:
            raise AnsibleError('ssh timed out waiting for privilege escalation.\n' + become_output)

        if result:
            rc = result.returncode
            out = result.stdout
            err = result.stderr
        else:
            rc = chan.get_channel_exit_status()
        return rc, out, err

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to remote '''

        super(Connection, self).put_file(in_path, out_path)

        display.vvv("PUT %s TO %s" % (in_path, out_path), host=self._play_context.remote_addr)

        if not os.path.exists(to_bytes(in_path, errors='surrogate_or_strict')):
            raise AnsibleFileNotFound("file or module does not exist: %s" % in_path)

        try:
            self.sftp = self.ssh.sftp()
        except Exception as e:
            raise AnsibleError("failed to open a SFTP connection (%s)" % e)

        try:
            self.sftp.put(to_bytes(in_path, errors='surrogate_or_strict'), to_bytes(out_path, errors='surrogate_or_strict'))
        except IOError:
            raise AnsibleError("failed to transfer file to %s" % out_path)

    def _connect_sftp(self):
        cache_key = "%s__%s__" % (self._play_context.remote_addr, self._play_context.remote_user)
        if cache_key in SFTP_CONNECTION_CACHE:
            return SFTP_CONNECTION_CACHE[cache_key]
        else:
            result = SFTP_CONNECTION_CACHE[cache_key] = self._connect().ssh.sftp()
            return result

    def fetch_file(self, in_path, out_path):
        ''' save a remote file to the specified path '''

        super(Connection, self).fetch_file(in_path, out_path)

        display.vvv("FETCH %s TO %s" % (in_path, out_path), host=self._play_context.remote_addr)

        # try:
        #     self.sftp = self._connect_sftp()
        # except Exception as e:
        #     raise AnsibleError("failed to open a SFTP connection (%s)" % to_native(e))
        #
        # try:
        #     self.sftp.get(to_bytes(in_path, errors='surrogate_or_strict'), to_bytes(out_path, errors='surrogate_or_strict'))
        # except IOError:
        #     raise AnsibleError("failed to transfer file from %s" % in_path)

    def _any_keys_added(self):

        for hostname, keys in iteritems(self.ssh._host_keys):
            for keytype, key in iteritems(keys):
                added_this_time = getattr(key, '_added_by_ansible_this_time', False)
                if added_this_time:
                    return True
        return False

    def _save_ssh_host_keys(self, filename):
        '''
        not using the paramiko save_ssh_host_keys function as we want to add new SSH keys at the bottom so folks
        don't complain about it :)
        '''

        if not self._any_keys_added():
            return False

        path = os.path.expanduser("~/.ssh")
        makedirs_safe(path)

        f = open(filename, 'w')

        for hostname, keys in iteritems(self.ssh._host_keys):

            for keytype, key in iteritems(keys):

                # was f.write
                added_this_time = getattr(key, '_added_by_ansible_this_time', False)
                if not added_this_time:
                    f.write("%s %s %s\n" % (hostname, keytype, key.get_base64()))

        for hostname, keys in iteritems(self.ssh._host_keys):

            for keytype, key in iteritems(keys):
                added_this_time = getattr(key, '_added_by_ansible_this_time', False)
                if added_this_time:
                    f.write("%s %s %s\n" % (hostname, keytype, key.get_base64()))

        f.close()

    def reset(self):
        self.close()
        self._connect()

    def close(self):
        ''' terminate the connection '''

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
