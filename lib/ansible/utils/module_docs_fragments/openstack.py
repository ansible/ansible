# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
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

    # Standard openstack documentation fragment
    DOCUMENTATION = '''
options:
  cloud:
    description:
      - Named cloud to operate against. Provides default values for I(auth) and I(auth_plugin)
     required: false
  auth:
    description:
      - Dictionary containing auth information as needed by the cloud's auth
        plugin strategy. For the default I{password) plugin, this would contain
        I(auth_url), I(username), I(password), I(project_name) and any
        information about domains if the cloud supports them. For other plugins,
        this param will need to contain whatever parameters that auth plugin
        requires. This parameter is not needed if a named cloud is provided or
        OpenStack OS_* environment variables are present.
    required: false
  auth_plugin:
    description:
      - Name of the auth plugin to use. If the cloud uses something other than
        password authentication, the name of the plugin should be indicated here
        and the contents of the I(auth) parameter should be updated accordingly.
    required: false
    default: password
  auth_token:
    description:
      - An auth token obtained previously. If I(auth_token) is given,
        I(auth) and I(auth_plugin) are not needed.
  region_name:
    description:
      - Name of the region.
    required: false
  availability_zone:
    description:
      - Name of the availability zone.
    required: false
  state:
    description:
      - Should the resource be present or absent.
    choices: [present, absent]
    default: present
  wait:
    description:
      - Should ansible wait until the requested resource is complete.
    required: false
    default: "yes"
    choices: ["yes", "no"]
  timeout:
    description:
      - How long should ansible wait for the requested resource.
    required: false
    default: 180
  endpoint_type:
    description:
      - Endpoint URL type to fetch from the service catalog.
    choices: [publicURL, internalURL]
    required: false
    default: publicURL
requirements:
  - shade
notes:
  - The standard OpenStack environment variables, such as C(OS_USERNAME)
    may be user instead of providing explicit values.
  - Auth information is driven by os-client-config, which means that values
    can come from a yaml config file in /etc/ansible/openstack.yaml,
    /etc/openstack/clouds.yaml or ~/.config/openstack/clouds.yaml, then from
    standard environment variables, then finally by explicit parameters in
    plays. More information can be found at
    U(http://docs.openstack.org/developer/os-client-config)
'''
