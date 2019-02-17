# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):
    # Standard F5 documentation fragment
    DOCUMENTATION = r'''
options:
  password:
    description:
      - The password for the user account used to connect to the BIG-IP.
      - You may omit this option by setting the environment variable C(F5_PASSWORD).
    type: str
    required: true
    aliases: [ pass, pwd ]
  server:
    description:
      - The BIG-IP host.
      - You may omit this option by setting the environment variable C(F5_SERVER).
    type: str
    required: true
  server_port:
    description:
      - The BIG-IP server port.
      - You may omit this option by setting the environment variable C(F5_SERVER_PORT).
    type: int
    default: 443
    version_added: '2.2'
  user:
    description:
      - The username to connect to the BIG-IP with. This user must have
        administrative privileges on the device.
      - You may omit this option by setting the environment variable C(F5_USER).
    type: str
    required: true
  validate_certs:
    description:
      - If C(no), SSL certificates are not validated. Use this only
        on personally controlled sites using self-signed certificates.
      - You may omit this option by setting the environment variable
        C(F5_VALIDATE_CERTS).
    type: bool
    default: yes
    version_added: '2.0'
  provider:
    description:
      - A dict object containing connection details.
    type: dict
    version_added: '2.5'
    suboptions:
      password:
        description:
          - The password for the user account used to connect to the BIG-IP.
          - You may omit this option by setting the environment variable C(F5_PASSWORD).
        type: str
        required: true
        aliases: [ pass, pwd ]
      server:
        description:
          - The BIG-IP host.
          - You may omit this option by setting the environment variable C(F5_SERVER).
        type: str
        required: true
      server_port:
        description:
          - The BIG-IP server port.
          - You may omit this option by setting the environment variable C(F5_SERVER_PORT).
        type: int
        default: 443
      user:
        description:
          - The username to connect to the BIG-IP with. This user must have
            administrative privileges on the device.
          - You may omit this option by setting the environment variable C(F5_USER).
        type: str
        required: true
      validate_certs:
        description:
          - If C(no), SSL certificates are not validated. Use this only
            on personally controlled sites using self-signed certificates.
          - You may omit this option by setting the environment variable C(F5_VALIDATE_CERTS).
        type: bool
        default: yes
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
          - You may omit this option by setting the environment variable C(ANSIBLE_NET_SSH_KEYFILE).
        type: path
      transport:
        description:
          - Configures the transport connection to use when connecting to the
            remote device.
        type: str
        choices: [ cli, rest ]
        default: rest
notes:
  - For more information on using Ansible to manage F5 Networks devices see U(https://www.ansible.com/integrations/networks/f5).
  - Requires BIG-IP software version >= 12.
  - The F5 modules only manipulate the running configuration of the F5 product. To ensure that BIG-IP
    specific configuration persists to disk, be sure to include at least one task that uses the
    M(bigip_config) module to save the running configuration. Refer to the module's documentation for
    the correct usage of the module to save your running configuration.
'''
