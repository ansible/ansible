# Copyright: (c) 2018, Anthony ARNAUD <github@anthony-arnaud.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    connection: sshchroot
    short_description: connect via chroot over ssh client binary
    description:
        - This connection plugin allows ansible to communicate to the target machines via chroot through
        - normal ssh command line. Useful with a debootstrap installation
    author: Anthony ARNAUD  (@bluelogon)
    version_added: 2.8
    options:
      host:
          description: Hostname/ip with chroot path to connect to.
          default: inventory_hostname
          vars:
               - name: ansible_host
               - name: ansible_ssh_host
      host_key_checking:
          #constant: HOST_KEY_CHECKING
          description: Determines if ssh should check host keys
          type: boolean
          ini:
              - section: defaults
                key: 'host_key_checking'
          env:
              - name: ANSIBLE_HOST_KEY_CHECKING
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
          yaml: {key: ssh_connection.ssh_executable}
          #const: ANSIBLE_SSH_EXECUTABLE
          version_added: "2.2"
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
          env: [{name: ANSIBLE_SSH_PIPELINING}]
          ini:
          - {key: pipelining, section: ssh_connection}
          type: boolean
          vars: [{name: ansible_ssh_pipelining}]
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
        default: null
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
        default: True
        description: 'TODO: write it'
        env: [{name: ANSIBLE_SFTP_BATCH_MODE}]
        ini:
        - {key: sftp_batch_mode, section: ssh_connection}
        type: boolean
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
      chroot_executable:
        default: "/usr/sbin/chroot"
        description:
          - This defines the location of the chroot binary.
        env:
         - name: ANSIBLE_CHROOT_EXECUTABLE
        ini:
          - {key: chroot_executable, section: ssh_connection}
        vars:
          - name: chroot_executable
      chroot_path:
        description:
          - This defines the location of the chroot binary.
        env:
          - name: ANSIBLE_CHROOT_PATH
        ini:
          - {key: chroot_path, section: ssh_connection}
        vars:
          - name: chroot_path
'''

EXAMPLES = '''
# with inventory file content:
# > server01 chroot_path=/mnt/debian_9
# Use this plugin in your playbook like this:
- name: Manage a deboostrap debian9 with chroot in /mnt/debian_9 on server01
  host: server01
  connection: sshchroot
'''

import sys
from ansible.errors import AnsibleError
from ansible.plugins.connection.ssh import Connection as SSHConnection
from ansible import constants as C
from ansible.utils.display import Display
display = Display()


# this _has to be_ named Connection
class Connection(SSHConnection):
    ''' SSH chroot based connections '''

    transport = 'sshchroot'
    has_pipelining = True
    # su currently has an undiagnosed issue with calculating the file
    # checksums (so copy, for instance, doesn't work right)
    # Have to look into that before re-enabling this
    become_methods = frozenset(C.BECOME_METHODS).difference(('su',))

    def _bare_run(self, cmd, in_data, sudoable=True, checkrc=True):
        chroot_bin = self.get_option('chroot_executable')
        chroot_path = self.get_option('chroot_path')
        self._play_context.ssh_transfer_method = "piped"

        if chroot_path is None:
            raise AnsibleError("chroot_path is mandatory")
        # split command to inject chroot
        # last value before the command is host
        host_index = cmd.index(self.host.encode(sys.getfilesystemencoding())) + 1
        new_cmd = cmd[:host_index] + [chroot_bin, chroot_path] + cmd[host_index:]

        return super(Connection, self)._bare_run(new_cmd, in_data, sudoable, checkrc)
