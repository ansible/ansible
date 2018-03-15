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
    suboptions:
      host:
        description:
          - Specifies the DNS host name or address for connecting to the remote
            instance of NIOS WAPI over REST
          - Value can also be specified using C(INFOBLOX_HOST) environment
            variable.
        required: true
      username:
        description:
          - Configures the username to use to authenticate the connection to
            the remote instance of NIOS.
          - Value can also be specified using C(INFOBLOX_USERNAME) environment
            variable.
      password:
        description:
          - Specifies the password to use to authenticate the connection to
            the remote instance of NIOS.
          - Value can also be specified using C(INFOBLOX_PASSWORD) environment
            variable.
      ssl_verify:
        description:
          - Boolean value to enable or disable verifying SSL certificates
          - Value can also be specified using C(INFOBLOX_SSL_VERIFY) environment
            variable.
        type: bool
        default: 'no'
      http_request_timeout:
        description:
          - The amount of time before to wait before receiving a response
          - Value can also be specified using C(INFOBLOX_HTTP_REQUEST_TIMEOUT) environment
            variable.
        default: 10
      max_retries:
        description:
          - Configures the number of attempted retries before the connection
            is declared usable
          - Value can also be specified using C(INFOBLOX_MAX_RETRIES) environment
            variable.
        default: 3
      wapi_version:
        description:
          - Specifies the version of WAPI to use
          - Value can also be specified using C(INFOBLOX_WAP_VERSION) environment
            variable.
        default: 1.4
      max_results:
        description:
          - Specifies the maximum number of objects to be returned,
            if set to a negative number the appliance will return an error when the
            number of returned objects would exceed the setting.
          - Value can also be specified using C(INFOBLOX_MAX_RESULTS) environment
            variable.
        default: 1000
notes:
  - "This module must be run locally, which can be achieved by specifying C(connection: local)."
"""
