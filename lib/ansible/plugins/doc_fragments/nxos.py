# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Peter Sprygada <psprygada@ansible.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
options:
  provider:
    description:
      - B(Deprecated)
      - "Starting with Ansible 2.5 we recommend using C(connection: network_cli)."
      - This option is only required if you are using NX-API.
      - For more information please see the L(NXOS Platform Options guide, ../network/user_guide/platform_nxos.html).
      - HORIZONTALLINE
      - A dict object containing connection details.
    type: dict
    suboptions:
      host:
        description:
          - Specifies the DNS host name or address for connecting to the remote
            device over the specified transport.  The value of host is used as
            the destination address for the transport.
        type: str
        required: true
      port:
        description:
          - Specifies the port to use when building the connection to the remote
            device.  This value applies to either I(cli) or I(nxapi).  The port
            value will default to the appropriate transport common port if
            none is provided in the task.  (cli=22, http=80, https=443).
        type: int
        default: 0 (use common port)
      username:
        description:
          - Configures the username to use to authenticate the connection to
            the remote device.  This value is used to authenticate
            either the CLI login or the nxapi authentication depending on which
            transport is used. If the value is not specified in the task, the
            value of environment variable C(ANSIBLE_NET_USERNAME) will be used instead.
        type: str
      password:
        description:
          - Specifies the password to use to authenticate the connection to
            the remote device.  This is a common argument used for either I(cli)
            or I(nxapi) transports. If the value is not specified in the task, the
            value of environment variable C(ANSIBLE_NET_PASSWORD) will be used instead.
        type: str
      authorize:
        description:
          - Instructs the module to enter privileged mode on the remote device
            before sending any commands.  If not specified, the device will
            attempt to execute all commands in non-privileged mode. If the value
            is not specified in the task, the value of environment variable
            C(ANSIBLE_NET_AUTHORIZE) will be used instead.
        type: bool
        default: no
        version_added: '2.5.3'
      auth_pass:
        description:
          - Specifies the password to use if required to enter privileged mode
            on the remote device.  If I(authorize) is false, then this argument
            does nothing. If the value is not specified in the task, the value of
            environment variable C(ANSIBLE_NET_AUTH_PASS) will be used instead.
        type: str
        version_added: '2.5.3'
      timeout:
        description:
          - Specifies the timeout in seconds for communicating with the network device
            for either connecting or sending commands.  If the timeout is
            exceeded before the operation is completed, the module will error.
            NX-API can be slow to return on long-running commands (sh mac, sh bgp, etc).
        type: int
        default: 10
        version_added: '2.3'
      ssh_keyfile:
        description:
          - Specifies the SSH key to use to authenticate the connection to
            the remote device.  This argument is only used for the I(cli)
            transport. If the value is not specified in the task, the
            value of environment variable C(ANSIBLE_NET_SSH_KEYFILE) will be used instead.
        type: str
      transport:
        description:
          - Configures the transport connection to use when connecting to the
            remote device.  The transport argument supports connectivity to the
            device over cli (ssh) or nxapi.
        type: str
        required: true
        choices: [ cli, nxapi ]
        default: cli
      use_ssl:
        description:
          - Configures the I(transport) to use SSL if set to C(yes) only when the
            C(transport=nxapi), otherwise this value is ignored.
        type: bool
        default: no
      validate_certs:
        description:
          - If C(no), SSL certificates will not be validated. This should only be used
            on personally controlled sites using self-signed certificates.  If the transport
            argument is not nxapi, this value is ignored.
        type: bool
        default: yes
      use_proxy:
        description:
          - If C(no), the environment variables C(http_proxy) and C(https_proxy) will be ignored.
        type: bool
        default: yes
        version_added: "2.5"

notes:
  - For information on using CLI and NX-API see the :ref:`NXOS Platform Options guide <nxos_platform_options>`
  - For more information on using Ansible to manage network devices see the :ref:`Ansible Network Guide <network_guide>`
  - For more information on using Ansible to manage Cisco devices see the `Cisco integration page <https://www.ansible.com/integrations/networks/cisco>`_.
'''
