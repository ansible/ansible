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
      - A dict object containing connection details.
    default: null
    suboptions:
      host:
        description:
          - Specifies the DNS host name or address for connecting to the remote
            instance of NIOS WAPI over REST
        required: true
      username:
        description:
          - Configures the username to use to authenticate the connection to
            the remote instance of NIOS.
      password:
        description:
          - Specifies the password to use to authenticate the connection to
            the remote instance of NIOS.
        default: null
      ssl_verify:
        description:
          - Boolean value to enable or disable verifying SSL certificates
        required: false
        default: false
      http_request_timeout:
        description:
          - The amount of time before to wait before receiving a response
        required: false
        default: 10
      max_retries:
        description:
          - Configures the number of attempted retries before the connection
            is declared usable
        required: false
        default: 3
      wapi_version:
        description:
          - Specifies the version of WAPI to use
        required: false
        default: 1.4
"""
