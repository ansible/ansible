#
# (c) 2015, Peter Sprygada <psprygada@ansible.com>
#
# Copyright (c) 2016 Dell Inc.
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
            device.
        default: 22
      username:
        description:
          - User to authenticate the SSH session to the remote device. If the
            value is not specified in the task, the value of environment variable
            C(ANSIBLE_NET_USERNAME) will be used instead.
      password:
        description:
          - Password to authenticate the SSH session to the remote device. If the
            value is not specified in the task, the value of environment variable
            C(ANSIBLE_NET_PASSWORD) will be used instead.
      ssh_keyfile:
        description:
          - Path to an ssh key used to authenticate the SSH session to the remote
            device.  If the value is not specified in the task, the value of
            environment variable C(ANSIBLE_NET_SSH_KEYFILE) will be used instead.
      timeout:
        description:
          - Specifies idle timeout (in seconds) for the connection. Useful if the
            console freezes before continuing. For example when saving
            configurations.
        default: 10
notes:
  - For more information on using Ansible to manage Dell EMC Network devices see U(https://www.ansible.com/ansible-dell-networking).
"""
