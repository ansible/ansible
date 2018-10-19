# (c) 2016, Charles Paul <cpaul@ansible.com>
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
    # Parameters for VCA modules
    DOCUMENTATION = """
options:
    username:
      description:
        - The vca username or email address, if not set the environment variable C(VCA_USER) is checked for the username.
      aliases: ['user']
    password:
      description:
        - The vca password, if not set the environment variable C(VCA_PASS) is checked for the password.
      aliases: ['pass', 'passwd']
    org:
      description:
        - The org to login to for creating vapp. This option is required when the C(service_type) is I(vdc).
    instance_id:
      description:
        - The instance id in a vchs environment to be used for creating the vapp.
    host:
      description:
        - The authentication host to be used when service type is vcd.
    api_version:
      description:
        - The api version to be used with the vca.
      default: "5.7"
    service_type:
      description:
        - The type of service we are authenticating against.
      default: vca
      choices: [ "vca", "vchs", "vcd" ]
    state:
      description:
        - If the object should be added or removed.
      default: present
      choices: [ "present", "absent" ]
    verify_certs:
      description:
        - If the certificates of the authentication is to be verified.
      type: bool
      default: 'yes'
    vdc_name:
      description:
        - The name of the vdc where the gateway is located.
    gateway_name:
      description:
        - The name of the gateway of the vdc where the rule should be added.
      default: gateway
"""
