#
# Created on December 12, 2016
# @author: Gaurav Rastogi (grastogi@avinetworks.com)
# module_check: not supported
# Avi Version: 16.3.2
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
    username:
        description:
            - Username used for accessing Avi controller. The default value is the environment variable C(AVI_USERNAME).
    password:
        description:
            - Password of Avi user in Avi controller. The default value is the environment variable C(AVI_PASSWORD).
    tenant:
        description:
            - Tenant for the operations
        default: admin
    tenant_uuid:
        description:
            - Tenant uuid for the operations
        default: ''
"""
