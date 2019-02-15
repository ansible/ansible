# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Peter Sprygada <psprygada@ansible.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
options:
  authorize:
    description:
      - B(Deprecated)
      - "Starting with Ansible 2.5 we recommend using C(connection: network_cli) and C(become: yes)."
      - This option is only required if you are using eAPI.
      - For more information please see the L(EOS Platform Options guide, ../network/user_guide/platform_eos.html).
      - HORIZONTALLINE
      - Instructs the module to enter privileged mode on the remote device
        before sending any commands.  If not specified, the device will
        attempt to execute all commands in non-privileged mode. If the value
        is not specified in the task, the value of environment variable
        C(ANSIBLE_NET_AUTHORIZE) will be used instead.
    type: bool
    default: no
  auth_pass:
    description:
      - B(Deprecated)
      - "Starting with Ansible 2.5 we recommend using C(connection: network_cli) and C(become: yes) with C(become_pass)."
      - This option is only required if you are using eAPI.
      - For more information please see the L(EOS Platform Options guide, ../network/user_guide/platform_eos.html).
      - HORIZONTALLINE
      - Specifies the password to use if required to enter privileged mode
        on the remote device.  If I(authorize) is false, then this argument
        does nothing. If the value is not specified in the task, the value of
        environment variable C(ANSIBLE_NET_AUTH_PASS) will be used instead.
    type: str
  provider:
    description:
      - B(Deprecated)
      - "Starting with Ansible 2.5 we recommend using C(connection: network_cli)."
      - This option is only required if you are using eAPI.
      - For more information please see the L(EOS Platform Options guide, ../network/user_guide/platform_eos.html).
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
        required: true
      port:
        description:
          - Specifies the port to use when building the connection to the remote
            device.  This value applies to either I(cli) or I(eapi).  The port
            value will default to the appropriate transport common port if
            none is provided in the task.  (cli=22, http=80, https=443).
        type: int
        default: 0 (use common port)
      username:
        description:
          - Configures the username to use to authenticate the connection to
            the remote device.  This value is used to authenticate
            either the CLI login or the eAPI authentication depending on which
            transport is used. If the value is not specified in the task, the
            value of environment variable C(ANSIBLE_NET_USERNAME) will be used instead.
        type: str
      password:
        description:
          - Specifies the password to use to authenticate the connection to
            the remote device.  This is a common argument used for either I(cli)
            or I(eapi) transports. If the value is not specified in the task, the
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
          - Specifies the SSH keyfile to use to authenticate the connection to
            the remote device.  This argument is only used for I(cli) transports.
            If the value is not specified in the task, the value of environment
            variable C(ANSIBLE_NET_SSH_KEYFILE) will be used instead.
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
      transport:
        description:
          - Configures the transport connection to use when connecting to the
            remote device.
        required: true
        type: str
        choices: [ cli, eapi ]
        default: cli
      use_ssl:
        description:
          - Configures the I(transport) to use SSL if set to C(yes) only when the
            C(transport=eapi).  If the transport
            argument is not eapi, this value is ignored.
        type: bool
        default: yes
      validate_certs:
        description:
          - If C(no), SSL certificates will not be validated. This should only be used
            on personally controlled sites using self-signed certificates.  If the transport
            argument is not eapi, this value is ignored.
        type: bool
      use_proxy:
        description:
          - If C(no), the environment variables C(http_proxy) and C(https_proxy) will be ignored.
        type: bool
        default: yes
        version_added: "2.5"

notes:
  - For information on using CLI, eAPI and privileged mode see the :ref:`EOS Platform Options guide <eos_platform_options>`
  - For more information on using Ansible to manage network devices see the :ref:`Ansible Network Guide <network_guide>`
  - For more information on using Ansible to manage Arista EOS devices see the `Arista integration page <https://www.ansible.com/ansible-arista-networks>`_.

'''
