# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
options:
    remote_addr:
        description:
            - Address of the remote target
        vars:
            - name: inventory_hostname
            - name: ansible_host
            - name: ansible_ssh_host
            - name: ansible_paramiko_host
            - name: delegated_vars['ansible_host']
            - name: delegated_vars['ansible_ssh_host']
            - name: delegated_vars['ansible_paramiko_host']
    remote_user:
        description:
            - User to login/authenticate as
            - Can be set from the CLI via the C(--user) or C(-u) options.
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
    password:
        description:
          - Secret used to either login the ssh server or as a passphrase for ssh keys that require it
          - Can be set from the CLI via the C(--ask-pass) option.
        vars:
            - name: ansible_password
            - name: ansible_ssh_pass
            - name: ansible_ssh_password
            - name: ansible_paramiko_pass
            - name: ansible_paramiko_password
              version_added: '2.5'
    host_key_auto_add:
        description: 'TODO: write it'
        env: [{name: ANSIBLE_PARAMIKO_HOST_KEY_AUTO_ADD}]
        ini:
          - {key: host_key_auto_add, section: paramiko_connection}
        type: boolean
    look_for_keys:
        default: True
        description: 'TODO: write it'
        env: [{name: ANSIBLE_PARAMIKO_LOOK_FOR_KEYS}]
        ini:
        - {key: look_for_keys, section: paramiko_connection}
        type: boolean
    proxy_command:
        default: ''
        description:
            - Proxy information for running the connection via a jumphost
            - Also this plugin will scan 'ssh_args', 'ssh_extra_args' and 'ssh_common_args' from the 'ssh' plugin settings for proxy information if set.
        env: [{name: ANSIBLE_PARAMIKO_PROXY_COMMAND}]
        ini:
          - {key: proxy_command, section: paramiko_connection}
    pty:
        default: True
        description: 'TODO: write it'
        env:
          - name: ANSIBLE_PARAMIKO_PTY
        ini:
          - section: paramiko_connection
            key: pty
        type: boolean
    record_host_keys:
        default: True
        description: 'TODO: write it'
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
    timeout:
        type: int
        description:
            - Sets the connection time, in seconds, for communicating with the remote device.
              This timeout is used as the default timeout value for commands when issuing a command to the network CLI.
              If the command does not return in timeout seconds, an error is generated.
        default: 120
    port:
        description:
            - Port on which ssh server is listening on
        default: 22
        type: int
        vars:
            - name: ansible_port
            - name: ansible_ssh_port
            - name: ansible_paramiko_port
              version_added: '2.8'
        env:
            - name: ANSIBLE_REMOTE_PORT
            - name: ANSIBLE_PARAMIKO_REMOTE_PORT
              version_added: '2.8'
        ini:
            - key: remote_port
              section: defaults
            - key: remote_port
              section: paramiko_connection
              version_added: '2.8'
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
'''
