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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = """
options:
  provider:
    description:
      - A dict object containing connection details.
    type: dict
    suboptions:
      server_endpoint:
        description:
          - Specifies the DNS host name or address for connecting to the remote
            tetration cluster
          - Value can also be specified using C(TETRATION_SERVER_ENDPOINT) environment
            variable.
        aliases:
          - endpoint
          - host
        type: str
        required: true
      api_key:
        description:
          - API Key used for tetration authentication
          - Value can also be specified using C(TETRATION_API_KEY) environment
            variable.
        type: str
        required: true
      api_secret:
        description:
          - Specifies the API secret used for tetration authentication
          - Value can also be specified using C(TETRATION_API_SECRET) environment
            variable.
        type: str
        required: true
      verify:
        description:
          - Boolean value to enable or disable verifying SSL certificates
          - Value can also be specified using C(TETRATION_VERIFY) environment
            variable.
        type: bool
        default: 'no'
      silent_ssl_warnings:
        description:
          - Specifies whether to ignore ssl warnings
        required: false
        type: bool
        default: True
      timeout:
        description:
          - The amount of time before to wait before receiving a response
          - Value can also be specified using C(TETRATION_TIMEOUT) environment
            variable.
        type: int
        default: 10
      max_retries:
        description:
          - Configures the number of attempted retries before the connection
            is declared usable
          - Value can also be specified using C(TETRATION_MAX_RETRIES) environment
            variable.
        type: int
        default: 3
      api_version:
        description:
          - Specifies the version of Tetration OpenAPI to use
          - Value can also be specified using C(TETRATION_API_VERSION) environment
            variable.
        type: str
        default: v1
notes:
  - "This module must be run locally, which can be achieved by specifying C(connection: local)."
  - Please read the :ref:`tetration_guide` for more detailed information on how to use Tetration with Ansible.

requirements:
  - tetpyclient
"""
