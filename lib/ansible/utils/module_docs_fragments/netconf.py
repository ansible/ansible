#
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
        device.  The port value will default to port 830.
    type: int
    default: 830
  username:
    description:
      - Configures the username to use to authenticate the connection to
        the remote device.  This value is used to authenticate
        the SSH session. If the value is not specified in the task, the
        value of environment variable C(ANSIBLE_NET_USERNAME) will be used instead.
  password:
    description:
      - Specifies the password to use to authenticate the connection to
        the remote device.   This value is used to authenticate
        the SSH session. If the value is not specified in the task, the
        value of environment variable C(ANSIBLE_NET_PASSWORD) will be used instead.
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
        the remote device.   This value is the path to the key
        used to authenticate the SSH session. If the value is not specified in
        the task, the value of environment variable C(ANSIBLE_NET_SSH_KEYFILE)
        will be used instead.
    type: path
  hostkey_verify:
    description:
      - If set to true, the ssh host key of the device must match a ssh key present on
        the host if false, the ssh host key of the device is not checked.
    type: bool
    default: True
  look_for_keys:
    description:
      - Enables looking in the usual locations for the ssh keys (e.g. :file:`~/.ssh/id_*`)
    type: bool
    default: True
notes:
  - For information on using netconf see the :ref:`Platform Options guide using Netconf<netconf_enabled_platform_options>`
  - For more information on using Ansible to manage network devices see the :ref:`Ansible Network Guide <network_guide>`
"""
