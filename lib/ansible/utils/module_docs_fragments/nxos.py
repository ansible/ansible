#
# (c) 2015, Peter Sprygada <psprygada@ansible.com>
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
      - B(Deprecated)
      - "Starting with Ansible 2.5 we recommend using C(connection: network_cli)."
      - This option is only required if you are using NX-API.
      - For more information please see the L(NXOS Platform Options guide, ../network/user_guide/platform_nxos.html).
      - HORIZONTALLINE
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
            device.  This value applies to either I(cli) or I(nxapi).  The port
            value will default to the appropriate transport common port if
            none is provided in the task.  (cli=22, http=80, https=443).
        default: 0 (use common port)
      username:
        description:
          - Configures the username to use to authenticate the connection to
            the remote device.  This value is used to authenticate
            either the CLI login or the nxapi authentication depending on which
            transport is used. If the value is not specified in the task, the
            value of environment variable C(ANSIBLE_NET_USERNAME) will be used instead.
      password:
        description:
          - Specifies the password to use to authenticate the connection to
            the remote device.  This is a common argument used for either I(cli)
            or I(nxapi) transports. If the value is not specified in the task, the
            value of environment variable C(ANSIBLE_NET_PASSWORD) will be used instead.
      authorize:
        description:
          - Instructs the module to enter privileged mode on the remote device
            before sending any commands.  If not specified, the device will
            attempt to execute all commands in non-privileged mode. If the value
            is not specified in the task, the value of environment variable
            C(ANSIBLE_NET_AUTHORIZE) will be used instead.
        type: bool
        default: no
        choices: ['yes', 'no']
        version_added: 2.5.3
      auth_pass:
        description:
          - Specifies the password to use if required to enter privileged mode
            on the remote device.  If I(authorize) is false, then this argument
            does nothing. If the value is not specified in the task, the value of
            environment variable C(ANSIBLE_NET_AUTH_PASS) will be used instead.
        default: none
        version_added: 2.5.3
      timeout:
        description:
          - Specifies the timeout in seconds for communicating with the network device
            for either connecting or sending commands.  If the timeout is
            exceeded before the operation is completed, the module will error.
            NX-API can be slow to return on long-running commands (sh mac, sh bgp, etc).
        default: 10
        version_added: 2.3
      ssh_keyfile:
        description:
          - Specifies the SSH key to use to authenticate the connection to
            the remote device.  This argument is only used for the I(cli)
            transport. If the value is not specified in the task, the
            value of environment variable C(ANSIBLE_NET_SSH_KEYFILE) will be used instead.
      transport:
        description:
          - Configures the transport connection to use when connecting to the
            remote device.  The transport argument supports connectivity to the
            device over cli (ssh) or nxapi.
        required: true
        default: cli
      use_ssl:
        description:
          - Configures the I(transport) to use SSL if set to true only when the
            C(transport=nxapi), otherwise this value is ignored.
        type: bool
        default: 'no'
      validate_certs:
        description:
          - If C(no), SSL certificates will not be validated. This should only be used
            on personally controlled sites using self-signed certificates.  If the transport
            argument is not nxapi, this value is ignored.
        type: bool
      use_proxy:
        description:
          - If C(no), the environment variables C(http_proxy) and C(https_proxy) will be ignored.
        type: bool
        default: 'yes'
        version_added: "2.5"

notes:
  - For information on using CLI and NX-API see the :ref:`NXOS Platform Options guide <nxos_platform_options>`
  - For more information on using Ansible to manage network devices see the :ref:`Ansible Network Guide <network_guide>`
  - For more information on using Ansible to manage Cisco devices see the `Cisco integration page <https://www.ansible.com/integrations/networks/cisco>`_.
"""
