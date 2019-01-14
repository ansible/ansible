#
# (c) 2019, Ricardo Carrillo Cruz <ricarril@redhat.com>
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
  auto_publish_session:
    description:
      - Publish the current session if changes have been performed
        after task completes.
    type: bool
    default: 'yes'
  auto_install_policy:
    description:
      - Install the package policy if changes have been performed
        after the task completes.
    type: bool
    default: 'yes'
  package_policy:
    description:
      - Package policy name to be installed.
    type: bool
    default: 'standard'
  targets:
    description:
      - Targets to install the package policy on.
    type: str
    default: None
"""
