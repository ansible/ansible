from __future__ import (absolute_import, division, print_function)

from ansible import constants as C
from ansible.plugins.connection.chroot import Connection as ChrootConnection

__metaclass__ = type

DOCUMENTATION = """
    author: Lars Kellogg-Stedman <lars@redhat.com>
    connection: nspawn
    short_description: Interact with local systemd-nspawn container
    description:
        - Run commands or put/fetch files to an existing systemd-nspawn
          container on the Ansible controller. Unlike the chroot driver,
          this will ensure that /proc, /sys, and /dev are all properly
          configured.
        - Set "ansible_nspawn_extra_args" to pass additional arguments to
          systemd-nspawn (e.g., --bind, --private-network, --private-user,
          etc).
    version_added: "2.8"
    options:
      remote_addr:
        description:
            - The path of the chroot you want to access
        default: inventory_hostname
        vars:
            - name: ansible_host
      executable:
        description:
            - User specified executable shell (defaults to /bin/sh)
        ini:
          - section: defaults
            key: executable
        env:
          - name: ANSIBLE_EXECUTABLE
        vars:
          - name: ansible_executable
      nspawn_extra_args:
        description:
          - Extra command line arguments to pass to systemd-nspawn
        env:
          - name: ANSIBLE_NSPAWN_EXTRA_ARGS
        vars:
          - name: ansible_nspawn_extra_args
"""


class Connection(ChrootConnection):
    transport = 'nspawn'
    transport_cmd = 'systemd-nspawn'

    def _local_command(self, cmd):
        executable = (C.DEFAULT_EXECUTABLE.split()[0]
                      if C.DEFAULT_EXECUTABLE
                      else '/bin/sh')

        extra_args = []

        if self.get_option('nspawn_extra_args'):
            extra_args = self.get_option('nspawn_extra_args').split()

        return ([self._transport_cmd] +
                extra_args +
                ['-D', self.chroot, executable, '-c', cmd])
