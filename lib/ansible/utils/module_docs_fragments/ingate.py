# Copyright (c) 2018, Ingate Systems AB
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
    DOCUMENTATION = '''
options:
  client:
    description:
      - A dict object containing connection details.
    suboptions:
      version:
        description:
          - REST API version.
        choices: [v1]
        default: v1
        required: true
      scheme:
        description:
          - Which HTTP protocol to use.
        choices: [http, https]
        required: true
      address:
        description:
          - The hostname or IP address to the unit.
        required: true
      username:
        description:
          - The username of the REST API user.
        required: true
      password:
        description:
          - The password for the REST API user.
        required: true
      port:
        description:
          - Which HTTP(S) port to connect to.
        required: false
      timeout:
        description:
          - The timeout (in seconds) for REST API requests.
        required: false
      verify_ssl:
        description:
          - Verify the unit's HTTPS certificate.
        default: true
        required: false
notes:
  - This module requires that the Ingate Python SDK is installed on the
    host. To install the SDK use the pip command from your shell
    C(pip install ingatesdk).
requirements:
  - ingatesdk >= 1.0.6
'''
