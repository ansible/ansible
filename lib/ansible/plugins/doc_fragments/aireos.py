# -*- coding: utf-8 -*-

# Copyright: (c) 2017, James Mighion <@jmighion>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
options:
  provider:
    description:
      - A dict object containing connection details.
    suboptions:
      host:
        description:
          - Specifies the DNS host name or address for connecting to the remote device over the specified transport.
          - The value of host is used as the destination address for the transport.
        type: str
        required: true
      port:
        description:
          - Specifies the port to use when building the connection to the remote device.
        type: int
        default: 22
      username:
        description:
          - Configures the username to use to authenticate the connection to the remote device.
          - This value is used to authenticate the SSH session.
          - If the value is not specified in the task, the value of environment variable
            C(ANSIBLE_NET_USERNAME) will be used instead.
        type: str
      password:
        description:
          - Specifies the password to use to authenticate the connection to the remote device.
          - This value is used to authenticate the SSH session.
          - If the value is not specified in the task, the value of environment variable
            C(ANSIBLE_NET_PASSWORD) will be used instead.
        type: str
      timeout:
        description:
          - Specifies the timeout in seconds for communicating with the network device
            for either connecting or sending commands.
          - If the timeout is exceeded before the operation is completed, the module will error.
        type: int
        default: 10
      ssh_keyfile:
        description:
          - Specifies the SSH key to use to authenticate the connection to the remote device.
          - This value is the path to the key used to authenticate the SSH session.
          - If the value is not specified in the task, the value of environment variable
            C(ANSIBLE_NET_SSH_KEYFILE) will be used instead.
        type: path
'''
