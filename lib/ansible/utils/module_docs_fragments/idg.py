# -*- coding: utf-8 -*-
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
    # IBM DataPower documentation fragment
    DOCUMENTATION = '''
options:
  idg_connection:
    description:
      - A dict object containing connection details.
    required: True
    suboptions:

      password:
        description:
          - The password for the user account used to connect to the
            REST management interface.
        aliases:
            - url_password
        required: True

      server:
        description:
          - The DataPower® Gateway host.
        required: True

      server_port:
        description:
          - The DataPower® Gateway port.
        default: 5554
        required: False

      timeout:
        description:
          - Specifies the timeout in seconds for communicating with the device.
        default: 10

      use_proxy:
        description:
          - Control if the lookup will observe HTTP proxy environment variables when present.
        default: False

      user:
        description:
          - The username to connect to the REST management interface with.
            This user must have administrative privileges.
        aliases:
            - url_username
        required: True

      validate_certs:
        description:
          - Control SSL handshake validation.
        default: True
        type: bool

notes:
  - This documentation was developed mostly from the content
    provided by IBM in its web administration interface.
  - For more information consult the official documentation.
    U(https://www.ibm.com/support/knowledgecenter/SS9H2Y_7.7.0/com.ibm.dp.doc/welcome.html)
'''
