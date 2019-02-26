# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Peter Sprygada <psprygada@ansible.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
options:
  host:
    description:
      - Specifies the DNS host name or address for connecting to the remote
        device over the specified transport.  The value of host is used as
        the destination address for the transport.  Note this argument
        does not affect the SSH argument.
    type: str
  port:
    description:
      - Specifies the port to use when building the connection to the remote
        device.  This value applies to either I(cli) or I(rest).  The port
        value will default to the appropriate transport common port if
        none is provided in the task.  (cli=22, http=80, https=443).  Note
        this argument does not affect the SSH transport.
    type: int
    default: 0 (use common port)
  username:
    description:
      - Configures the username to use to authenticate the connection to
        the remote device.  This value is used to authenticate
        either the CLI login or the eAPI authentication depending on which
        transport is used. Note this argument does not affect the SSH
        transport. If the value is not specified in the task, the value of
        environment variable C(ANSIBLE_NET_USERNAME) will be used instead.
    type: str
  password:
    description:
      - Specifies the password to use to authenticate the connection to
        the remote device.  This is a common argument used for either I(cli)
        or I(rest) transports.  Note this argument does not affect the SSH
        transport. If the value is not specified in the task, the value of
        environment variable C(ANSIBLE_NET_PASSWORD) will be used instead.
    type: str
  timeout:
    description:
      - Specifies the timeout in seconds for communicating with the network device
        for either connecting or sending commands.  If the timeout is
        exceeded before the operation is completed, the module will error.
    type: int
    default: 10
  ssh_keyfile:
    description:
      - Specifies the SSH key to use to authenticate the connection to
        the remote device.  This argument is only used for the I(cli)
        transports. If the value is not specified in the task, the value of
        environment variable C(ANSIBLE_NET_SSH_KEYFILE) will be used instead.
    type: path
  transport:
    description:
      - Configures the transport connection to use when connecting to the
        remote device.  The transport argument supports connectivity to the
        device over ssh, cli or REST.
    required: true
    type: str
    choices: [ cli, rest, ssh ]
    default: ssh
  use_ssl:
    description:
      - Configures the I(transport) to use SSL if set to C(yes) only when the
        I(transport) argument is configured as rest.  If the transport
        argument is not I(rest), this value is ignored.
    type: bool
    default: yes
  provider:
    description:
      - Convenience method that allows all I(openswitch) arguments to be passed as
        a dict object.  All constraints (required, choices, etc) must be
        met either by individual arguments or values in this dict.
    type: dict
'''
