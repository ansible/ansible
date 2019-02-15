# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
options:
  host:
    description:
      - Specifies the DNS host name or address for connecting to the remote
        device over the specified transport.  The value of host is used as
        the destination address for the transport.
    type: str
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
    type: str
  password:
    description:
      - Specifies the password to use to authenticate the connection to
        the remote device.   This value is used to authenticate
        the SSH session. If the value is not specified in the task, the
        value of environment variable C(ANSIBLE_NET_PASSWORD) will be used instead.
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
        the remote device.   This value is the path to the key
        used to authenticate the SSH session. If the value is not specified in
        the task, the value of environment variable C(ANSIBLE_NET_SSH_KEYFILE)
        will be used instead.
    type: path
  hostkey_verify:
    description:
      - If set to C(yes), the ssh host key of the device must match a ssh key present on
        the host if set to C(no), the ssh host key of the device is not checked.
    type: bool
    default: yes
  look_for_keys:
    description:
      - Enables looking in the usual locations for the ssh keys (e.g. :file:`~/.ssh/id_*`)
    type: bool
    default: yes
notes:
  - For information on using netconf see the :ref:`Platform Options guide using Netconf<netconf_enabled_platform_options>`
  - For more information on using Ansible to manage network devices see the :ref:`Ansible Network Guide <network_guide>`
'''
