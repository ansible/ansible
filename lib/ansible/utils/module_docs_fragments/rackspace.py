# (c) 2014, Matt Martz <matt@sivel.net>
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

    # Standard Rackspace only documentation fragment
    DOCUMENTATION = """
options:
  api_key:
    description:
      - Rackspace API key, overrides I(credentials).
    aliases:
      - password
  credentials:
    description:
      - File to find the Rackspace credentials in. Ignored if I(api_key) and
        I(username) are provided.
    aliases:
      - creds_file
  env:
    description:
      - Environment as configured in I(~/.pyrax.cfg),
        see U(https://github.com/rackspace/pyrax/blob/master/docs/getting_started.md#pyrax-configuration).
    version_added: 1.5
  region:
    description:
      - Region to create an instance in.
    default: DFW
  username:
    description:
      - Rackspace username, overrides I(credentials).
  verify_ssl:
    description:
      - Whether or not to require SSL validation of API endpoints.
    version_added: 1.5
requirements:
  - "python >= 2.6"
  - pyrax
notes:
  - The following environment variables can be used, C(RAX_USERNAME),
    C(RAX_API_KEY), C(RAX_CREDS_FILE), C(RAX_CREDENTIALS), C(RAX_REGION).
  - C(RAX_CREDENTIALS) and C(RAX_CREDS_FILE) points to a credentials file
    appropriate for pyrax. See U(https://github.com/rackspace/pyrax/blob/master/docs/getting_started.md#authenticating)
  - C(RAX_USERNAME) and C(RAX_API_KEY) obviate the use of a credentials file
  - C(RAX_REGION) defines a Rackspace Public Cloud region (DFW, ORD, LON, ...)
"""

    # Documentation fragment including attributes to enable communication
    # of other OpenStack clouds. Not all rax modules support this.
    OPENSTACK = """
options:
  api_key:
    description:
      - Rackspace API key, overrides I(credentials).
    aliases:
      - password
  auth_endpoint:
    description:
      - The URI of the authentication service.
    default: https://identity.api.rackspacecloud.com/v2.0/
    version_added: 1.5
  credentials:
    description:
      - File to find the Rackspace credentials in. Ignored if I(api_key) and
        I(username) are provided.
    aliases:
      - creds_file
  env:
    description:
      - Environment as configured in I(~/.pyrax.cfg),
        see U(https://github.com/rackspace/pyrax/blob/master/docs/getting_started.md#pyrax-configuration).
    version_added: 1.5
  identity_type:
    description:
      - Authentication mechanism to use, such as rackspace or keystone.
    default: rackspace
    version_added: 1.5
  region:
    description:
      - Region to create an instance in.
    default: DFW
  tenant_id:
    description:
      - The tenant ID used for authentication.
    version_added: 1.5
  tenant_name:
    description:
      - The tenant name used for authentication.
    version_added: 1.5
  username:
    description:
      - Rackspace username, overrides I(credentials).
  verify_ssl:
    description:
      - Whether or not to require SSL validation of API endpoints.
    version_added: 1.5
requirements:
  - "python >= 2.6"
  - pyrax
notes:
  - The following environment variables can be used, C(RAX_USERNAME),
    C(RAX_API_KEY), C(RAX_CREDS_FILE), C(RAX_CREDENTIALS), C(RAX_REGION).
  - C(RAX_CREDENTIALS) and C(RAX_CREDS_FILE) points to a credentials file
    appropriate for pyrax. See U(https://github.com/rackspace/pyrax/blob/master/docs/getting_started.md#authenticating)
  - C(RAX_USERNAME) and C(RAX_API_KEY) obviate the use of a credentials file
  - C(RAX_REGION) defines a Rackspace Public Cloud region (DFW, ORD, LON, ...)
"""
