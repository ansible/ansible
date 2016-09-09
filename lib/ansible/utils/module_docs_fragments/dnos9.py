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
      - User to authenticate the SSH session to the remote device. If the
        value is not specified in the task, the value of environment variable
        ANSIBLE_NET_USERNAME will be used instead.
    required: false
  password:
    description:
      - Password to authenticate the SSH session to the remote device. If the
        value is not specified in the task, the value of environment variable
        ANSIBLE_NET_PASSWORD will be used instead.
    required: false
    default: null
  ssh_keyfile:
    description:
      - Path to an ssh key used to authenticate the SSH session to the remote
        device.  If the value is not specified in the task, the value of
        environment variable ANSIBLE_NET_SSH_KEYFILE will be used instead.
    required: false
  authorize:
    description:
      - Instructs the module to enter priviledged mode on the remote device
        before sending any commands.  If not specified, the device will
        attempt to excecute all commands in non-priviledged mode. If the value
        is not specified in the task, the value of environment variable
        ANSIBLE_NET_AUTHORIZE will be used instead.
    required: false
    default: no
    choices: ['yes', 'no']
  auth_pass:
    description:
      - Specifies the password to use if required to enter privileged mode
        on the remote device.  If I(authorize) is false, then this argument
        does nothing. If the value is not specified in the task, the value of
        environment variable ANSIBLE_NET_AUTH_PASS will be used instead.
    required: false
    default: none
  timeout:
    description:
      - Specifies idle timeout (in seconds) for the connection. Useful if the
        console freezes before continuing. For example when saving
        configurations.
    required: false
    default: 10
  provider:
    description:
      - Convenience method that allows all M(dnos9) arguments to be passed as
        a dict object.  All constraints (required, choices, etc) must be
        met either by individual arguments or values in this dict.
    required: false
    default: null
"""
