#
# (c) 2016, John Barker <jobarker@redhat.com>
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
notes:
    - "Requires A10 Networks aXAPI 2.1"
options:
  host:
    description:
      - Hostname or IP of the A10 Networks device.
    required: true
  username:
    description:
      - An account with administrator privileges.
    required: true
    aliases: ['user', 'admin']
  password:
    description:
      - Password for the C(username) account.
    required: true
    aliases: ['pass', 'pwd']
  write_config:
    description:
      - If C(yes), any changes will cause a write of the running configuration
        to non-volatile memory. This will save I(all) configuration changes,
        including those that may have been made manually or through other modules,
        so care should be taken when specifying C(yes).
    version_added: 2.2
    type: bool
    default: 'no'
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used
        on personally controlled devices using self-signed certificates.
    version_added: 2.2
    type: bool
    default: 'yes'
"""
