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
  api_url:
    description:
      - The resolvable endpoint for the API
  api_username:
    description:
      - The username to use for authentication against the API
  api_password:
    description:
      - The password to use for authentication against the API
  validate_certs:
    description:
      - Whether or not to validate SSL certs when supplying a https endpoint.
    type: bool
    default: 'yes'
"""
