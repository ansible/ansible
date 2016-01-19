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
        device.  The port value will default to the well known SSH port
        of 22
    required: false
    default: 22
  username:
    description:
      - Configures the usename to use to authenticate the connection to
        the remote device.  The value of I(username) is used to authenticate
        the SSH session
    required: true
  password:
    description:
      - Specifies the password to use when authentication the connection to
        the remote device.   The value of I(password) is used to authenticate
        the SSH session
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
  provider:
    description:
      - Convience method that allows all M(ios) arguments to be passed as
        a dict object.  All constraints (required, choices, etc) must be
        met either by individual arguments or values in this dict.
    required: false
    default: null

"""
