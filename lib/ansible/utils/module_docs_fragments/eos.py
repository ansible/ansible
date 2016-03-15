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
      - Specifies the port to use when buiding the connection to the remote
        device.  This value applies to either I(cli) or I(eapi).  The port
        value will default to the approriate transport common port if
        none is provided in the task.  (cli=22, http=80, https=443).
    required: false
    default: 0 (use common port)
  username:
    description:
      - Configures the usename to use to authenticate the connection to
        the remote device.  The value of I(username) is used to authenticate
        either the CLI login or the eAPI authentication depending on which
        transport is used.
    required: true
  password:
    description:
      - Specifies the password to use when authentication the connection to
        the remote device.  This is a common argument used for either I(cli)
        or I(eapi) transports.
    required: false
    default: null
  authorize:
    description:
      - Instructs the module to enter priviledged mode on the remote device
        before sending any commands.  If not specified, the device will
        attempt to excecute all commands in non-priviledged mode.
    required: false
    default: false
    choices: BOOLEANS
  auth_pass:
    description:
      - Specifies the password to use if required to enter privileged mode
        on the remote device.  If I(authorize) is false, then this argument
        does nothing
    required: false
    default: none
  transport:
    description:
      - Configures the transport connection to use when connecting to the
        remote device.  The transport argument supports connectivity to the
        device over cli (ssh) or eapi.
    required: true
    default: cli
  use_ssl:
    description:
      - Configures the I(transport) to use SSL if set to true only when the
        I(transport) argument is configured as eapi.  If the transport
        argument is not eapi, this value is ignored
    required: false
    default: true
    choices: BOOLEANS
  provider:
    description:
      - Convience method that allows all M(eos) arguments to be passed as
        a dict object.  All constraints (required, choices, etc) must be
        met either by individual arguments or values in this dict.
    required: false
    default: null

"""
