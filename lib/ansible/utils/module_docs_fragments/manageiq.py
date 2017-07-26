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
  miq:
    required: true
    description:
      - url            ManageIQ environment url. C(MIQ_URL) env var if set. otherwise, it is required to pass it.
      - username       ManageIQ username. C(MIQ_USERNAME) env var if set. otherwise, it is required to pass it.
      - password       ManageIQ password. C(MIQ_PASSWORD) env var if set. otherwise, it is required to pass it.
      - verify_ssl     Whether SSL certificates should be verified for HTTPS requests. defaults to True.
      - ca_bundle_path The path to a CA bundle file or directory with certificates. defaults to None.

requirements:
  - 'manageiq-client U(https://github.com/ManageIQ/manageiq-api-client-python/)'
"""
