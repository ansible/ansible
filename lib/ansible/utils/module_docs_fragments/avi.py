#
# Created on December 12, 2016
# @author: Gaurav Rastogi (grastogi@avinetworks.com)
# Avi Version: 16.3.4
#
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
    # Avi common documentation fragment
    DOCUMENTATION = """
options:
    controller:
        description:
            - IP address or hostname of the controller. The default value is the environment variable C(AVI_CONTROLLER).
        default: ''
    username:
        description:
            - Username used for accessing Avi controller. The default value is the environment variable C(AVI_USERNAME).
        default: ''
    password:
        description:
            - Password of Avi user in Avi controller. The default value is the environment variable C(AVI_PASSWORD).
        default: ''
    tenant:
        description:
            - Name of tenant used for all Avi API calls and context of object.
        default: admin
    tenant_uuid:
        description:
            - UUID of tenant used for all Avi API calls and context of object.
        default: ''
    api_version:
        description:
            - Avi API version of to use for Avi API and objects.
        default: "16.4.4"
    avi_credentials:
        description:
            - Avi Credentials dictionary which can be used in lieu of enumerating Avi Controller login details.
        version_added: "2.5"
    api_context:
        description:
            - Avi API context that includes current session ID and CSRF Token.
            - This allows user to perform single login and re-use the session.
        version_added: "2.5"
notes:
  - For more information on using Ansible to manage Avi Network devices see U(https://www.ansible.com/ansible-avi-networks).
"""
