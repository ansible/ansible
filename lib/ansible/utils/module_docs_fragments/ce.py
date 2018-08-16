#
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = """
options:
  provider:
    description:
      - A dict object containing connection details.
    suboptions:
      host:
        description:
          - Specifies the DNS host name or address for connecting to the remote
            device over the specified transport.  The value of host is used as
            the destination address for the transport.
        required: true
      port:
        description:
          - Specifies the port to use when building the connection to the remote
            device.  This value applies to either I(cli) or I(netconf).  The port
            value will default to the appropriate transport common port if
            none is provided in the task.  (cli=22, netconf=22).
        default: 0 (use common port)
      username:
        description:
          - Configures the username to use to authenticate the connection to
            the remote device.  This value is used to authenticate the CLI login.
            If the value is not specified in the task, the value of environment
            variable C(ANSIBLE_NET_USERNAME) will be used instead.
      password:
        description:
          - Specifies the password to use to authenticate the connection to
            the remote device.  This is a common argument used for cli
            transports. If the value is not specified in the task, the
            value of environment variable C(ANSIBLE_NET_PASSWORD) will be used instead.
      ssh_keyfile:
        description:
          - Specifies the SSH key to use to authenticate the connection to
            the remote device.  This argument is used for the I(cli)
            transport. If the value is not specified in the task, the
            value of environment variable C(ANSIBLE_NET_SSH_KEYFILE) will be used instead.
      transport:
        description:
          - Configures the transport connection to use when connecting to the
            remote device.  The transport argument supports connectivity to the
            device over cli (ssh).
        required: true
        default: cli

"""
