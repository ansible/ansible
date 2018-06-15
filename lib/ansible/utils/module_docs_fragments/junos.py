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
  provider:
    description:
      - B(Deprecated)
      - "Starting with Ansible 2.5 we recommend using C(connection: network_cli) or C(connection: netconf)."
      - For more information please see the L(Junos OS Platform Options guide, ../network/user_guide/platform_junos.html).
      - HORIZONTALLINE
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
            device.  The port value will default to the well known SSH port
            of 22 (for C(transport=cli)) or port 830 (for C(transport=netconf))
            device.
        default: 22
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
        default: 10
      ssh_keyfile:
        description:
          - Specifies the SSH key to use to authenticate the connection to
            the remote device.   This value is the path to the key
            used to authenticate the SSH session. If the value is not specified in
            the task, the value of environment variable C(ANSIBLE_NET_SSH_KEYFILE)
            will be used instead.
notes:
  - For information on using CLI and netconf see the :ref:`Junos OS Platform Options guide <junos_platform_options>`
  - For more information on using Ansible to manage network devices see the :ref:`Ansible Network Guide <network_guide>`
  - For more information on using Ansible to manage Juniper network devices see U(https://www.ansible.com/ansible-juniper).
"""
