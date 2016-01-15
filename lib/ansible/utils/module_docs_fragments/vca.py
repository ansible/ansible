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
        - The vca username or email address, if not set the environment variable VCA_USER is checked for the username.
      required: false
      default: None
      aliases: ['user']
    password:
      description:
        - The vca password, if not set the environment variable VCA_PASS is checked for the password
      required: false
      default: None
      aliases: ['pass', 'pwd']
    org:
      description:
        - The org to login to for creating vapp, mostly set when the service_type is vdc.
      required: false
      default: None
    instance_id:
      description:
        - The instance id in a vchs environment to be used for creating the vapp
      required: false
      default: None
    host:
      description:
        - The authentication host to be used when service type  is vcd.
      required: false
      default: None
    api_version:
      description:
        - The api version to be used with the vca
      required: false
      default: "5.7"
    service_type:
      description:
        - The type of service we are authenticating against
      required: false
      default: vca
      choices: [ "vca", "vchs", "vcd" ]
    state:
      description:
        - if the object should be added or removed
      required: false
      default: present
      choices: [ "present", "absent" ]
    verify_certs:
      description:
        - If the certificates of the authentication is to be verified
      required: false
      default: True
    vdc_name:
      description:
        - The name of the vdc where the gateway is located.
      required: false
      default: None
    gateway_name:
      description:
        - The name of the gateway of the vdc where the rule should be added
      required: false
      default: gateway
"""

