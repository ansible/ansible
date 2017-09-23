#
# (c) 2017, Will Wagner <willwagner602@gmail.com> and Eugene Opredelennov <eoprede@gmail.com>
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
#


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = """
notes:
  - Due to the volume of available options, it is unreasonable to list all the possible configuration options for each module.
    Instead, run the module with "print_current_config = true" to get full list of possible options output as a json file at
    the path where the playbook is executed. Additionally, default objects and argument specifications (including options,
    suboptions, and expected values) are saved locally wherever the playbook is executed.
  - Module is written to take input of a desired end config of the device. As such, if an object in the configuration
    is missing from that file, it will be DELETED from the device. It is recommended to use print_current_config = true
    for onboarding devices with existing configuration.
  - The module determines whether an existing configuration matches the proposed configuration by checking each key - value
    pair in the proposal against the existing configuration. Any keys not found in the proposed configuration are assumed
    to be in their desired state, because the list of keys is exhaustive and the API always returns all keys.
options:
  conn_params:
    description:
      - Dictionary with all the connection parameters.
    required: true
    type: dict
    suboptions:
      fortigate_username:
        description:
          - Specifies username for Fortigate connection.
        required: true
        type: str
      fortigate_password:
        description:
          - Specifies password for Fortigate connection.
        required: true
        type: str
      fortigate_ip:
        description:
          - IP or FQDN of the firewall.
        required: true
        type: str
      port:
        description:
          - Specifies port for firewall connection.
        required: false
        type: int
        default: 80 or 443
      verify:
        description:
          - Verify SSL certificate, must be located in conn_params dict.
        required: false
        type: boolean
        default: true
      secure:
        description:
          - Use secure (HTTPS) communication, must be located in conn_params dict.
        required: false
        type: boolean
        default: true
      proxies:
        description:
          - Proxies to use in requests format.
        required: false
        type: dict
        default: none
  print_current_config:
    description:
      - Runs playbook in check mode and generates JSON file with the current configuration,
        named as api-path-CurrentConfig.json in the folder playbook was run from.
    required: false
    type: boolean
    default: false
  vdom:
    default: root
    type: str
    description: Vdom to which configuration is applied to.
  permanent_objects:
    type: list
    required: false
    description:
      - A list of identifiers for objects at the endpoint that cannot be deleted.
        These objects will be reset to their default values unless they are referenced in the config.
  ignore_objects:
    type: list
    required: false
    description:
      - A list of identifiers for objects at the endpoint that cannot be deleted.
        These objects will not be deleted or updated and can not be changed.
  default_ignore_params:
    type: list
    description: A list of parameters to ignore when updating permanent objects with the default
                 object from the endpoint.
  match_ignore_params:
    type: list
    description: A list of parameters to ignore when checking whether two objects match or generating a difference.
"""
