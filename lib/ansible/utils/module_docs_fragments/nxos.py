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
    required: false
    default: 0 (use common port)
  username:
    description:
      - Configures the username to use to authenticate the connection to
        the remote device.  This value is used to authenticate
        either the CLI login or the nxapi authentication depending on which
        transport is used. If the value is not specified in the task, the
        value of environment variable C(ANSIBLE_NET_USERNAME) will be used instead.
    required: false
  password:
    description:
      - Specifies the password to use to authenticate the connection to
        the remote device.  This is a common argument used for either I(cli)
        or I(nxapi) transports. If the value is not specified in the task, the
        value of environment variable C(ANSIBLE_NET_PASSWORD) will be used instead.
    required: false
    default: null
  timeout:
    description:
      - Specifies the timeout in seconds for communicating with the network device
        for either connecting or sending commands.  If the timeout is
        exceeded before the operation is completed, the module will error.
        NX-API can be slow to return on long-running commands (sh mac, sh bgp, etc).
    require: false
    default: 10
    version_added: 2.3
  ssh_keyfile:
    description:
      - Specifies the SSH key to use to authenticate the connection to
        the remote device.  This argument is only used for the I(cli)
        transport. If the value is not specified in the task, the
        value of environment variable C(ANSIBLE_NET_SSH_KEYFILE) will be used instead.
    required: false
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
    required: false
    default: no
    choices: ['yes', 'no']
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used
        on personally controlled sites using self-signed certificates.  If the transport
        argument is not nxapi, this value is ignored.
    choices: ['yes', 'no']
  provider:
    description:
      - Convenience method that allows all I(nxos) arguments to be passed as
        a dict object.  All constraints (required, choices, etc) must be
        met either by individual arguments or values in this dict.
    required: false
    default: null

"""
