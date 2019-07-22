# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
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
        type: str
        required: true
      port:
        description:
          - Specifies the port to use when building the connection to the remote
            device.  This value applies to either I(cli) or I(netconf).  The port
            value will default to the appropriate transport common port if
            none is provided in the task.  (cli=22, netconf=22).
        type: int
        default: 0 (use common port)
      username:
        description:
          - Configures the username to use to authenticate the connection to
            the remote device.  This value is used to authenticate the CLI login.
            If the value is not specified in the task, the value of environment
            variable C(ANSIBLE_NET_USERNAME) will be used instead.
        type: str
      password:
        description:
          - Specifies the password to use to authenticate the connection to
            the remote device.  This is a common argument used for cli
            transports. If the value is not specified in the task, the
            value of environment variable C(ANSIBLE_NET_PASSWORD) will be used instead.
        type: str
      ssh_keyfile:
        description:
          - Specifies the SSH key to use to authenticate the connection to
            the remote device.  This argument is used for the I(cli)
            transport. If the value is not specified in the task, the
            value of environment variable C(ANSIBLE_NET_SSH_KEYFILE) will be used instead.
        type: path
      transport:
        description:
          - Configures the transport connection to use when connecting to the
            remote device.  The transport argument supports connectivity to the
            device over cli (ssh).
        type: str
        required: true
        choices: [ cli, netconf ]
        default: cli
'''
