# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Peter Sprygada <psprygada@ansible.com>
# Copyright: (c) 2016, Dell Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
options:
  provider:
    description:
      - A dict object containing connection details.
    type: dict
    suboptions:
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
            device.
        type: int
        default: 22
      username:
        description:
          - User to authenticate the SSH session to the remote device. If the
            value is not specified in the task, the value of environment variable
            C(ANSIBLE_NET_USERNAME) will be used instead.
        type: str
      password:
        description:
          - Password to authenticate the SSH session to the remote device. If the
            value is not specified in the task, the value of environment variable
            C(ANSIBLE_NET_PASSWORD) will be used instead.
        type: str
      ssh_keyfile:
        description:
          - Path to an ssh key used to authenticate the SSH session to the remote
            device.  If the value is not specified in the task, the value of
            environment variable C(ANSIBLE_NET_SSH_KEYFILE) will be used instead.
        type: path
      timeout:
        description:
          - Specifies idle timeout (in seconds) for the connection. Useful if the
            console freezes before continuing. For example when saving
            configurations.
        type: int
        default: 10
notes:
  - For more information on using Ansible to manage Dell EMC Network devices see U(https://www.ansible.com/ansible-dell-networking).
'''
