#
# (c) 2016, Peter Sprygada <psprygada@ansible.com>
# (c) 2016, Patrick Ogenstad <@ogenstad>
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
        the SSH session. If the value is not specified in the task, the
        value of environment variable ANSIBLE_NET_USERNAME will be used instead.
    required: false
  password:
    description:
      - Specifies the password to use to authenticate the connection to
        the remote device.   The value of I(password) is used to authenticate
        the SSH session. If the value is not specified in the task, the
        value of environment variable ANSIBLE_NET_PASSWORD will be used instead.
    required: false
    default: null
  ssh_keyfile:
    description:
      - Specifies the SSH key to use to authenticate the connection to
        the remote device.   The value of I(ssh_keyfile) is the path to the
        key used to authenticate the SSH session. If the value is not specified
        in the task, the value of environment variable ANSIBLE_NET_SSH_KEYFILE
        will be used instead.
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
      - Specifies idle timeout for the connection. Useful if the console
        freezes before continuing. For example when saving configurations.
    required: false
    default: 10
  provider:
    description:
      - Convience method that allows all M(ios) arguments to be passed as
        a dict object.  All constraints (required, choices, etc) must be
        met either by individual arguments or values in this dict.
    required: false
    default: null
  show_command:
    description:
      - Specifies which command will be used to get the current configuration.
        By default the 'show running-config' command will be used, this command
        masks some passwords. For example ike passwords for VPN. If you need to
        match against masked passwords use 'more system:running-config'.
        Note that the 'more system:running-config' only works in the system
        context if you are running the ASA in multiple context mode.
        before sending any commands.  If not specified, the device will
    required: false
    default: show running-config
    choices: ['show running-config', 'more system:running-config']
  context:
    description:
      - Specifies which context to target if you are running in the ASA in
        multiple context mode. Defaults to the current context you login to.
    required: false
    default: null


"""
