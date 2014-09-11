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
  login_username:
   description:
      - login username to authenticate to keystone
   required: true
   default: admin
  login_password:
   description:
      - Password of login user
   required: true
   default: 'yes'
  login_tenant_name:
   description:
      - The tenant name of the login user
   required: true
   default: 'yes'
  auth_url:
   description:
      - The keystone url for authentication
   required: false
   default: 'http://127.0.0.1:35357/v2.0/'
  region_name:
   description:
      - Name of the region
   required: false
   default: None
  availability_zone:
   description:
      - Name of the availability zone
   required: false
   default: None
   version_added: "1.8"
  endpoint_type:
   description:
      - endpoint URL type
   choices: [publicURL, internalURL]
   required: false
   default: publicURL
'''
