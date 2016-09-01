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
        device.
    required: false
    default: 22
  username:
    description:
      - Configures the username to use to authenticate the connection to
        the remote device.  The value of I(username) is used to authenticate
        the SSH session. If the value is not specified in the task, the
        value of environment variable C(ANSIBLE_NET_USERNAME) will be used instead.
    required: false
  password:
    description:
      - Specifies the password to use to authenticate the connection to
        the remote device.   The value of I(password) is used to authenticate
        the SSH session. If the value is not specified in the task, the
        value of environment variable C(ANSIBLE_NET_PASSWORD) will be used instead.
    required: false
    default: null
  ssh_keyfile:
    description:
      - Specifies the SSH key to use to authenticate the connection to
        the remote device.   The value of I(ssh_keyfile) is the path to the
        key used to authenticate the SSH session. If the value is not specified
        in the task, the value of environment variable C(ANSIBLE_NET_SSH_KEYFILE)
        will be used instead.
    required: false
  provider:
    description:
      - Convenience method that allows all I(iosxr) arguments to be passed as
        a dict object.  All constraints (required, choices, etc) must be
        met either by individual arguments or values in this dict.
    required: false
    default: null

  """
