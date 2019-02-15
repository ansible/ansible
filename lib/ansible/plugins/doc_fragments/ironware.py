# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Paul Baker <@paulquack>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
options:
  authorize:
    description:
      - B(Deprecated)
      - "Starting with Ansible 2.7 we recommend using C(connection: network_cli) and C(become: yes)."
      - For more information please see the L(IronWare Platform Options guide, ../network/user_guide/platform_ironware.html).
      - HORIZONTALLINE
      - Instructs the module to enter privileged mode on the remote device
        before sending any commands.  If not specified, the device will
        attempt to execute all commands in non-privileged mode. If the value
        is not specified in the task, the value of environment variable
        C(ANSIBLE_NET_AUTHORIZE) will be used instead.
    type: bool
    default: no
  provider:
    description:
      - B(Deprecated)
      - "Starting with Ansible 2.7 we recommend using C(connection: network_cli) and C(become: yes)."
      - For more information please see the L(IronWare Platform Options guide, ../network/user_guide/platform_ironware.html).
      - HORIZONTALLINE
      - A dict object containing connection details.
    type: dict
    suboptions:
      host:
        description:
          - Specifies the DNS host name or address for connecting to the remote
            device over the specified transport.  The value of host is used as
            the destination address for the transport.
        type: str
      port:
        description:
          - Specifies the port to use when building the connection to the remote
            device.
        type: int
        default: 22
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
      ssh_keyfile:
        description:
          - Specifies the SSH key to use to authenticate the connection to
            the remote device.   This value is the path to the
            key used to authenticate the SSH session. If the value is not specified
            in the task, the value of environment variable C(ANSIBLE_NET_SSH_KEYFILE)
            will be used instead.
        type: path
      authorize:
        description:
          - Instructs the module to enter privileged mode on the remote device
            before sending any commands.  If not specified, the device will
            attempt to execute all commands in non-privileged mode. If the value
            is not specified in the task, the value of environment variable
            C(ANSIBLE_NET_AUTHORIZE) will be used instead.
        type: bool
        default: no
      auth_pass:
        description:
          - Specifies the password to use if required to enter privileged mode
            on the remote device.  If I(authorize) is false, then this argument
            does nothing. If the value is not specified in the task, the value of
            environment variable C(ANSIBLE_NET_AUTH_PASS) will be used instead.
        type: str
      timeout:
        description:
          - Specifies idle timeout in seconds for the connection, in seconds. Useful
            if the console freezes before continuing. For example when saving
            configurations.
        type: int
        default: 10
notes:
  - For more information on using Ansible to manage network devices see the :ref:`Ansible Network Guide <network_guide>`
'''
