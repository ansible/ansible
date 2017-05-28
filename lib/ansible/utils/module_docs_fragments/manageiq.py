#
# (c) 2017, Daniel Korn <korndaniel1@gmail.com>
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

    # Standard ManageIQ documentation fragment
    DOCUMENTATION = """
options:
  miq_url:
    description:
      - The ManageIQ environment url
    default: MIQ_URL env var if set. otherwise, it is required to pass it
  miq_username:
    description:
      - ManageIQ username
    default: MIQ_USERNAME env var if set. otherwise, it is required to pass it
  miq_password:
    description:
      - ManageIQ password
    default: MIQ_PASSWORD env var if set. otherwise, it is required to pass it
  validate_certs:
    required: False
    description:
      - Whether SSL certificates should be verified for HTTPS requests
    default: True
    choices: ['True', 'False']
  ca_bundle_path:
    required: False
    description:
      - The path to a CA_BUNDLE file or directory with certificates
    default: null

requirements:
  - 'manageiq-client (source: https://github.com/ManageIQ/manageiq-api-client-python/)'
"""
